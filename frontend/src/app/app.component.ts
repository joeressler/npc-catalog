import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: `
    <div class="app-frame">
      <router-outlet />
    </div>
  `,
  styles: `
    .app-frame {
      min-height: 100vh;
    }
  `,
})
export class AppComponent {}
