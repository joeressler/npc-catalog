import { Component, EventEmitter, Input, OnDestroy, OnInit, Output, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../services/api.service';
import { AiGenerateKind } from '../../models/domain.models';

@Component({
  selector: 'app-ai-image-generate',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './ai-image-generate.component.html',
  styleUrl: './ai-image-generate.component.scss',
})
export class AiImageGenerateComponent implements OnInit, OnDestroy {
  private readonly api = inject(ApiService);

  @Input({ required: true }) kind!: AiGenerateKind;
  /** Current form field bag sent to the prompt builder. */
  @Input({ required: true }) fields!: Record<string, unknown>;
  @Input() disabled = false;

  @Output() readonly imageChosen = new EventEmitter<File>();

  available = false;
  panelOpen = false;
  generating = false;
  showGuidance = false;
  guidance = '';
  error = '';
  previewDataUrl: string | null = null;
  private objectUrl: string | null = null;

  ngOnInit(): void {
    this.api.getAiStatus().subscribe({
      next: (status) => {
        this.available = status.enabled;
      },
      error: () => {
        this.available = false;
      },
    });
  }

  ngOnDestroy(): void {
    this.revokeObjectUrl();
  }

  get buttonLabel(): string {
    return this.kind === 'npc' ? 'Generate portrait' : 'Generate landscape';
  }

  openGenerate(): void {
    if (this.disabled || this.generating) {
      return;
    }
    this.panelOpen = true;
    this.showGuidance = false;
    this.error = '';
    this.previewDataUrl = null;
    this.runGenerate();
  }

  cancel(): void {
    this.panelOpen = false;
    this.generating = false;
    this.showGuidance = false;
    this.error = '';
    this.previewDataUrl = null;
    this.revokeObjectUrl();
  }

  tryAgain(): void {
    this.showGuidance = true;
    this.error = '';
  }

  retryWithGuidance(): void {
    if (this.generating) {
      return;
    }
    this.previewDataUrl = null;
    this.runGenerate();
  }

  save(): void {
    if (!this.previewDataUrl) {
      return;
    }
    const file = this.dataUrlToFile(
      this.previewDataUrl,
      this.kind === 'npc' ? 'ai-portrait.png' : 'ai-landscape.png',
    );
    this.imageChosen.emit(file);
    this.cancel();
  }

  private runGenerate(): void {
    this.generating = true;
    this.error = '';
    this.api
      .generateAiImage({
        kind: this.kind,
        fields: this.fields ?? {},
        guidance: this.guidance.trim() || null,
      })
      .subscribe({
        next: (result) => {
          this.previewDataUrl = `data:${result.mime_type};base64,${result.image_base64}`;
          this.generating = false;
        },
        error: (err) => {
          const detail = err?.error?.detail;
          this.error =
            typeof detail === 'string'
              ? detail
              : 'Could not generate an image. Check that ComfyUI is running.';
          this.generating = false;
        },
      });
  }

  private dataUrlToFile(dataUrl: string, filename: string): File {
    const [header, data] = dataUrl.split(',');
    const mimeMatch = /data:(.*?);base64/.exec(header);
    const mime = mimeMatch?.[1] || 'image/png';
    const binary = atob(data);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) {
      bytes[i] = binary.charCodeAt(i);
    }
    return new File([bytes], filename, { type: mime });
  }

  private revokeObjectUrl(): void {
    if (this.objectUrl) {
      URL.revokeObjectURL(this.objectUrl);
      this.objectUrl = null;
    }
  }
}
