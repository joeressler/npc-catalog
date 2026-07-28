import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';

import { ApiService } from '../../services/api.service';
import { LocationDetail } from '../../models/domain.models';

@Component({
  selector: 'app-location-detail',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './location-detail.component.html',
  styleUrl: './location-detail.component.scss',
})
export class LocationDetailComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  location: LocationDetail | null = null;
  loading = true;
  error = '';
  deleting = false;

  ngOnInit(): void {
    const locationId = Number(this.route.snapshot.paramMap.get('locationId'));
    this.api.getLocation(locationId).subscribe({
      next: (location) => {
        this.location = location;
        this.loading = false;
      },
      error: () => {
        this.error = 'Location not found.';
        this.loading = false;
      },
    });
  }

  imageUrl(): string | null {
    return this.location ? this.api.mediaUrl(this.location.image) : null;
  }

  deleteLocation(): void {
    if (!this.location || this.deleting) {
      return;
    }
    if (!confirm(`Delete ${this.location.title}?`)) {
      return;
    }

    this.deleting = true;
    const campaignId = this.location.campaign;
    this.api.deleteLocation(this.location.id).subscribe({
      next: () => {
        this.router.navigate(['/campaigns', campaignId, 'locations']);
      },
      error: () => {
        this.error = 'Could not delete location.';
        this.deleting = false;
      },
    });
  }
}
