import { Component, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';

import { ApiService } from '../../services/api.service';
import { Campaign } from '../../models/npc.models';

@Component({
  selector: 'app-campaign-list',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './campaign-list.component.html',
  styleUrl: './campaign-list.component.scss',
})
export class CampaignListComponent implements OnInit {
  campaigns: Campaign[] = [];
  loading = true;
  error = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.getCampaigns().subscribe({
      next: (response) => {
        this.campaigns = response.results;
        this.loading = false;
      },
      error: () => {
        this.error = 'Could not load campaigns.';
        this.loading = false;
      },
    });
  }

  imageUrl(campaign: Campaign): string | null {
    return this.api.mediaUrl(campaign.image);
  }
}
