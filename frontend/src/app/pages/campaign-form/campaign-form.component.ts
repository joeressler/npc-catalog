import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-campaign-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './campaign-form.component.html',
  styleUrl: './campaign-form.component.scss',
})
export class CampaignFormComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  editing = false;
  campaignId: number | null = null;
  currentImage: string | null = null;
  selectedFile: File | null = null;
  previewUrl: string | null = null;
  saving = false;
  deleting = false;
  error = '';

  form = this.fb.group({
    name: ['', [Validators.required, Validators.maxLength(200)]],
  });

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam) {
      this.editing = true;
      this.campaignId = Number(idParam);
      this.api.getCampaign(this.campaignId).subscribe({
        next: (campaign) => {
          this.form.patchValue({ name: campaign.name });
          this.currentImage = this.api.mediaUrl(campaign.image);
        },
        error: () => {
          this.error = 'Campaign not found.';
        },
      });
    }
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    this.selectedFile = file;
    if (this.previewUrl) {
      URL.revokeObjectURL(this.previewUrl);
    }
    this.previewUrl = file ? URL.createObjectURL(file) : null;
  }

  submit(): void {
    if (this.form.invalid || this.saving || this.deleting) {
      this.form.markAllAsTouched();
      return;
    }

    this.saving = true;
    this.error = '';
    const name = this.form.value.name!.trim();

    const request$ =
      this.editing && this.campaignId
        ? this.api.updateCampaign(this.campaignId, name, this.selectedFile)
        : this.api.createCampaign(name, this.selectedFile);

    request$.subscribe({
      next: (campaign) => {
        this.router.navigate(['/campaigns', campaign.id]);
      },
      error: () => {
        this.error = 'Could not save campaign.';
        this.saving = false;
      },
    });
  }

  deleteCampaign(): void {
    if (!this.editing || !this.campaignId || this.deleting || this.saving) {
      return;
    }

    const name = this.form.value.name?.trim() || 'this campaign';
    if (!confirm(`Delete "${name}" and all of its NPCs? This cannot be undone.`)) {
      return;
    }

    this.deleting = true;
    this.error = '';
    this.api.deleteCampaign(this.campaignId).subscribe({
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
