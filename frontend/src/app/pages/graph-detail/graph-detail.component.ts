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
import { Core } from 'cytoscape';

import { ApiService } from '../../services/api.service';
import {
  GraphDetail,
  GraphEdge,
  GraphNode,
  NPC,
  RELATION_POLARITIES,
  RelationPolarity,
  RelationType,
} from '../../models/domain.models';
import { createGraphCytoscape } from './graph-cytoscape';
import {
  EndpointOption,
  GRAPH_STYLESHEET,
  availableNpcs,
  buildCyElements,
  endpointKey,
  hasPartyNode,
  mapEndpointOptions,
  parseCyNodeId,
} from './graph-model';

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
    return endpointKey(nodeId);
  }

  endpointOptions(): EndpointOption[] {
    if (!this.graph) {
      return [];
    }
    return mapEndpointOptions(this.graph.nodes);
  }

  hasPartyNode(): boolean {
    return hasPartyNode(this.graph?.nodes ?? []);
  }

  availableNpcs(): NPC[] {
    if (!this.graph) {
      return this.campaignNpcs;
    }
    return availableNpcs(this.campaignNpcs, this.graph.nodes);
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
      animate: false,
      padding: 48,
      randomize: true,
      componentSpacing: 80,
    });
    layout.one('layoutstop', () => {
      this.cy?.nodes().forEach((node) => {
        const nodeId = parseCyNodeId(node.id());
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
    const elements = buildCyElements(this.graph);
    this.destroyCy();

    this.zone.runOutsideAngular(() => {
      this.cy = createGraphCytoscape(container, elements, GRAPH_STYLESHEET, {
        onNodeTap: (nodeId) => {
          this.zone.run(() => {
            this.selectedEdgeId = null;
            this.selectedNodeId = nodeId;
          });
        },
        onEdgeTap: (edgeId) => {
          this.zone.run(() => {
            this.selectedNodeId = null;
            this.selectedEdgeId = edgeId;
          });
        },
        onBackgroundTap: () => {
          this.zone.run(() => {
            this.selectedNodeId = null;
            this.selectedEdgeId = null;
          });
        },
        onNodeDragFree: (nodeId, position) => {
          this.persistNodePosition(nodeId, position);
        },
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
