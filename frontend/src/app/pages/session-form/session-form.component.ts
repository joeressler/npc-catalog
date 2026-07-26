import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormArray, FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { ApiService } from '../../services/api.service';
import { NPC, SessionWritePayload } from '../../models/npc.models';

@Component({
  selector: 'app-session-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './session-form.component.html',
  styleUrl: './session-form.component.scss',
})
export class SessionFormComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  editing = false;
  sessionId: number | null = null;
  campaignId: number | null = null;
  campaignNpcs: NPC[] = [];
  selectedCharacterIds = new Set<number>();
  saving = false;
  error = '';

  form = this.fb.group({
    number: [{ value: '', disabled: true }],
    title: [''],
    overall_notes: [''],
    story_beats: this.fb.array<string>([]),
    clues: this.fb.array<string>([]),
    secrets: this.fb.array<string>([]),
  });

  ngOnInit(): void {
    const sessionIdParam = this.route.snapshot.paramMap.get('sessionId');
    const campaignIdParam = this.route.snapshot.paramMap.get('campaignId');
    this.campaignId = Number(campaignIdParam);

    this.api.getCampaignNpcs(this.campaignId).subscribe({
      next: (response) => {
        this.campaignNpcs = response.results;
      },
    });

    if (sessionIdParam && sessionIdParam !== 'new') {
      this.editing = true;
      this.sessionId = Number(sessionIdParam);
      this.form.controls.number.enable();
      this.form.controls.number.setValidators([Validators.required, Validators.min(1)]);

      this.api.getSession(this.sessionId).subscribe({
        next: (session) => {
          this.campaignId = session.campaign;
          this.form.patchValue({
            number: String(session.number),
            title: session.title,
            overall_notes: session.overall_notes,
          });
          this.setLineItems('story_beats', session.story_beats.map((item) => item.text));
          this.setLineItems('clues', session.clues.map((item) => item.text));
          this.setLineItems('secrets', session.secrets.map((item) => item.text));
          this.selectedCharacterIds = new Set(session.characters.map((character) => character.id));
        },
        error: () => {
          this.error = 'Session not found.';
        },
      });
    }
  }

  get storyBeats(): FormArray {
    return this.form.controls.story_beats;
  }

  get clues(): FormArray {
    return this.form.controls.clues;
  }

  get secrets(): FormArray {
    return this.form.controls.secrets;
  }

  addLineItem(field: 'story_beats' | 'clues' | 'secrets'): void {
    this.lineItems(field).push(this.fb.control(''));
  }

  removeLineItem(field: 'story_beats' | 'clues' | 'secrets', index: number): void {
    this.lineItems(field).removeAt(index);
  }

  moveLineItem(field: 'story_beats' | 'clues' | 'secrets', index: number, direction: -1 | 1): void {
    const items = this.lineItems(field);
    const targetIndex = index + direction;
    if (targetIndex < 0 || targetIndex >= items.length) {
      return;
    }
    const control = items.at(index);
    items.removeAt(index);
    items.insert(targetIndex, control);
  }

  isCharacterSelected(npcId: number): boolean {
    return this.selectedCharacterIds.has(npcId);
  }

  toggleCharacter(npcId: number): void {
    if (this.selectedCharacterIds.has(npcId)) {
      this.selectedCharacterIds.delete(npcId);
    } else {
      this.selectedCharacterIds.add(npcId);
    }
  }

  submit(): void {
    if (this.form.invalid || this.saving || !this.campaignId) {
      this.form.markAllAsTouched();
      return;
    }

    const raw = this.form.getRawValue();
    const payload: SessionWritePayload = {
      title: raw.title?.trim() || '',
      overall_notes: raw.overall_notes?.trim() || '',
      story_beats: this.lineItemValues('story_beats'),
      clues: this.lineItemValues('clues'),
      secrets: this.lineItemValues('secrets'),
      character_ids: [...this.selectedCharacterIds],
    };

    if (this.editing) {
      payload.number = Number(raw.number);
    }

    this.saving = true;
    this.error = '';

    const request$ =
      this.editing && this.sessionId
        ? this.api.updateSession(this.sessionId, payload)
        : this.api.createSession(this.campaignId, payload);

    request$.subscribe({
      next: (session) => {
        this.router.navigate(['/campaigns', this.campaignId, 'sessions', session.id]);
      },
      error: () => {
        this.error = 'Could not save session.';
        this.saving = false;
      },
    });
  }

  backLink(): (string | number)[] {
    if (this.campaignId) {
      return ['/campaigns', this.campaignId, 'sessions'];
    }
    return ['/'];
  }

  private lineItems(field: 'story_beats' | 'clues' | 'secrets'): FormArray {
    return this.form.controls[field];
  }

  private setLineItems(field: 'story_beats' | 'clues' | 'secrets', values: string[]): void {
    const items = this.lineItems(field);
    while (items.length) {
      items.removeAt(0);
    }
    values.forEach((value) => items.push(this.fb.control(value)));
  }

  private lineItemValues(field: 'story_beats' | 'clues' | 'secrets'): string[] {
    return this.lineItems(field)
      .controls.map((control) => String(control.value || '').trim())
      .filter(Boolean);
  }
}
