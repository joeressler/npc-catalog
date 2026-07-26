import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';

import { ApiService } from '../../services/api.service';
import { SessionDetail } from '../../models/npc.models';

@Component({
  selector: 'app-session-detail',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './session-detail.component.html',
  styleUrl: './session-detail.component.scss',
})
export class SessionDetailComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  session: SessionDetail | null = null;
  loading = true;
  error = '';
  deleting = false;

  ngOnInit(): void {
    const sessionId = Number(this.route.snapshot.paramMap.get('sessionId'));
    this.api.getSession(sessionId).subscribe({
      next: (session) => {
        this.session = session;
        this.loading = false;
      },
      error: () => {
        this.error = 'Session not found.';
        this.loading = false;
      },
    });
  }

  sessionTitle(): string {
    if (!this.session) {
      return '';
    }
    if (this.session.title.trim()) {
      return `Session ${this.session.number} — ${this.session.title}`;
    }
    return `Session ${this.session.number}`;
  }

  deleteSession(): void {
    if (!this.session || this.deleting) {
      return;
    }
    if (!confirm(`Delete ${this.sessionTitle()}?`)) {
      return;
    }

    this.deleting = true;
    const campaignId = this.session.campaign;
    this.api.deleteSession(this.session.id).subscribe({
      next: () => {
        this.router.navigate(['/campaigns', campaignId, 'sessions']);
      },
      error: () => {
        this.error = 'Could not delete session.';
        this.deleting = false;
      },
    });
  }
}
