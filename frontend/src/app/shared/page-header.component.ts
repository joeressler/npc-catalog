import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

/**
 * Shared page/list heading. Projected content is rendered in the actions slot
 * (typically buttons / router links).
 *
 * - `variant="page"` renders the simple `.page-header` chrome used by forms.
 * - `variant="list"` renders the `.list-header glass-panel` chrome used by list
 *   screens, including an optional campaign thumbnail.
 */
@Component({
  selector: 'app-page-header',
  standalone: true,
  imports: [CommonModule],
  template: `
    @if (variant === 'list') {
      <header class="list-header glass-panel">
        <div class="list-title">
          @if (imageUrl) {
            <img class="campaign-thumb" [src]="imageUrl" [alt]="title" />
          }
          <div>
            @if (eyebrow) {
              <p class="eyebrow">{{ eyebrow }}</p>
            }
            <h1 class="page-title">{{ title }}</h1>
            @if (subtitle) {
              <p class="page-subtitle">{{ subtitle }}</p>
            }
          </div>
        </div>
        <div class="header-actions">
          <ng-content></ng-content>
        </div>
      </header>
    } @else {
      <header class="page-header">
        <div>
          @if (eyebrow) {
            <p class="eyebrow">{{ eyebrow }}</p>
          }
          <h1 class="page-title">{{ title }}</h1>
          @if (subtitle) {
            <p class="page-subtitle">{{ subtitle }}</p>
          }
        </div>
        <div class="header-actions">
          <ng-content></ng-content>
        </div>
      </header>
    }
  `,
})
export class PageHeaderComponent {
  @Input({ required: true }) title = '';
  @Input() subtitle?: string;
  @Input() eyebrow?: string;
  @Input() imageUrl?: string | null;
  @Input() variant: 'page' | 'list' = 'page';
}
