import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter, map, startWith } from 'rxjs/operators';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="fey-motes" aria-hidden="true">
      @for (mote of motes; track mote.id) {
        <span
          class="fey-mote"
          [style.left]="mote.left"
          [style.top]="mote.top"
          [style.width]="mote.size"
          [style.height]="mote.size"
          [style.animationDelay]="mote.delay"
          [style.animationDuration]="mote.duration"
        ></span>
      }
    </div>
    <div class="app-frame">
      @if (showSiteNav()) {
        <nav class="site-nav glass-panel" aria-label="Primary">
          <a routerLink="/" class="site-nav-brand">NPC Catalog</a>
          <div class="site-nav-links">
            <a routerLink="/" class="btn btn-secondary btn-sm" routerLinkActive="is-active" [routerLinkActiveOptions]="{ exact: true }">
              Campaigns
            </a>
            <a href="/trains/" class="btn btn-secondary btn-sm">South Side Rail</a>
          </div>
        </nav>
      }
      <router-outlet />
    </div>
  `,
  styles: `
    .app-frame {
      position: relative;
      z-index: 1;
      min-height: 100vh;
    }

    .site-nav {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      margin: 0.75rem 1rem 0;
      padding: 0.55rem 0.85rem;
    }

    .site-nav-brand {
      font-family: var(--font-display, Georgia, serif);
      font-weight: 700;
      font-size: 1.05rem;
      color: var(--aero-text);
      text-decoration: none;
      letter-spacing: -0.02em;
    }

    .site-nav-brand:hover {
      color: var(--aero-purple-deep);
    }

    .site-nav-links {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      align-items: center;
    }

    .site-nav-links a.is-active {
      border-color: rgba(123, 92, 255, 0.65);
      box-shadow: 0 0 0 1px rgba(196, 176, 255, 0.35);
    }

    @media (max-width: 640px) {
      .site-nav {
        margin: 0.5rem 0.65rem 0;
        flex-direction: column;
        align-items: stretch;
      }

      .site-nav-links {
        justify-content: flex-start;
      }
    }
  `,
})
export class AppComponent {
  private readonly router = inject(Router);

  readonly showSiteNav = toSignal(
    this.router.events.pipe(
      filter((event): event is NavigationEnd => event instanceof NavigationEnd),
      map((event) => !event.urlAfterRedirects.startsWith('/login')),
      startWith(!this.router.url.startsWith('/login')),
    ),
    { initialValue: !this.router.url.startsWith('/login') },
  );

  readonly motes = [
    { id: 1, left: '8%', top: '18%', size: '6px', delay: '0s', duration: '16s' },
    { id: 2, left: '22%', top: '62%', size: '4px', delay: '2.5s', duration: '20s' },
    { id: 3, left: '38%', top: '28%', size: '5px', delay: '1.2s', duration: '18s' },
    { id: 4, left: '55%', top: '72%', size: '7px', delay: '4s', duration: '22s' },
    { id: 5, left: '68%', top: '14%', size: '4px', delay: '0.8s', duration: '17s' },
    { id: 6, left: '78%', top: '48%', size: '5px', delay: '3.2s', duration: '19s' },
    { id: 7, left: '88%', top: '32%', size: '6px', delay: '5.5s', duration: '21s' },
    { id: 8, left: '14%', top: '82%', size: '4px', delay: '6s', duration: '23s' },
  ];
}
