import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../services/api.service';
import { AutosizeTextareaDirective } from '../../shared/autosize-textarea.directive';
import {
  ALIGNMENTS,
  Campaign,
  NPC_IMPORT_TEMPLATE,
  NPCImportResult,
} from '../../models/domain.models';

@Component({
  selector: 'app-npc-import',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, AutosizeTextareaDirective],
  templateUrl: './npc-import.component.html',
  styleUrl: './npc-import.component.scss',
})
export class NpcImportComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);

  campaign: Campaign | null = null;
  campaignId = 0;
  step: 'prepare' | 'results' = 'prepare';
  jsonText = '';
  error = '';
  importing = false;
  copied = false;
  result: NPCImportResult | null = null;
  alignments = ALIGNMENTS;
  readonly templateJson = JSON.stringify(NPC_IMPORT_TEMPLATE, null, 2);

  ngOnInit(): void {
    this.campaignId = Number(this.route.snapshot.paramMap.get('campaignId'));
    this.api.getCampaign(this.campaignId).subscribe({
      next: (campaign) => {
        this.campaign = campaign;
      },
      error: () => {
        this.error = 'Campaign not found.';
      },
    });
  }

  async copyTemplate(): Promise<void> {
    try {
      await navigator.clipboard.writeText(this.templateJson);
      this.copied = true;
      window.setTimeout(() => {
        this.copied = false;
      }, 2000);
    } catch {
      this.jsonText = this.templateJson;
      this.error = 'Clipboard was blocked, so the template was pasted into the editor.';
    }
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) {
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      this.jsonText = typeof reader.result === 'string' ? reader.result : '';
      this.error = '';
    };
    reader.onerror = () => {
      this.error = 'Could not read that file.';
    };
    reader.readAsText(file);
    input.value = '';
  }

  importCharacters(): void {
    if (this.importing) {
      return;
    }

    const raw = this.jsonText.trim();
    if (!raw) {
      this.error = 'Paste a JSON object with a characters array, or an array of character objects.';
      this.step = 'prepare';
      return;
    }

    let parsed: unknown;
    try {
      parsed = JSON.parse(raw);
    } catch {
      this.error = 'That is not valid JSON. Check for missing commas, quotes, or brackets.';
      this.step = 'prepare';
      return;
    }

    if (!this.isImportEnvelope(parsed)) {
      this.error =
        'JSON must be an object with a characters array, or an array of character objects.';
      this.step = 'prepare';
      return;
    }

    this.importing = true;
    this.error = '';
    this.api.importCampaignNpcs(this.campaignId, parsed).subscribe({
      next: (result) => {
        this.result = result;
        this.jsonText = this.remainingFailedJson(parsed, result);
        this.step = 'results';
        this.importing = false;
      },
      error: (err: unknown) => {
        this.error = this.apiErrorMessage(err, 'Could not import characters.');
        this.step = 'prepare';
        this.importing = false;
      },
    });
  }

  editFailed(): void {
    this.step = 'prepare';
    this.error = '';
  }

  importMore(): void {
    this.step = 'prepare';
    this.result = null;
    this.error = '';
    this.jsonText = '';
  }

  characterLabel(index: number, name: string | null): string {
    const ordinal = `Character ${index + 1}`;
    return name ? `${ordinal} · ${name}` : ordinal;
  }

  fieldLabel(field: string | null): string {
    return field || 'Character';
  }

  private isImportEnvelope(value: unknown): boolean {
    if (Array.isArray(value)) {
      return true;
    }
    return (
      typeof value === 'object' &&
      value !== null &&
      Array.isArray((value as { characters?: unknown }).characters)
    );
  }

  private remainingFailedJson(parsed: unknown, result: NPCImportResult): string {
    const items = Array.isArray(parsed)
      ? parsed
      : ((parsed as { characters: unknown[] }).characters ?? []);
    const failedItems = result.failed
      .map((entry) => items[entry.index])
      .filter((item) => item !== undefined);
    return JSON.stringify({ characters: failedItems }, null, 2);
  }

  private apiErrorMessage(err: unknown, fallback: string): string {
    if (err instanceof HttpErrorResponse) {
      const detail = err.error?.detail;
      if (typeof detail === 'string' && detail.trim()) {
        return detail;
      }
    }
    return fallback;
  }
}
