import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-graph-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './graph-form.component.html',
  styleUrl: './graph-form.component.scss',
})
export class GraphFormComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  editing = false;
  graphId: number | null = null;
  campaignId: number | null = null;
  saving = false;
  error = '';

  form = this.fb.group({
    name: ['', [Validators.required, Validators.maxLength(200)]],
    notes: [''],
  });

  ngOnInit(): void {
    const graphIdParam = this.route.snapshot.paramMap.get('graphId');
    const campaignIdParam = this.route.snapshot.paramMap.get('campaignId');
    this.campaignId = Number(campaignIdParam);

    if (graphIdParam && graphIdParam !== 'new') {
      this.editing = true;
      this.graphId = Number(graphIdParam);

      this.api.getGraph(this.graphId).subscribe({
        next: (graph) => {
          this.campaignId = graph.campaign;
          this.form.patchValue({
            name: graph.name,
            notes: graph.notes,
          });
        },
        error: () => {
          this.error = 'Relationship web not found.';
        },
      });
    }
  }

  backLink(): (string | number)[] {
    if (this.editing && this.graphId && this.campaignId) {
      return ['/campaigns', this.campaignId, 'graphs', this.graphId];
    }
    if (this.campaignId) {
      return ['/campaigns', this.campaignId, 'graphs'];
    }
    return ['/'];
  }

  submit(): void {
    if (this.form.invalid || this.campaignId === null) {
      this.form.markAllAsTouched();
      return;
    }

    this.saving = true;
    this.error = '';
    const payload = {
      name: this.form.value.name!.trim(),
      notes: this.form.value.notes?.trim() ?? '',
    };

    const request =
      this.editing && this.graphId
        ? this.api.updateGraph(this.graphId, payload)
        : this.api.createGraph(this.campaignId, payload);

    request.subscribe({
      next: (graph) => {
        this.router.navigate(['/campaigns', graph.campaign, 'graphs', graph.id]);
      },
      error: () => {
        this.error = 'Could not save relationship web.';
        this.saving = false;
      },
    });
  }
}
