import type { ElementDefinition, StylesheetStyle } from 'cytoscape';

import {
  GraphDetail,
  GraphNode,
  GraphNodeKind,
  NPC,
  RelationPolarity,
} from '../../models/domain.models';

export interface EndpointOption {
  key: string;
  nodeId: number;
  kind: GraphNodeKind;
  label: string;
}

export function endpointKey(nodeId: number): string {
  return `node:${nodeId}`;
}

export function mapEndpointOptions(nodes: GraphNode[]): EndpointOption[] {
  return nodes.map((node) => ({
    key: endpointKey(node.id),
    nodeId: node.id,
    kind: node.kind,
    label: node.kind === 'pc' ? `${node.label} (PC)` : node.label,
  }));
}

export function hasPartyNode(nodes: GraphNode[]): boolean {
  return nodes.some((node) => node.kind === 'party');
}

export function availableNpcs(campaignNpcs: NPC[], graphNodes: GraphNode[]): NPC[] {
  const onGraph = new Set(
    graphNodes.filter((node) => node.kind === 'npc').map((node) => node.npc_id),
  );
  return campaignNpcs.filter((npc) => !onGraph.has(npc.id));
}

export function polarityColor(polarity: RelationPolarity): string {
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

export function parseCyNodeId(id: string): number {
  return Number(id.replace('node-', ''));
}

export function parseCyEdgeId(id: string): number {
  return Number(id.replace('edge-', ''));
}

export function buildCyElements(graph: GraphDetail): ElementDefinition[] {
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
        color: polarityColor(edge.relation_type.polarity),
      },
    }));

  return [...nodes, ...edges];
}

export const GRAPH_STYLESHEET: StylesheetStyle[] = [
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
];
