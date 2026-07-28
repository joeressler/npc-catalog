import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';

import { ApiService } from '../../services/api.service';
import { Campaign, GraphSummary } from '../../models/domain.models';
import { PageHeaderComponent } from '../../shared/page-header.component';

@Component({
  selector: 'app-graph-list',
  standalone: true,
  imports: [CommonModule, RouterLink, PageHeaderComponent],
  templateUrl: './graph-list.component.html',
  styleUrl: './graph-list.component.scss',
})
export class GraphListComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);

  campaign: Campaign | null = null;
  graphs: GraphSummary[] = [];
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

    this.api.getCampaignGraphs(campaignId).subscribe({
      next: (response) => {
        this.graphs = response.results;
        this.loading = false;
      },
      error: () => {
        this.error = 'Could not load relationship webs.';
        this.loading = false;
      },
    });
  }

  imageUrl(): string | null {
    return this.campaign ? this.api.mediaUrl(this.campaign.image) : null;
  }

  subtitle(): string {
    const count = this.graphs.length;
    return `${count} web${count === 1 ? '' : 's'} mapped`;
  }
}
