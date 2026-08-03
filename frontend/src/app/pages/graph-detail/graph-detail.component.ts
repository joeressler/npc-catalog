import {
  AfterViewInit,
  ChangeDetectorRef,
  Component,
  ElementRef,
  NgZone,
  OnDestroy,
  OnInit,
  ViewChild,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import cytoscape, { Core, ElementDefinition } from 'cytoscape';

import { MarkdownViewComponent } from '../../shared/markdown-view.component';
import { ApiService } from '../../services/api.service';
import {
  GraphDetail,
  GraphEdge,
  GraphNode,
  GraphNodeKind,
  NPC,
  RELATION_POLARITIES,
  RelationPolarity,
  RelationType,
} from '../../models/domain.models';

interface EndpointOption {
  key: string;
  nodeId: number;
  kind: GraphNodeKind;
  label: string;
}

@Component({
  selector: 'app-graph-detail',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, MarkdownViewComponent],
  templateUrl: './graph-detail.component.html',
  styleUrl: './graph-detail.component.scss',
})
export class GraphDetailComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('cyContainer') cyContainer!: ElementRef<HTMLDivElement>;

  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly zone = inject(NgZone);

  graph: GraphDetail | null = null;
  relationTypes: RelationType[] = [];
  campaignNpcs: NPC[] = [];
  campaignId = 0;
  loading = true;
  error = '';
  actionError = '';
  deleting = false;

  selectedNodeId: number | null = null;
  selectedEdgeId: number | null = null;

  addNpcId: number | null = null;
  addPcName = '';
  edgeFromKey = '';
  edgeToKey = '';
  edgeRelationTypeId: number | null = null;
  edgeNotes = '';
  edgeBidirectional = true;
  newRelationName = '';
  newRelationPolarity: RelationPolarity = 'complex';

  readonly polarities = RELATION_POLARITIES;

  private cy: Core | null = null;
  private graphId = 0;
  private positionTimers = new Map<number, ReturnType<typeof setTimeout>>();
  private pendingPositions = new Map<number, { x: number; y: number }>();
  private renderRetryHandle: ReturnType<typeof setTimeout> | null = null;
  private resizeHandles: Array<ReturnType<typeof setTimeout>> = [];
  private viewReady = false;

  ngOnInit(): void {
    this.graphId = Number(this.route.snapshot.paramMap.get('graphId'));
    this.campaignId = Number(this.route.snapshot.paramMap.get('campaignId'));
    this.loadGraph();
  }

  ngAfterViewInit(): void {
    this.viewReady = true;
    this.scheduleRender();
  }

  ngOnDestroy(): void {
    if (this.renderRetryHandle !== null) {
      clearTimeout(this.renderRetryHandle);
    }
    this.resizeHandles.forEach((handle) => clearTimeout(handle));
    this.flushPendingPositions();
    this.destroyCy();
  }

  loadGraph(silent = false): void {
    if (!silent) {
      this.loading = true;
      this.error = '';
    }

    this.api.getGraph(this.graphId).subscribe({
      next: (graph) => {
        this.zone.run(() => {
          this.graph = graph;
          this.campaignId = graph.campaign;
          this.loading = false;
          this.cdr.detectChanges();
          this.scheduleRender();
        });
      },
      error: () => {
        this.zone.run(() => {
          this.error = 'Relationship web not found.';
          this.loading = false;
        });
      },
    });

    this.api.getCampaignRelationTypes(this.campaignId).subscribe({
      next: (response) => {
        this.zone.run(() => {
          this.relationTypes = response.results;
        });
      },
    });

    this.api.getCampaignNpcs(this.campaignId).subscribe({
      next: (response) => {
        this.zone.run(() => {
          this.campaignNpcs = response.results;
        });
      },
    });
  }

  endpointKey(nodeId: number): string {
    return `node:${nodeId}`;
  }

  endpointOptions(): EndpointOption[] {
    if (!this.graph) {
      return [];
    }
    return this.graph.nodes.map((node) => ({
      key: this.endpointKey(node.id),
      nodeId: node.id,
      kind: node.kind,
      label: node.kind === 'pc' ? `${node.label} (PC)` : node.label,
    }));
  }

  hasPartyNode(): boolean {
    return this.graph?.nodes.some((node) => node.kind === 'party') ?? false;
  }

  availableNpcs(): NPC[] {
    if (!this.graph) {
      return this.campaignNpcs;
    }
    const onGraph = new Set(
      this.graph.nodes.filter((node) => node.kind === 'npc').map((node) => node.npc_id),
    );
    return this.campaignNpcs.filter((npc) => !onGraph.has(npc.id));
  }

  addPartyNode(): void {
    this.actionError = '';
    this.api.addGraphNode(this.graphId, { kind: 'party' }).subscribe({
      next: () => this.loadGraph(true),
      error: (err) => {
        this.actionError = err.error?.detail ?? 'Could not add Party node.';
      },
    });
  }

  addNpcNode(): void {
    if (this.addNpcId === null) {
      return;
    }
    this.actionError = '';
    this.api.addGraphNode(this.graphId, { kind: 'npc', npc_id: this.addNpcId }).subscribe({
      next: () => {
        this.addNpcId = null;
        this.loadGraph(true);
      },
      error: (err) => {
        this.actionError = err.error?.detail ?? 'Could not add NPC.';
      },
    });
  }

  addPcNode(): void {
    const name = this.addPcName.trim();
    if (!name) {
      this.actionError = 'Enter a player character name.';
      return;
    }
    if (!this.hasPartyNode()) {
      this.actionError = 'Add the Party node before adding player characters.';
      return;
    }
    this.actionError = '';
    this.api.addGraphNode(this.graphId, { kind: 'pc', label: name }).subscribe({
      next: () => {
        this.addPcName = '';
        this.loadGraph(true);
      },
      error: (err) => {
        const detail = err.error?.detail;
        this.actionError =
          typeof detail === 'string' ? detail : 'Could not add player character.';
      },
    });
  }

  addEdge(): void {
    if (!this.edgeFromKey || !this.edgeToKey || this.edgeRelationTypeId === null) {
      this.actionError = 'Choose from, to, and relation type.';
      return;
    }

    const from = this.endpointOptions().find((option) => option.key === this.edgeFromKey);
    const to = this.endpointOptions().find((option) => option.key === this.edgeToKey);
    if (!from || !to) {
      return;
    }

    this.actionError = '';
    this.api
      .addGraphEdge(this.graphId, {
        relation_type_id: this.edgeRelationTypeId,
        from_node_id: from.nodeId,
        to_node_id: to.nodeId,
        notes: this.edgeNotes.trim(),
        bidirectional: this.edgeBidirectional,
      })
      .subscribe({
        next: () => {
          this.edgeNotes = '';
          this.loadGraph(true);
        },
        error: (err) => {
          this.actionError = err.error?.detail ?? 'Could not add relation.';
        },
      });
  }

  addRelationType(): void {
    const name = this.newRelationName.trim();
    if (!name) {
      return;
    }
    this.actionError = '';
    this.api
      .createRelationType(this.campaignId, {
        name,
        polarity: this.newRelationPolarity,
      })
      .subscribe({
        next: (relationType) => {
          this.relationTypes = [...this.relationTypes, relationType].sort((a, b) =>
            a.name.localeCompare(b.name),
          );
          this.newRelationName = '';
        },
        error: (err) => {
          this.actionError = err.error?.detail ?? 'Could not add relation type.';
        },
      });
  }

  deleteSelectedNode(): void {
    if (this.selectedNodeId === null) {
      return;
    }
    const node = this.selectedNode();
    const message =
      node?.kind === 'party'
        ? 'Remove the Party node and all player characters under it? Connected relations will also be removed.'
        : 'Remove this character from the web? Connected relations will also be removed.';
    if (!confirm(message)) {
      return;
    }
    this.api.deleteGraphNode(this.selectedNodeId).subscribe({
      next: () => {
        this.selectedNodeId = null;
        this.loadGraph(true);
      },
      error: (err) => {
        this.actionError = err.error?.detail ?? 'Could not remove node.';
      },
    });
  }

  deleteSelectedEdge(): void {
    if (this.selectedEdgeId === null) {
      return;
    }
    if (!confirm('Remove this relation?')) {
      return;
    }
    this.api.deleteGraphEdge(this.selectedEdgeId).subscribe({
      next: () => {
        this.selectedEdgeId = null;
        this.loadGraph(true);
      },
      error: (err) => {
        this.actionError = err.error?.detail ?? 'Could not remove relation.';
      },
    });
  }

  deleteGraph(): void {
    if (!this.graph || !confirm(`Delete "${this.graph.name}"? This cannot be undone.`)) {
      return;
    }
    this.deleting = true;
    this.api.deleteGraph(this.graph.id).subscribe({
      next: () => {
        this.router.navigate(['/campaigns', this.campaignId, 'graphs']);
      },
      error: () => {
        this.actionError = 'Could not delete relationship web.';
        this.deleting = false;
      },
    });
  }

  fitView(): void {
    this.cy?.resize();
    this.cy?.fit(undefined, 48);
  }

  runLayout(): void {
    if (!this.cy || this.cy.nodes().length === 0) {
      return;
    }
    const layout = this.cy.layout({
      name: 'cose',
      animate: true,
      animationDuration: 500,
      animationEasing: 'ease-out',
      padding: 48,
      randomize: true,
      componentSpacing: 80,
    });
    layout.one('layoutstop', () => {
      this.cy?.nodes().forEach((node) => {
        const nodeId = Number(node.id().replace('node-', ''));
        if (!Number.isNaN(nodeId)) {
          this.persistNodePosition(nodeId, node.position());
        }
      });
      this.fitView();
    });
    layout.run();
  }

  selectedNode(): GraphNode | null {
    if (!this.graph || this.selectedNodeId === null) {
      return null;
    }
    return this.graph.nodes.find((node) => node.id === this.selectedNodeId) ?? null;
  }

  selectedEdge(): GraphEdge | null {
    if (!this.graph || this.selectedEdgeId === null) {
      return null;
    }
    return this.graph.edges.find((edge) => edge.id === this.selectedEdgeId) ?? null;
  }

  openNpc(node: GraphNode): void {
    if (node.kind === 'npc' && node.npc_id !== null) {
      this.router.navigate(['/npcs', node.npc_id]);
    }
  }

  private destroyCy(): void {
    if (this.cy) {
      this.cy.destroy();
      this.cy = null;
    }
  }

  private scheduleRender(): void {
    if (!this.viewReady) {
      return;
    }
    if (this.renderRetryHandle !== null) {
      clearTimeout(this.renderRetryHandle);
    }

    let attempts = 0;
    const attempt = () => {
      this.renderRetryHandle = null;
      if (!this.graph || this.loading) {
        return;
      }
      const el = this.cyContainer?.nativeElement;
      if (!el || el.clientWidth < 8 || el.clientHeight < 8) {
        attempts += 1;
        if (attempts < 40) {
          this.renderRetryHandle = setTimeout(attempt, 50);
        }
        return;
      }
      this.renderGraph();
    };
    this.renderRetryHandle = setTimeout(attempt, 0);
  }

  private renderGraph(): void {
    if (!this.graph || !this.cyContainer?.nativeElement) {
      return;
    }

    const container = this.cyContainer.nativeElement;
    const elements = this.buildElements(this.graph);
    this.destroyCy();

    this.zone.runOutsideAngular(() => {
      this.cy = cytoscape({
        container,
        elements,
        minZoom: 0.2,
        maxZoom: 2.5,
        wheelSensitivity: 0.25,
        style: [
          {
            selector: 'node',
            style: {
              label: 'data(label)',
              'text-valign': 'center',
              'text-halign': 'center',
              'background-color': '#ffffff',
              'border-color': '#7b5cff',
              'border-width': 2,
              color: '#2a1f4a',
              'font-family': 'Figtree, sans-serif',
              'font-size': 12,
              width: 72,
              height: 72,
              'text-wrap': 'wrap',
              'text-max-width': '64px',
              'overlay-padding': 6,
            },
          },
          {
            selector: 'node[kind = "party"]',
            style: {
              shape: 'round-rectangle',
              'background-color': '#e8dcff',
              'background-opacity': 0.45,
              'border-color': '#4a2d7a',
              'border-width': 3,
              'font-size': 13,
              'font-weight': 700,
              'text-valign': 'top',
              'text-halign': 'center',
              'text-margin-y': 10,
              padding: '36px',
            },
          },
          {
            selector: 'node[kind = "party"]:selected',
            style: {
              'border-width': 5,
              'border-color': '#9b7dff',
              'background-opacity': 0.65,
              'overlay-color': '#c4b0ff',
              'overlay-opacity': 0.18,
              'overlay-padding': 10,
            },
          },
          {
            selector: 'node[kind = "pc"]',
            style: {
              shape: 'ellipse',
              width: 64,
              height: 64,
              'background-color': '#d8e8ff',
              'border-color': '#4a2d7a',
              'border-width': 2,
              'font-size': 11,
            },
          },
          {
            selector: 'node:selected',
            style: {
              'border-width': 4,
              'border-color': '#9b7dff',
              'overlay-color': '#c4b0ff',
              'overlay-opacity': 0.15,
              'overlay-padding': 8,
            },
          },
          {
            selector: 'edge',
            style: {
              label: 'data(label)',
              'curve-style': 'bezier',
              'target-arrow-shape': 'triangle',
              width: 2,
              'line-color': 'data(color)',
              'target-arrow-color': 'data(color)',
              color: '#2a1f4a',
              'font-size': 10,
              'text-background-color': 'rgba(255,255,255,0.75)',
              'text-background-opacity': 1,
              'text-background-padding': '2px',
              'text-rotation': 'autorotate',
            },
          },
          {
            selector: 'edge:selected',
            style: {
              width: 3,
            },
          },
        ],
        layout: { name: 'preset' },
      });

      this.cy.on('tap', 'node', (event) => {
        this.zone.run(() => {
          this.selectedEdgeId = null;
          this.selectedNodeId = Number(event.target.id().replace('node-', ''));
        });
      });

      this.cy.on('tap', 'edge', (event) => {
        this.zone.run(() => {
          this.selectedNodeId = null;
          this.selectedEdgeId = Number(event.target.id().replace('edge-', ''));
        });
      });

      this.cy.on('tap', (event) => {
        if (event.target === this.cy) {
          this.zone.run(() => {
            this.selectedNodeId = null;
            this.selectedEdgeId = null;
          });
        }
      });

      this.cy.on('dragfree', 'node', (event) => {
        const nodeId = Number(event.target.id().replace('node-', ''));
        if (Number.isNaN(nodeId)) {
          return;
        }
        this.persistNodePosition(nodeId, event.target.position());
      });
    });

    const missingPositions =
      this.graph.nodes.length > 0 &&
      this.graph.nodes.every((node) => node.pos_x === null || node.pos_y === null);

    if (missingPositions) {
      this.runLayout();
    } else {
      this.queueResizeAndFit();
    }
  }

  private queueResizeAndFit(): void {
    this.resizeHandles.forEach((handle) => clearTimeout(handle));
    this.resizeHandles = [0, 100, 350, 700].map((delay) =>
      setTimeout(() => {
        if (!this.cy) {
          return;
        }
        this.cy.resize();
        this.cy.fit(undefined, 48);
      }, delay),
    );
  }

  private buildElements(graph: GraphDetail): ElementDefinition[] {
    const kindOrder: Record<string, number> = { party: 0, pc: 1, npc: 2 };
    const sortedNodes = [...graph.nodes].sort(
      (a, b) => (kindOrder[a.kind] ?? 9) - (kindOrder[b.kind] ?? 9) || a.id - b.id,
    );
    const party = sortedNodes.find((node) => node.kind === 'party');

    const nodes: ElementDefinition[] = sortedNodes.map((node, index) => {
      const data: Record<string, string | number | null> = {
        id: `node-${node.id}`,
        label: node.label,
        kind: node.kind,
        npcId: node.npc_id,
      };
      // Nest PCs under Party for the "sub-node" UX. Party must be first in elements
      // (ensured by sort) so the parent exists before children are added.
      if (node.kind === 'pc' && party) {
        data['parent'] = `node-${party.id}`;
      }

      let position: { x: number; y: number };
      if (node.pos_x !== null && node.pos_y !== null) {
        position = { x: node.pos_x, y: node.pos_y };
      } else if (node.kind === 'pc' && party?.pos_x != null && party?.pos_y != null) {
        position = { x: 70, y: 40 + index * 30 };
      } else {
        position = {
          x: 140 + (index % 5) * 150,
          y: 140 + Math.floor(index / 5) * 130,
        };
      }

      return { data, position };
    });

    const nodeIds = new Set(sortedNodes.map((node) => `node-${node.id}`));
    const edges: ElementDefinition[] = graph.edges
      .filter(
        (edge) =>
          nodeIds.has(`node-${edge.from_endpoint.node_id}`) &&
          nodeIds.has(`node-${edge.to_endpoint.node_id}`),
      )
      .map((edge) => ({
        data: {
          id: `edge-${edge.id}`,
          source: `node-${edge.from_endpoint.node_id}`,
          target: `node-${edge.to_endpoint.node_id}`,
          label: edge.relation_type.name,
          color: this.polarityColor(edge.relation_type.polarity),
        },
      }));

    return [...nodes, ...edges];
  }

  private polarityColor(polarity: RelationPolarity): string {
    switch (polarity) {
      case 'positive':
        return '#2d8a6e';
      case 'negative':
        return '#c0396b';
      case 'complex':
        return '#7b5cff';
      default:
        return '#6b628a';
    }
  }

  private persistNodePosition(nodeId: number, position: { x: number; y: number }): void {
    this.pendingPositions.set(nodeId, position);
    const existing = this.positionTimers.get(nodeId);
    if (existing) {
      clearTimeout(existing);
    }
    const timer = setTimeout(() => {
      this.positionTimers.delete(nodeId);
      const pending = this.pendingPositions.get(nodeId);
      if (!pending) {
        return;
      }
      this.pendingPositions.delete(nodeId);
      this.api.updateGraphNodePosition(nodeId, { pos_x: pending.x, pos_y: pending.y }).subscribe();
    }, 400);
    this.positionTimers.set(nodeId, timer);
  }

  private flushPendingPositions(): void {
    this.positionTimers.forEach((timer) => clearTimeout(timer));
    this.positionTimers.clear();
    this.pendingPositions.forEach((position, nodeId) => {
      this.api.updateGraphNodePosition(nodeId, { pos_x: position.x, pos_y: position.y }).subscribe();
    });
    this.pendingPositions.clear();
  }
}
