import { Routes } from '@angular/router';

import { authGuard, dmGuard, guestGuard } from './guards/auth.guard';

export const routes: Routes = [
  {
    path: 'login',
    canActivate: [guestGuard],
    loadComponent: () =>
      import('./pages/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: '',
    canActivate: [authGuard],
    canActivateChild: [authGuard],
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./pages/campaign-list/campaign-list.component').then((m) => m.CampaignListComponent),
      },
      {
        path: 'campaigns/new',
        canActivate: [dmGuard],
        loadComponent: () =>
          import('./pages/campaign-form/campaign-form.component').then((m) => m.CampaignFormComponent),
      },
      {
        path: 'campaigns/:campaignId/edit',
        canActivate: [dmGuard],
        loadComponent: () =>
          import('./pages/campaign-form/campaign-form.component').then((m) => m.CampaignFormComponent),
      },
      {
        path: 'campaigns/:campaignId/sessions',
        canActivate: [dmGuard],
        children: [
          {
            path: '',
            loadComponent: () =>
              import('./pages/session-list/session-list.component').then((m) => m.SessionListComponent),
          },
          {
            path: 'new',
            loadComponent: () =>
              import('./pages/session-form/session-form.component').then((m) => m.SessionFormComponent),
          },
          {
            path: ':sessionId/edit',
            loadComponent: () =>
              import('./pages/session-form/session-form.component').then((m) => m.SessionFormComponent),
          },
          {
            path: ':sessionId',
            loadComponent: () =>
              import('./pages/session-detail/session-detail.component').then(
                (m) => m.SessionDetailComponent,
              ),
          },
        ],
      },
      {
        path: 'campaigns/:campaignId/encounters',
        canActivate: [dmGuard],
        children: [
          {
            path: '',
            loadComponent: () =>
              import('./pages/encounter-list/encounter-list.component').then(
                (m) => m.EncounterListComponent,
              ),
          },
          {
            path: 'new',
            loadComponent: () =>
              import('./pages/encounter-form/encounter-form.component').then(
                (m) => m.EncounterFormComponent,
              ),
          },
          {
            path: ':encounterId/edit',
            loadComponent: () =>
              import('./pages/encounter-form/encounter-form.component').then(
                (m) => m.EncounterFormComponent,
              ),
          },
          {
            path: ':encounterId',
            loadComponent: () =>
              import('./pages/encounter-detail/encounter-detail.component').then(
                (m) => m.EncounterDetailComponent,
              ),
          },
        ],
      },
      {
        path: 'campaigns/:campaignId/locations/new',
        canActivate: [dmGuard],
        loadComponent: () =>
          import('./pages/location-form/location-form.component').then((m) => m.LocationFormComponent),
      },
      {
        path: 'campaigns/:campaignId/locations/:locationId/edit',
        canActivate: [dmGuard],
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
        canActivate: [dmGuard],
        loadComponent: () =>
          import('./pages/graph-form/graph-form.component').then((m) => m.GraphFormComponent),
      },
      {
        path: 'campaigns/:campaignId/graphs/:graphId/edit',
        canActivate: [dmGuard],
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
        path: 'campaigns/:campaignId',
        loadComponent: () =>
          import('./pages/campaign-roster/campaign-roster.component').then((m) => m.CampaignRosterComponent),
      },
      {
        path: 'campaigns/:campaignId/npcs/new',
        canActivate: [dmGuard],
        loadComponent: () =>
          import('./pages/npc-form/npc-form.component').then((m) => m.NpcFormComponent),
      },
      {
        path: 'npcs/:npcId',
        loadComponent: () =>
          import('./pages/npc-detail/npc-detail.component').then((m) => m.NpcDetailComponent),
      },
      {
        path: 'npcs/:npcId/edit',
        canActivate: [dmGuard],
        loadComponent: () =>
          import('./pages/npc-form/npc-form.component').then((m) => m.NpcFormComponent),
      },
      { path: '**', redirectTo: '' },
    ],
  },
];
