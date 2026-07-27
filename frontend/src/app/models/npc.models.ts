export interface Campaign {
  id: number;
  name: string;
  image: string | null;
  npc_count?: number;
  created_at: string;
  updated_at: string;
}

export interface Tag {
  id: number;
  name: string;
}

export interface Alias {
  id: number;
  name: string;
}

export interface NPC {
  id: number;
  campaign: number;
  name: string;
  role_occupation: string;
  alignment: AlignmentCode;
  alignment_display: string;
  location: string;
  faction: string;
  attitude: string;
  party_relationship: string;
  image: string | null;
  appearance?: string;
  voice_mannerisms?: string;
  personality_traits?: string;
  motivation_goal?: string;
  secret_hook?: string;
  knowledge?: string;
  inventory?: string;
  dm_notes?: string;
  session_log?: string;
  aliases: Alias[];
  tags: Tag[];
  created_at: string;
  updated_at: string;
}

export type AlignmentCode = 'LG' | 'NG' | 'CG' | 'LN' | 'N' | 'CN' | 'LE' | 'NE' | 'CE';

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface NPCFilters {
  q?: string;
  alignment?: string;
  tag?: string;
  location?: string;
  faction?: string;
  ordering?: string;
}

export interface NPCWritePayload {
  campaign?: number;
  name: string;
  role_occupation: string;
  alignment: AlignmentCode;
  location: string;
  faction?: string;
  attitude: string;
  party_relationship: string;
  appearance?: string;
  voice_mannerisms?: string;
  personality_traits?: string;
  motivation_goal?: string;
  secret_hook?: string;
  knowledge?: string;
  inventory?: string;
  dm_notes?: string;
  session_log?: string;
  aliases?: string[];
  tags?: string[];
}

export const ALIGNMENTS: { code: AlignmentCode; label: string }[] = [
  { code: 'LG', label: 'Lawful Good' },
  { code: 'NG', label: 'Neutral Good' },
  { code: 'CG', label: 'Chaotic Good' },
  { code: 'LN', label: 'Lawful Neutral' },
  { code: 'N', label: 'True Neutral' },
  { code: 'CN', label: 'Chaotic Neutral' },
  { code: 'LE', label: 'Lawful Evil' },
  { code: 'NE', label: 'Neutral Evil' },
  { code: 'CE', label: 'Chaotic Evil' },
];

export interface SessionLineItem {
  id: number;
  text: string;
  sort_order: number;
}

export interface SessionStoryPath {
  id: number;
  name: string;
  sort_order: number;
  beats: SessionLineItem[];
}

export interface SessionStoryPathWrite {
  name: string;
  beats: string[];
}

export interface SessionCharacter {
  id: number;
  name: string;
  role_occupation: string;
  alignment: AlignmentCode;
  alignment_display: string;
}

export interface SessionSummary {
  id: number;
  campaign: number;
  number: number;
  title: string;
  character_count: number;
  created_at: string;
  updated_at: string;
}

export interface SessionDetail extends SessionSummary {
  overall_notes: string;
  story_paths: SessionStoryPath[];
  clues: SessionLineItem[];
  secrets: SessionLineItem[];
  characters: SessionCharacter[];
  encounters: SessionEncounterRef[];
}

export interface SessionWritePayload {
  number?: number | null;
  title?: string;
  overall_notes?: string;
  story_paths?: SessionStoryPathWrite[];
  clues?: string[];
  secrets?: string[];
  character_ids?: number[];
  encounter_ids?: number[];
}

export interface SessionEncounterRef {
  id: number;
  title: string;
  short_description: string;
}

export interface EncounterEnemy {
  id: number;
  quantity: number;
  name: string;
  creature_type: string;
  sort_order: number;
}

export interface EncounterEnemyWrite {
  quantity: number;
  name: string;
  creature_type: string;
}

export interface EncounterLoot {
  id: number;
  description: string;
  sort_order: number;
}

export interface EncounterObject {
  id: number;
  name: string;
  description: string;
  sort_order: number;
}

export interface EncounterObjectWrite {
  name: string;
  description: string;
}

export interface EncounterCharacter {
  id: number;
  name: string;
  role_occupation: string;
  alignment: AlignmentCode;
  alignment_display: string;
}

export interface EncounterSummary {
  id: number;
  campaign: number;
  title: string;
  short_description: string;
  enemy_count: number;
  character_count: number;
  created_at: string;
  updated_at: string;
}

export interface EncounterDetail extends EncounterSummary {
  battlefield_description: string;
  further_notes: string;
  enemies: EncounterEnemy[];
  loot: EncounterLoot[];
  objects: EncounterObject[];
  characters: EncounterCharacter[];
}

export interface EncounterWritePayload {
  title: string;
  short_description?: string;
  battlefield_description?: string;
  further_notes?: string;
  enemies?: EncounterEnemyWrite[];
  loot?: string[];
  objects?: EncounterObjectWrite[];
  character_ids?: number[];
}

export type RelationPolarity = 'positive' | 'negative' | 'neutral' | 'complex';
export type GraphNodeKind = 'npc' | 'party' | 'pc';

export interface RelationType {
  id: number;
  name: string;
  polarity: RelationPolarity;
}

export interface RelationTypeWritePayload {
  name: string;
  polarity: RelationPolarity;
}

export interface GraphEndpoint {
  node_id: number;
  kind: GraphNodeKind;
  npc_id: number | null;
  label: string;
}

export interface GraphNode {
  id: number;
  kind: GraphNodeKind;
  npc_id: number | null;
  label: string;
  pos_x: number | null;
  pos_y: number | null;
}

export interface GraphEdge {
  id: number;
  relation_type: RelationType;
  from_endpoint: GraphEndpoint;
  to_endpoint: GraphEndpoint;
  notes: string;
}

export interface GraphSummary {
  id: number;
  campaign: number;
  name: string;
  notes: string;
  node_count: number;
  edge_count: number;
  created_at: string;
  updated_at: string;
}

export interface GraphDetail extends Omit<GraphSummary, 'node_count' | 'edge_count'> {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface GraphWritePayload {
  name: string;
  notes?: string;
}

export interface GraphNodeWritePayload {
  kind: GraphNodeKind;
  npc_id?: number | null;
  label?: string | null;
}

export interface GraphNodePositionPayload {
  pos_x: number;
  pos_y: number;
}

export interface GraphEdgeWritePayload {
  relation_type_id: number;
  from_node_id: number;
  to_node_id: number;
  notes?: string;
  bidirectional?: boolean;
}

export interface GraphEdgeUpdatePayload {
  relation_type_id?: number;
  notes?: string;
}

export const RELATION_POLARITIES: { value: RelationPolarity; label: string }[] = [
  { value: 'positive', label: 'Positive' },
  { value: 'negative', label: 'Negative' },
  { value: 'neutral', label: 'Neutral' },
  { value: 'complex', label: 'Complex' },
];
