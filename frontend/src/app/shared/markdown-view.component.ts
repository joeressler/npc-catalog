import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

import { renderMarkdown } from './markdown.util';

@Component({
  selector: 'app-markdown-view',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './markdown-view.component.html',
  styleUrl: './markdown-view.component.scss',
})
export class MarkdownViewComponent {
  @Input() content = '';

  get html(): string {
    return renderMarkdown(this.content);
  }
}
