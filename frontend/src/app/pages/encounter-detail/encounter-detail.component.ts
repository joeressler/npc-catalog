import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';

import { ApiService } from '../../services/api.service';
import { EncounterDetail } from '../../models/domain.models';

@Component({
  selector: 'app-encounter-detail',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './encounter-detail.component.html',
  styleUrl: './encounter-detail.component.scss',
})
export class EncounterDetailComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  encounter: EncounterDetail | null = null;
  loading = true;
  error = '';
  deleting = false;
  cloning = false;

  ngOnInit(): void {
    const encounterId = Number(this.route.snapshot.paramMap.get('encounterId'));
    this.api.getEncounter(encounterId).subscribe({
      next: (encounter) => {
        this.encounter = encounter;
        this.loading = false;
      },
      error: () => {
        this.error = 'Encounter not found.';
        this.loading = false;
      },
    });
  }

  enemyLabel(quantity: number, name: string, creatureType: string): string {
    const typePart = creatureType.trim() ? ` (${creatureType})` : '';
    return `${quantity}× ${name}${typePart}`;
  }

  cloneEncounter(): void {
    if (!this.encounter || this.cloning) {
      return;
    }
    this.cloning = true;
    this.error = '';
    this.api.cloneEncounter(this.encounter.id).subscribe({
      next: (cloned) => {
        this.router.navigate(['/campaigns', cloned.campaign, 'encounters', cloned.id]);
      },
      error: () => {
        this.error = 'Could not clone encounter.';
        this.cloning = false;
      },
    });
  }

  deleteEncounter(): void {
    if (!this.encounter || this.deleting) {
      return;
    }
    if (!confirm(`Delete ${this.encounter.title}?`)) {
      return;
    }

    this.deleting = true;
    const campaignId = this.encounter.campaign;
    this.api.deleteEncounter(this.encounter.id).subscribe({
      next: () => {
        this.router.navigate(['/campaigns', campaignId, 'encounters']);
      },
      error: () => {
        this.error = 'Could not delete encounter.';
        this.deleting = false;
      },
    });
  }
}
