import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import {
  Campaign,
  GraphDetail,
  GraphEdge,
  GraphEdgeUpdatePayload,
  GraphEdgeWritePayload,
  GraphNode,
  GraphNodePositionPayload,
  GraphNodeWritePayload,
  GraphSummary,
  GraphWritePayload,
  NPC,
  NPCFilters,
  NPCWritePayload,
  PaginatedResponse,
  RelationType,
  RelationTypeWritePayload,
  SessionDetail,
  SessionSummary,
  SessionWritePayload,
  EncounterDetail,
  EncounterSummary,
  EncounterWritePayload,
  LocationDetail,
  LocationSummary,
  LocationWritePayload,
  Tag,
  AiGenerateRequest,
  AiGenerateResponse,
  AiStatus,
} from '../models/domain.models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api';

  getCampaigns(): Observable<PaginatedResponse<Campaign>> {
    return this.http.get<PaginatedResponse<Campaign>>(`${this.base}/campaigns/`);
  }

  getCampaign(id: number): Observable<Campaign> {
    return this.http.get<Campaign>(`${this.base}/campaigns/${id}/`);
  }

  createCampaign(
    name: string,
    image?: File | null,
    playerVisible = false,
  ): Observable<Campaign> {
    const form = new FormData();
    form.append('name', name);
    form.append('player_visible', playerVisible ? 'true' : 'false');
    if (image) {
      form.append('image', image);
    }
    return this.http.post<Campaign>(`${this.base}/campaigns/`, form);
  }

  updateCampaign(
    id: number,
    name: string,
    image?: File | null,
    clearImage = false,
    playerVisible?: boolean,
  ): Observable<Campaign> {
    const form = new FormData();
    form.append('name', name);
    if (playerVisible !== undefined) {
      form.append('player_visible', playerVisible ? 'true' : 'false');
    }
    if (image) {
      form.append('image', image);
    } else if (clearImage) {
      form.append('image', '');
    }
    return this.http.patch<Campaign>(`${this.base}/campaigns/${id}/`, form);
  }

  deleteCampaign(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/campaigns/${id}/`);
  }

  getCampaignNpcs(campaignId: number, filters: NPCFilters = {}): Observable<PaginatedResponse<NPC>> {
    return this.http.get<PaginatedResponse<NPC>>(
      `${this.base}/campaigns/${campaignId}/npcs/`,
      { params: this.buildParams(filters) },
    );
  }

  getNpc(id: number): Observable<NPC> {
    return this.http.get<NPC>(`${this.base}/npcs/${id}/`);
  }

  createNpc(campaignId: number, payload: NPCWritePayload, image?: File | null): Observable<NPC> {
    const form = new FormData();
    form.append('payload', JSON.stringify(payload));
    if (image) {
      form.append('image', image);
    }
    return this.http.post<NPC>(`${this.base}/campaigns/${campaignId}/npcs/`, form);
  }

  updateNpc(
    id: number,
    payload: Partial<NPCWritePayload>,
    image?: File | null,
    clearImage = false,
  ): Observable<NPC> {
    const form = new FormData();
    form.append('payload', JSON.stringify(payload));
    if (image) {
      form.append('image', image);
    } else if (clearImage) {
      form.append('image', '');
    }
    return this.http.patch<NPC>(`${this.base}/npcs/${id}/`, form);
  }

  deleteNpc(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/npcs/${id}/`);
  }

  getTags(): Observable<PaginatedResponse<Tag>> {
    return this.http.get<PaginatedResponse<Tag>>(`${this.base}/tags/`);
  }

  getCampaignSessions(campaignId: number): Observable<PaginatedResponse<SessionSummary>> {
    return this.http.get<PaginatedResponse<SessionSummary>>(
      `${this.base}/campaigns/${campaignId}/sessions/`,
    );
  }

  getSession(id: number): Observable<SessionDetail> {
    return this.http.get<SessionDetail>(`${this.base}/sessions/${id}/`);
  }

  createSession(campaignId: number, payload: SessionWritePayload): Observable<SessionDetail> {
    return this.http.post<SessionDetail>(`${this.base}/campaigns/${campaignId}/sessions/`, payload);
  }

  updateSession(id: number, payload: Partial<SessionWritePayload>): Observable<SessionDetail> {
    return this.http.patch<SessionDetail>(`${this.base}/sessions/${id}/`, payload);
  }

  deleteSession(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/sessions/${id}/`);
  }

  getCampaignEncounters(campaignId: number): Observable<PaginatedResponse<EncounterSummary>> {
    return this.http.get<PaginatedResponse<EncounterSummary>>(
      `${this.base}/campaigns/${campaignId}/encounters/`,
    );
  }

  getEncounter(id: number): Observable<EncounterDetail> {
    return this.http.get<EncounterDetail>(`${this.base}/encounters/${id}/`);
  }

  createEncounter(campaignId: number, payload: EncounterWritePayload): Observable<EncounterDetail> {
    return this.http.post<EncounterDetail>(
      `${this.base}/campaigns/${campaignId}/encounters/`,
      payload,
    );
  }

  updateEncounter(id: number, payload: Partial<EncounterWritePayload>): Observable<EncounterDetail> {
    return this.http.patch<EncounterDetail>(`${this.base}/encounters/${id}/`, payload);
  }

  deleteEncounter(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/encounters/${id}/`);
  }

  cloneEncounter(id: number): Observable<EncounterDetail> {
    return this.http.post<EncounterDetail>(`${this.base}/encounters/${id}/clone/`, {});
  }

  getCampaignLocations(campaignId: number): Observable<PaginatedResponse<LocationSummary>> {
    return this.http.get<PaginatedResponse<LocationSummary>>(
      `${this.base}/campaigns/${campaignId}/locations/`,
    );
  }

  getLocation(id: number): Observable<LocationDetail> {
    return this.http.get<LocationDetail>(`${this.base}/locations/${id}/`);
  }

  createLocation(
    campaignId: number,
    payload: LocationWritePayload,
    image?: File | null,
  ): Observable<LocationDetail> {
    const form = new FormData();
    form.append('payload', JSON.stringify(payload));
    if (image) {
      form.append('image', image);
    }
    return this.http.post<LocationDetail>(`${this.base}/campaigns/${campaignId}/locations/`, form);
  }

  updateLocation(
    id: number,
    payload: Partial<LocationWritePayload>,
    image?: File | null,
    clearImage = false,
  ): Observable<LocationDetail> {
    const form = new FormData();
    form.append('payload', JSON.stringify(payload));
    if (image) {
      form.append('image', image);
    } else if (clearImage) {
      form.append('image', '');
    }
    return this.http.patch<LocationDetail>(`${this.base}/locations/${id}/`, form);
  }

  deleteLocation(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/locations/${id}/`);
  }

  getCampaignGraphs(campaignId: number): Observable<PaginatedResponse<GraphSummary>> {
    return this.http.get<PaginatedResponse<GraphSummary>>(
      `${this.base}/campaigns/${campaignId}/graphs/`,
    );
  }

  getGraph(id: number): Observable<GraphDetail> {
    return this.http.get<GraphDetail>(`${this.base}/graphs/${id}/`);
  }

  createGraph(campaignId: number, payload: GraphWritePayload): Observable<GraphDetail> {
    return this.http.post<GraphDetail>(`${this.base}/campaigns/${campaignId}/graphs/`, payload);
  }

  updateGraph(id: number, payload: Partial<GraphWritePayload>): Observable<GraphDetail> {
    return this.http.patch<GraphDetail>(`${this.base}/graphs/${id}/`, payload);
  }

  deleteGraph(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/graphs/${id}/`);
  }

  getCampaignRelationTypes(campaignId: number): Observable<PaginatedResponse<RelationType>> {
    return this.http.get<PaginatedResponse<RelationType>>(
      `${this.base}/campaigns/${campaignId}/relation-types/`,
    );
  }

  createRelationType(campaignId: number, payload: RelationTypeWritePayload): Observable<RelationType> {
    return this.http.post<RelationType>(
      `${this.base}/campaigns/${campaignId}/relation-types/`,
      payload,
    );
  }

  deleteRelationType(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/relation-types/${id}/`);
  }

  addGraphNode(graphId: number, payload: GraphNodeWritePayload): Observable<GraphNode> {
    return this.http.post<GraphNode>(`${this.base}/graphs/${graphId}/nodes/`, payload);
  }

  updateGraphNodePosition(nodeId: number, payload: GraphNodePositionPayload): Observable<GraphNode> {
    return this.http.patch<GraphNode>(`${this.base}/graph-nodes/${nodeId}/`, payload);
  }

  deleteGraphNode(nodeId: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/graph-nodes/${nodeId}/`);
  }

  addGraphEdge(graphId: number, payload: GraphEdgeWritePayload): Observable<GraphEdge> {
    return this.http.post<GraphEdge>(`${this.base}/graphs/${graphId}/edges/`, payload);
  }

  updateGraphEdge(edgeId: number, payload: GraphEdgeUpdatePayload): Observable<GraphEdge> {
    return this.http.patch<GraphEdge>(`${this.base}/graph-edges/${edgeId}/`, payload);
  }

  deleteGraphEdge(edgeId: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/graph-edges/${edgeId}/`);
  }

  mediaUrl(path: string | null | undefined): string | null {
    if (!path) {
      return null;
    }
    if (path.startsWith('http')) {
      return path;
    }
    return path.startsWith('/') ? path : `/${path}`;
  }

  getAiStatus(): Observable<AiStatus> {
    return this.http.get<AiStatus>(`${this.base}/ai/status/`);
  }

  generateAiImage(payload: AiGenerateRequest): Observable<AiGenerateResponse> {
    return this.http.post<AiGenerateResponse>(`${this.base}/ai/generate-image/`, payload);
  }

  private buildParams(filters: NPCFilters): HttpParams {
    let params = new HttpParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params = params.set(key, value);
      }
    });
    return params;
  }
}
