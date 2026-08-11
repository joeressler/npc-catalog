import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';

import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { Campaign, LocationSummary } from '../../models/domain.models';

@Component({
  selector: 'app-location-list',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './location-list.component.html',
  styleUrl: './location-list.component.scss',
})
export class LocationListComponent implements OnInit {
  private readonly api = inject(ApiService);
  readonly auth = inject(AuthService);
  private readonly route = inject(ActivatedRoute);

  campaign: Campaign | null = null;
  locations: LocationSummary[] = [];
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

    this.api.getCampaignLocations(campaignId).subscribe({
      next: (response) => {
        this.locations = response.results;
        this.loading = false;
      },
      error: () => {
        this.error = 'Could not load locations.';
        this.loading = false;
      },
    });
  }

  imageUrl(path: string | null): string | null {
    return this.api.mediaUrl(path);
  }

  campaignImageUrl(): string | null {
    return this.campaign ? this.api.mediaUrl(this.campaign.image) : null;
  }
}
