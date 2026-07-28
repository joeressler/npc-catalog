import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';

import { ApiService } from '../../services/api.service';
import { Campaign, EncounterSummary } from '../../models/domain.models';
import { PageHeaderComponent } from '../../shared/page-header.component';

@Component({
  selector: 'app-encounter-list',
  standalone: true,
  imports: [CommonModule, RouterLink, PageHeaderComponent],
  templateUrl: './encounter-list.component.html',
  styleUrl: './encounter-list.component.scss',
})
export class EncounterListComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);

  campaign: Campaign | null = null;
  encounters: EncounterSummary[] = [];
  loading = true;
  error = '';

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

    this.api.getCampaignEncounters(campaignId).subscribe({
      next: (response) => {
        this.encounters = response.results;
        this.loading = false;
      },
      error: () => {
        this.error = 'Could not load encounters.';
        this.loading = false;
      },
    });
  }

  imageUrl(): string | null {
    return this.campaign ? this.api.mediaUrl(this.campaign.image) : null;
  }

  subtitle(): string {
    const count = this.encounters.length;
    return `${count} encounter${count === 1 ? '' : 's'} prepared`;
  }
}
