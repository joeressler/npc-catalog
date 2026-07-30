import { Component, OnInit, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';

import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { Campaign } from '../../models/domain.models';

@Component({
  selector: 'app-campaign-list',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './campaign-list.component.html',
  styleUrl: './campaign-list.component.scss',
})
export class CampaignListComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  campaigns: Campaign[] = [];
  loading = true;
  error = '';

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

  logout(): void {
    this.auth.logout().subscribe({
      next: () => void this.router.navigate(['/login']),
      error: () => void this.router.navigate(['/login']),
    });
  }
}
