import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { debounceTime } from 'rxjs/operators';

import { ApiService } from '../../services/api.service';
import { ALIGNMENTS, Campaign, NPC, Tag } from '../../models/domain.models';

@Component({
  selector: 'app-campaign-roster',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './campaign-roster.component.html',
  styleUrl: './campaign-roster.component.scss',
})
export class CampaignRosterComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  campaign: Campaign | null = null;
  npcs: NPC[] = [];
  tags: Tag[] = [];
  alignments = ALIGNMENTS;
  loading = true;
  deleting = false;
  error = '';

  filters = this.fb.group({
    q: [''],
    alignment: [''],
    tag: [''],
    location: [''],
    faction: [''],
  });

  ngOnInit(): void {
    const campaignId = Number(this.route.snapshot.paramMap.get('campaignId'));

    this.api.getCampaign(campaignId).subscribe({
      next: (campaign) => {
        this.campaign = campaign;
      },
      error: () => {
        this.error = 'Campaign not found.';
        this.loading = false;
      },
    });

    this.api.getTags().subscribe({
      next: (response) => {
        this.tags = response.results;
      },
    });

    this.loadNpcs(campaignId);

    this.filters.valueChanges.pipe(debounceTime(250)).subscribe(() => {
      this.loadNpcs(campaignId);
    });
  }

  loadNpcs(campaignId: number): void {
    const raw = this.filters.getRawValue();
    this.api.getCampaignNpcs(campaignId, {
      q: raw.q || undefined,
      alignment: raw.alignment || undefined,
      tag: raw.tag || undefined,
      location: raw.location || undefined,
      faction: raw.faction || undefined,
    }).subscribe({
      next: (response) => {
        this.npcs = response.results;
        this.loading = false;
      },
      error: () => {
        this.error = 'Could not load NPCs.';
        this.loading = false;
      },
    });
  }

  clearFilters(): void {
    this.filters.reset({
      q: '',
      alignment: '',
      tag: '',
      location: '',
      faction: '',
    });
  }

  imageUrl(): string | null {
    return this.campaign ? this.api.mediaUrl(this.campaign.image) : null;
  }

  npcImageUrl(npc: NPC): string | null {
    return this.api.mediaUrl(npc.image);
  }

  locationSubtitle(npc: NPC): string {
    if (npc.catalog_location) {
      return npc.location.trim()
        ? `${npc.catalog_location.title} · ${npc.location}`
        : npc.catalog_location.title;
    }
    return npc.location;
  }

  aliasList(npc: NPC): string {
    return npc.aliases.map((alias) => alias.name).join(', ');
  }

  deleteCampaign(): void {
    if (!this.campaign || this.deleting) {
      return;
    }

    if (
      !confirm(
        `Delete "${this.campaign.name}" and all of its NPCs? This cannot be undone.`,
      )
    ) {
      return;
    }

    this.deleting = true;
    this.api.deleteCampaign(this.campaign.id).subscribe({
      next: () => {
        this.router.navigate(['/']);
      },
      error: () => {
        this.error = 'Could not delete campaign.';
        this.deleting = false;
      },
    });
  }
}
