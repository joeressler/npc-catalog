import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';

import { ApiService } from '../../services/api.service';
import { NPC } from '../../models/domain.models';

interface DossierSection {
  title: string;
  content: string;
  open: boolean;
}

@Component({
  selector: 'app-npc-detail',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './npc-detail.component.html',
  styleUrl: './npc-detail.component.scss',
})
export class NpcDetailComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  npc: NPC | null = null;
  portraitUrl: string | null = null;
  sections: DossierSection[] = [];
  loading = true;
  error = '';
  deleting = false;

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('npcId'));
    this.api.getNpc(id).subscribe({
      next: (npc) => {
        this.npc = npc;
        this.portraitUrl = this.api.mediaUrl(npc.image);
        this.sections = [
          { title: 'Appearance', content: npc.appearance || '', open: true },
          { title: 'Voice / Accent / Mannerisms', content: npc.voice_mannerisms || '', open: false },
          { title: 'Personality Traits', content: npc.personality_traits || '', open: false },
          { title: 'Motivation / Goal', content: npc.motivation_goal || '', open: false },
          { title: 'Secret / Hook', content: npc.secret_hook || '', open: false },
          { title: 'Knowledge', content: npc.knowledge || '', open: false },
          { title: 'Inventory / Notable Items', content: npc.inventory || '', open: false },
          { title: 'DM Notes', content: npc.dm_notes || '', open: false },
          { title: 'Session Log', content: npc.session_log || '', open: false },
        ].filter((section) => section.content.trim().length > 0);
        this.loading = false;
      },
      error: () => {
        this.error = 'NPC not found.';
        this.loading = false;
      },
    });
  }

  toggleSection(section: DossierSection): void {
    section.open = !section.open;
  }

  aliasList(): string {
    if (!this.npc) {
      return '';
    }
    return this.npc.aliases.map((alias) => alias.name).join(', ');
  }

  deleteNpc(): void {
    if (!this.npc || this.deleting) {
      return;
    }
    if (!confirm(`Delete ${this.npc.name}?`)) {
      return;
    }

    this.deleting = true;
    const campaignId = this.npc.campaign;
    this.api.deleteNpc(this.npc.id).subscribe({
      next: () => {
        this.router.navigate(['/campaigns', campaignId]);
      },
      error: () => {
        this.error = 'Could not delete NPC.';
        this.deleting = false;
      },
    });
  }
}
