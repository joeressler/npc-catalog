import {
  AfterViewInit,
  Component,
  ElementRef,
  OnDestroy,
  OnInit,
  ViewChild,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import cytoscape, { Core, ElementDefinition } from 'cytoscape';

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
} from '../../models/npc.models';

interface EndpointOption {
  key: string;
  nodeId: number;
  kind: GraphNodeKind;
  label: string;
}

@Component({
  selector: 'app-graph-detail',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './graph-detail.component.html',
  styleUrl: './graph-detail.component.scss',
})
export class GraphDetailComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('cyContainer') cyContainer!: ElementRef<HTMLDivElement>;

  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

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
  private viewReady = false;
  private positionTimers = new Map<number, ReturnType<typeof setTimeout>>();

  ngOnInit(): void {
    this.graphId = Number(this.route.snapshot.paramMap.get('graphId'));
    this.campaignId = Number(this.route.snapshot.paramMap.get('campaignId'));
    this.loadGraph();
  }

  ngAfterViewInit(): void {
    this.viewReady = true;
    if (this.graph) {
      this.renderGraph();
    }
  }

  ngOnDestroy(): void {
    this.positionTimers.forEach((timer) => clearTimeout(timer));
    this.cy?.destroy();
  }

  loadGraph(silent = false): void {
    if (!silent) {
      this.loading = true;
      this.error = '';
    }

    this.api.getGraph(this.graphId).subscribe({
      next: (graph) => {
        this.graph = graph;
        this.campaignId = graph.campaign;
        this.loading = false;
        if (this.viewReady) {
          this.renderGraph();
        }
      },
      error: () => {
        this.error = 'Graph not found.';
        this.loading = false;
      },
    });

    this.api.getCampaignRelationTypes(this.campaignId).subscribe({
      next: (response) => {
        this.relationTypes = response.results;
      },
    });

    this.api.getCampaignNpcs(this.campaignId).subscribe({
      next: (response) => {
        this.campaignNpcs = response.results;
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
    this.actionError = '';
    this.api.addGraphNode(this.graphId, { kind: 'pc', label: name }).subscribe({
      next: () => {
        this.addPcName = '';
        this.loadGraph(true);
      },
      error: (err) => {
        this.actionError = err.error?.detail ?? 'Could not add player character.';
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
        this.actionError = 'Could not delete graph.';
        this.deleting = false;
      },
    });
  }

  fitView(): void {
    this.cy?.fit(undefined, 48);
  }

  runLayout(): void {
    if (!this.cy) {
      return;
    }
    const layout = this.cy.layout({
      name: 'cose',
      animate: true,
      padding: 48,
      nodeRepulsion: 8000,
      idealEdgeLength: 120,
    });
    layout.run();
    layout.one('layoutstop', () => {
      this.cy?.nodes().forEach((node) => {
        const nodeId = Number(node.id().replace('node-', ''));
        this.persistNodePosition(nodeId, node.position());
      });
    });
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

  private renderGraph(): void {
    if (!this.graph || !this.cyContainer) {
      return;
    }

    const elements = this.buildElements(this.graph);
    if (this.cy) {
      this.cy.destroy();
    }

    this.cy = cytoscape({
      container: this.cyContainer.nativeElement,
      elements,
      minZoom: 0.3,
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
            'background-opacity': 0.5,
            'border-color': '#4a2d7a',
            'border-width': 3,
            'font-size': 13,
            'font-weight': 700,
            'text-valign': 'top',
            'text-margin-y': 8,
            padding: '28px',
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
            'border-color': '#4a2d7a',
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
      this.selectedEdgeId = null;
      this.selectedNodeId = Number(event.target.id().replace('node-', ''));
    });

    this.cy.on('tap', 'edge', (event) => {
      this.selectedNodeId = null;
      this.selectedEdgeId = Number(event.target.id().replace('edge-', ''));
    });

    this.cy.on('tap', (event) => {
      if (event.target === this.cy) {
        this.selectedNodeId = null;
        this.selectedEdgeId = null;
      }
    });

    this.cy.on('dragfree', 'node', (event) => {
      const nodeId = Number(event.target.id().replace('node-', ''));
      this.persistNodePosition(nodeId, event.target.position());
    });

    if (this.graph.nodes.every((node) => node.pos_x === null || node.pos_y === null)) {
      this.runLayout();
    } else {
      this.cy.fit(undefined, 48);
    }
  }

  private buildElements(graph: GraphDetail): ElementDefinition[] {
    const party = graph.nodes.find((node) => node.kind === 'party');
    const nodes: ElementDefinition[] = graph.nodes.map((node, index) => {
      const data: Record<string, string | number | null> = {
        id: `node-${node.id}`,
        label: node.label,
        kind: node.kind,
        npcId: node.npc_id,
      };
      if (node.kind === 'pc' && party) {
        data['parent'] = `node-${party.id}`;
      }
      return {
        data,
        position:
          node.pos_x !== null && node.pos_y !== null
            ? { x: node.pos_x, y: node.pos_y }
            : { x: 120 + (index % 4) * 140, y: 120 + Math.floor(index / 4) * 120 },
      };
    });

    const edges: ElementDefinition[] = graph.edges.map((edge) => ({
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
    const existing = this.positionTimers.get(nodeId);
    if (existing) {
      clearTimeout(existing);
    }
    const timer = setTimeout(() => {
      this.api
        .updateGraphNodePosition(nodeId, { pos_x: position.x, pos_y: position.y })
        .subscribe();
      this.positionTimers.delete(nodeId);
    }, 400);
    this.positionTimers.set(nodeId, timer);
  }
}
