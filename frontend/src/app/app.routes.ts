import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./pages/campaign-list/campaign-list.component').then((m) => m.CampaignListComponent),
  },
  {
    path: 'campaigns/new',
    loadComponent: () =>
      import('./pages/campaign-form/campaign-form.component').then((m) => m.CampaignFormComponent),
  },
  {
    path: 'campaigns/:id/edit',
    loadComponent: () =>
      import('./pages/campaign-form/campaign-form.component').then((m) => m.CampaignFormComponent),
  },
  {
    path: 'campaigns/:campaignId/sessions/new',
    loadComponent: () =>
      import('./pages/session-form/session-form.component').then((m) => m.SessionFormComponent),
  },
  {
    path: 'campaigns/:campaignId/sessions/:sessionId/edit',
    loadComponent: () =>
      import('./pages/session-form/session-form.component').then((m) => m.SessionFormComponent),
  },
  {
    path: 'campaigns/:campaignId/sessions/:sessionId',
    loadComponent: () =>
      import('./pages/session-detail/session-detail.component').then((m) => m.SessionDetailComponent),
  },
  {
    path: 'campaigns/:campaignId/sessions',
    loadComponent: () =>
      import('./pages/session-list/session-list.component').then((m) => m.SessionListComponent),
  },
  {
    path: 'campaigns/:campaignId/encounters/new',
    loadComponent: () =>
      import('./pages/encounter-form/encounter-form.component').then((m) => m.EncounterFormComponent),
  },
  {
    path: 'campaigns/:campaignId/encounters/:encounterId/edit',
    loadComponent: () =>
      import('./pages/encounter-form/encounter-form.component').then((m) => m.EncounterFormComponent),
  },
  {
    path: 'campaigns/:campaignId/encounters/:encounterId',
    loadComponent: () =>
      import('./pages/encounter-detail/encounter-detail.component').then(
        (m) => m.EncounterDetailComponent,
      ),
  },
  {
    path: 'campaigns/:campaignId/encounters',
    loadComponent: () =>
      import('./pages/encounter-list/encounter-list.component').then((m) => m.EncounterListComponent),
  },
  {
    path: 'campaigns/:campaignId/locations/new',
    loadComponent: () =>
      import('./pages/location-form/location-form.component').then((m) => m.LocationFormComponent),
  },
  {
    path: 'campaigns/:campaignId/locations/:locationId/edit',
    loadComponent: () =>
      import('./pages/location-form/location-form.component').then((m) => m.LocationFormComponent),
  },
  {
    path: 'campaigns/:campaignId/locations/:locationId',
    loadComponent: () =>
      import('./pages/location-detail/location-detail.component').then((m) => m.LocationDetailComponent),
  },
  {
    path: 'campaigns/:campaignId/locations',
    loadComponent: () =>
      import('./pages/location-list/location-list.component').then((m) => m.LocationListComponent),
  },
  {
    path: 'campaigns/:campaignId/graphs/new',
    loadComponent: () =>
      import('./pages/graph-form/graph-form.component').then((m) => m.GraphFormComponent),
  },
  {
    path: 'campaigns/:campaignId/graphs/:graphId/edit',
    loadComponent: () =>
      import('./pages/graph-form/graph-form.component').then((m) => m.GraphFormComponent),
  },
  {
    path: 'campaigns/:campaignId/graphs/:graphId',
    loadComponent: () =>
      import('./pages/graph-detail/graph-detail.component').then((m) => m.GraphDetailComponent),
  },
  {
    path: 'campaigns/:campaignId/graphs',
    loadComponent: () =>
      import('./pages/graph-list/graph-list.component').then((m) => m.GraphListComponent),
  },
  {
    path: 'campaigns/:id',
    loadComponent: () =>
      import('./pages/campaign-roster/campaign-roster.component').then((m) => m.CampaignRosterComponent),
  },
  {
    path: 'campaigns/:campaignId/npcs/new',
    loadComponent: () =>
      import('./pages/npc-form/npc-form.component').then((m) => m.NpcFormComponent),
  },
  {
    path: 'npcs/:id',
    loadComponent: () =>
      import('./pages/npc-detail/npc-detail.component').then((m) => m.NpcDetailComponent),
  },
  {
    path: 'npcs/:id/edit',
    loadComponent: () =>
      import('./pages/npc-form/npc-form.component').then((m) => m.NpcFormComponent),
  },
  { path: '**', redirectTo: '' },
];
