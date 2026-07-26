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
