import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

import { NPC } from '../models/domain.models';

/**
 * Checkbox grid for selecting NPCs to link to a session/encounter. The parent
 * owns the selection set and toggles it in response to `toggle` events.
 */
@Component({
  selector: 'app-npc-multi-select',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="character-grid">
      @for (npc of npcs; track npc.id) {
        <label class="character-option">
          <input
            type="checkbox"
            [checked]="selectedIds.has(npc.id)"
            (change)="toggle.emit(npc.id)"
          />
          <span>
            <strong>{{ npc.name }}</strong>
            <small>{{ npc.role_occupation }}</small>
          </span>
        </label>
      }
    </div>
  `,
})
export class NpcMultiSelectComponent {
  @Input({ required: true }) npcs: NPC[] = [];
  @Input({ required: true }) selectedIds = new Set<number>();
  @Output() toggle = new EventEmitter<number>();
}
