import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';

import { ApiService } from '../../services/api.service';
import { Campaign, SessionSummary } from '../../models/domain.models';

@Component({
  selector: 'app-session-list',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './session-list.component.html',
  styleUrl: './session-list.component.scss',
})
export class SessionListComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  campaign: Campaign | null = null;
  sessions: SessionSummary[] = [];
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

    this.api.getCampaignSessions(campaignId).subscribe({
      next: (response) => {
        this.sessions = response.results;
        this.loading = false;
      },
      error: () => {
        this.error = 'Could not load sessions.';
        this.loading = false;
      },
    });
  }

  sessionLabel(session: SessionSummary): string {
    if (session.title.trim()) {
      return `Session ${session.number} — ${session.title}`;
    }
    return `Session ${session.number}`;
  }

  imageUrl(): string | null {
    return this.campaign ? this.api.mediaUrl(this.campaign.image) : null;
  }
}
