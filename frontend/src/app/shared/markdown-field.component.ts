import {
  AfterViewInit,
  Component,
  forwardRef,
  Input,
  ViewChild,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  ControlValueAccessor,
  NG_VALUE_ACCESSOR,
} from '@angular/forms';

import { AutosizeTextareaDirective } from './autosize-textarea.directive';
import { renderMarkdown } from './markdown.util';

type MarkdownFieldMode = 'edit' | 'preview';

@Component({
  selector: 'app-markdown-field',
  standalone: true,
  imports: [CommonModule, AutosizeTextareaDirective],
  templateUrl: './markdown-field.component.html',
  styleUrl: './markdown-field.component.scss',
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => MarkdownFieldComponent),
      multi: true,
    },
  ],
})
export class MarkdownFieldComponent implements ControlValueAccessor, AfterViewInit {
  @Input({ required: true }) label!: string;
  @Input({ required: true }) inputId!: string;
  @Input() rows = 5;
  @Input() placeholder = '';

  @ViewChild(AutosizeTextareaDirective) private autosize?: AutosizeTextareaDirective;

  mode: MarkdownFieldMode = 'edit';
  value = '';
  disabled = false;

  private onChange: (value: string) => void = () => {};
  private onTouched: () => void = () => {};

  ngAfterViewInit(): void {
    this.autosize?.refresh();
  }

  get previewHtml(): string {
    return renderMarkdown(this.value);
  }

  writeValue(value: string | null): void {
    this.value = value ?? '';
    queueMicrotask(() => this.autosize?.refresh());
  }

  registerOnChange(fn: (value: string) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(disabled: boolean): void {
    this.disabled = disabled;
  }

  setMode(mode: MarkdownFieldMode): void {
    this.mode = mode;
    if (mode === 'edit') {
      queueMicrotask(() => this.autosize?.refresh());
    }
  }

  onInput(event: Event): void {
    const target = event.target as HTMLTextAreaElement;
    this.value = target.value;
    this.onChange(this.value);
  }

  onBlur(): void {
    this.onTouched();
  }
}
