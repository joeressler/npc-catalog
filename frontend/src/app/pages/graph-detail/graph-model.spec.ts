import {
  GraphDetail,
  GraphEdge,
  GraphNode,
  GraphNodeKind,
  NPC,
  RelationPolarity,
} from '../../models/domain.models';
import {
  availableNpcs,
  buildCyElements,
  endpointKey,
  hasPartyNode,
  mapEndpointOptions,
  parseCyEdgeId,
  parseCyNodeId,
  polarityColor,
} from './graph-model';

function makeNode(overrides: Partial<GraphNode> & { id: number; kind: GraphNodeKind }): GraphNode {
  return {
    id: overrides.id,
    kind: overrides.kind,
    npc_id: overrides.npc_id ?? null,
    label: overrides.label ?? `Node ${overrides.id}`,
    pos_x: overrides.pos_x ?? null,
    pos_y: overrides.pos_y ?? null,
  };
}

function makeNpc(id: number, name = `NPC ${id}`): NPC {
  return {
    id,
    campaign: 1,
    name,
    role_occupation: 'Merchant',
    alignment: 'N',
    alignment_display: 'True Neutral',
    location: '',
    faction: '',
    attitude: '',
    party_relationship: '',
    image: null,
    aliases: [],
    tags: [],
    created_at: '',
    updated_at: '',
  };
}

function makeEdge(
  id: number,
  fromNodeId: number,
  toNodeId: number,
  polarity: RelationPolarity = 'positive',
  name = 'Allies',
): GraphEdge {
  return {
    id,
    relation_type: { id: 1, name, polarity },
    from_endpoint: { node_id: fromNodeId, kind: 'npc', npc_id: null, label: 'from' },
    to_endpoint: { node_id: toNodeId, kind: 'npc', npc_id: null, label: 'to' },
    notes: '',
  };
}

function makeGraph(nodes: GraphNode[], edges: GraphEdge[] = []): GraphDetail {
  return {
    id: 1,
    campaign: 1,
    name: 'Web',
    notes: '',
    nodes,
    edges,
    created_at: '',
    updated_at: '',
  };
}

describe('graph-model', () => {
  describe('endpointKey', () => {
    it('prefixes the node id with node:', () => {
      expect(endpointKey(7)).toBe('node:7');
    });
  });

  describe('mapEndpointOptions', () => {
    it('maps nodes to endpoint options and suffixes PCs with (PC)', () => {
      const nodes = [
        makeNode({ id: 1, kind: 'party', label: 'Party' }),
        makeNode({ id: 2, kind: 'pc', label: 'Thorn' }),
        makeNode({ id: 3, kind: 'npc', label: 'Grix', npc_id: 42 }),
      ];

      const options = mapEndpointOptions(nodes);

      expect(options).toEqual([
        { key: 'node:1', nodeId: 1, kind: 'party', label: 'Party' },
        { key: 'node:2', nodeId: 2, kind: 'pc', label: 'Thorn (PC)' },
        { key: 'node:3', nodeId: 3, kind: 'npc', label: 'Grix' },
      ]);
    });

    it('returns an empty array for no nodes', () => {
      expect(mapEndpointOptions([])).toEqual([]);
    });
  });

  describe('hasPartyNode', () => {
    it('is true when a party node exists', () => {
      const nodes = [
        makeNode({ id: 1, kind: 'npc' }),
        makeNode({ id: 2, kind: 'party' }),
      ];
      expect(hasPartyNode(nodes)).toBe(true);
    });

    it('is false without a party node', () => {
      expect(hasPartyNode([makeNode({ id: 1, kind: 'npc' })])).toBe(false);
      expect(hasPartyNode([])).toBe(false);
    });
  });

  describe('availableNpcs', () => {
    it('excludes NPCs already placed on the graph', () => {
      const campaignNpcs = [makeNpc(1), makeNpc(2), makeNpc(3)];
      const nodes = [
        makeNode({ id: 10, kind: 'npc', npc_id: 2 }),
        makeNode({ id: 11, kind: 'party' }),
        makeNode({ id: 12, kind: 'pc' }),
      ];

      const result = availableNpcs(campaignNpcs, nodes);

      expect(result.map((npc) => npc.id)).toEqual([1, 3]);
    });

    it('returns all NPCs when none are on the graph', () => {
      const campaignNpcs = [makeNpc(1), makeNpc(2)];
      expect(availableNpcs(campaignNpcs, []).map((npc) => npc.id)).toEqual([1, 2]);
    });
  });

  describe('polarityColor', () => {
    it('maps each polarity to a colour', () => {
      expect(polarityColor('positive')).toBe('#2d8a6e');
      expect(polarityColor('negative')).toBe('#c0396b');
      expect(polarityColor('complex')).toBe('#7b5cff');
      expect(polarityColor('neutral')).toBe('#6b628a');
    });
  });

  describe('parseCyNodeId / parseCyEdgeId', () => {
    it('parses the numeric id out of the cytoscape element id', () => {
      expect(parseCyNodeId('node-15')).toBe(15);
      expect(parseCyEdgeId('edge-9')).toBe(9);
    });
  });

  describe('buildCyElements', () => {
    it('builds node elements with fallback grid positions', () => {
      const graph = makeGraph([makeNode({ id: 1, kind: 'npc', label: 'Grix', npc_id: 42 })]);

      const elements = buildCyElements(graph);

      expect(elements.length).toBe(1);
      expect(elements[0].data).toEqual({
        id: 'node-1',
        label: 'Grix',
        kind: 'npc',
        npcId: 42,
      });
      expect(elements[0].position).toEqual({ x: 140, y: 140 });
    });

    it('uses stored positions when present', () => {
      const graph = makeGraph([
        makeNode({ id: 1, kind: 'npc', label: 'Grix', npc_id: 42, pos_x: 200, pos_y: 320 }),
      ]);

      const elements = buildCyElements(graph);

      expect(elements[0].position).toEqual({ x: 200, y: 320 });
    });

    it('nests PC nodes under the party node and orders party first', () => {
      const graph = makeGraph([
        makeNode({ id: 3, kind: 'npc', label: 'Grix', npc_id: 42 }),
        makeNode({ id: 2, kind: 'pc', label: 'Thorn' }),
        makeNode({ id: 1, kind: 'party', label: 'Party' }),
      ]);

      const elements = buildCyElements(graph);

      // Party sorts before pc before npc.
      expect(elements[0].data['id']).toBe('node-1');
      expect(elements[1].data['id']).toBe('node-2');
      expect(elements[1].data['parent']).toBe('node-1');
      expect(elements[2].data['id']).toBe('node-3');
      expect(elements[2].data['parent']).toBeUndefined();
    });

    it('builds edge elements with polarity colours and drops edges to missing nodes', () => {
      const graph = makeGraph(
        [
          makeNode({ id: 1, kind: 'npc', npc_id: 1 }),
          makeNode({ id: 2, kind: 'npc', npc_id: 2 }),
        ],
        [makeEdge(5, 1, 2, 'negative', 'Rivals'), makeEdge(6, 1, 99)],
      );

      const elements = buildCyElements(graph);
      const edges = elements.filter((element) => String(element.data['id']).startsWith('edge-'));

      expect(edges.length).toBe(1);
      expect(edges[0].data).toEqual({
        id: 'edge-5',
        source: 'node-1',
        target: 'node-2',
        label: 'Rivals',
        color: '#c0396b',
      });
    });
  });
});
