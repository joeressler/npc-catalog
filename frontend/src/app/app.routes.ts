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
