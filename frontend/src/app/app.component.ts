import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
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
      <router-outlet />
    </div>
  `,
  styles: `
    .app-frame {
      position: relative;
      z-index: 1;
      min-height: 100vh;
    }
  `,
})
export class AppComponent {
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
