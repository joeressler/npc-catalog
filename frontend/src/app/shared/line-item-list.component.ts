import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AbstractControl, FormArray, FormControl, ReactiveFormsModule } from '@angular/forms';

/**
 * Renders a FormArray of simple string controls as an orderable, removable
 * list. The parent keeps ownership of add/remove/move so it can construct the
 * right control shape; this component only renders and emits intent.
 */
@Component({
  selector: 'app-line-item-list',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="line-items">
      @for (control of formArray.controls; track control; let i = $index) {
        <div
          class="line-item"
          [class.has-index]="showIndex"
          [class.is-textarea]="controlType === 'textarea'"
        >
          @if (showIndex) {
            <span class="line-index">{{ i + 1 }}</span>
          }
          @if (controlType === 'textarea') {
            <textarea
              [formControl]="asControl(control)"
              rows="2"
              [placeholder]="placeholder"
            ></textarea>
          } @else {
            <input type="text" [formControl]="asControl(control)" [placeholder]="placeholder" />
          }
          <div class="line-actions">
            <button
              type="button"
              class="btn btn-secondary btn-sm"
              (click)="move.emit({ index: i, direction: -1 })"
              [disabled]="i === 0"
            >
              Up
            </button>
            <button
              type="button"
              class="btn btn-secondary btn-sm"
              (click)="move.emit({ index: i, direction: 1 })"
              [disabled]="i === formArray.length - 1"
            >
              Down
            </button>
            <button type="button" class="btn btn-danger btn-sm" (click)="remove.emit(i)">
              Remove
            </button>
          </div>
        </div>
      }
    </div>
  `,
})
export class LineItemListComponent {
  @Input({ required: true }) formArray!: FormArray;
  @Input() controlType: 'text' | 'textarea' = 'text';
  @Input() placeholder = '';
  @Input() showIndex = false;

  @Output() add = new EventEmitter<void>();
  @Output() remove = new EventEmitter<number>();
  @Output() move = new EventEmitter<{ index: number; direction: -1 | 1 }>();

  asControl(control: AbstractControl): FormControl {
    return control as FormControl;
  }
}
