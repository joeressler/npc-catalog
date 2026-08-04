import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import {
  FormArray,
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';

import { ApiService } from '../../services/api.service';
import { AutosizeTextareaDirective } from '../../shared/autosize-textarea.directive';
import { MarkdownFieldComponent } from '../../shared/markdown-field.component';
import {
  EncounterSummary,
  LocationSummary,
  NPC,
  SessionStoryPath,
  SessionWritePayload,
} from '../../models/domain.models';

@Component({
  selector: 'app-session-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, MarkdownFieldComponent, AutosizeTextareaDirective],
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
  campaignEncounters: EncounterSummary[] = [];
  campaignLocations: LocationSummary[] = [];
  selectedLocationIds = new Set<number>();
  selectedNpcIds = new Set<number>();
  selectedEncounterIds = new Set<number>();
  saving = false;
  error = '';

  form = this.fb.group({
    number: [{ value: '', disabled: true }],
    title: [''],
    overall_notes: [''],
    story_paths: this.fb.array<FormGroup>([]),
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

    this.api.getCampaignEncounters(this.campaignId).subscribe({
      next: (response) => {
        this.campaignEncounters = response.results;
      },
    });

    this.api.getCampaignLocations(this.campaignId).subscribe({
      next: (response) => {
        this.campaignLocations = response.results;
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
          this.setStoryPaths(session.story_paths);
          this.setLineItems('clues', session.clues.map((item) => item.text));
          this.setLineItems('secrets', session.secrets.map((item) => item.text));
          this.selectedLocationIds = new Set(session.locations.map((location) => location.id));
          this.selectedNpcIds = new Set(session.npcs.map((npc) => npc.id));
          this.selectedEncounterIds = new Set(session.encounters.map((encounter) => encounter.id));
        },
        error: () => {
          this.error = 'Session not found.';
        },
      });
    }
  }

  get storyPaths(): FormArray<FormGroup> {
    return this.form.controls.story_paths;
  }

  get clues(): FormArray {
    return this.form.controls.clues;
  }

  get secrets(): FormArray {
    return this.form.controls.secrets;
  }

  pathBeats(pathIndex: number): FormArray {
    return this.storyPaths.at(pathIndex).controls['beats'] as FormArray;
  }

  addStoryPath(): void {
    this.storyPaths.push(this.createPathGroup('', []));
  }

  removeStoryPath(pathIndex: number): void {
    this.storyPaths.removeAt(pathIndex);
  }

  moveStoryPath(pathIndex: number, direction: -1 | 1): void {
    this.moveFormArrayItem(this.storyPaths, pathIndex, direction);
  }

  addPathBeat(pathIndex: number): void {
    this.pathBeats(pathIndex).push(this.fb.control(''));
  }

  removePathBeat(pathIndex: number, beatIndex: number): void {
    this.pathBeats(pathIndex).removeAt(beatIndex);
  }

  movePathBeat(pathIndex: number, beatIndex: number, direction: -1 | 1): void {
    this.moveFormArrayItem(this.pathBeats(pathIndex), beatIndex, direction);
  }

  addLineItem(field: 'clues' | 'secrets'): void {
    this.lineItems(field).push(this.fb.control(''));
  }

  removeLineItem(field: 'clues' | 'secrets', index: number): void {
    this.lineItems(field).removeAt(index);
  }

  moveLineItem(field: 'clues' | 'secrets', index: number, direction: -1 | 1): void {
    this.moveFormArrayItem(this.lineItems(field), index, direction);
  }

  isNpcSelected(npcId: number): boolean {
    return this.selectedNpcIds.has(npcId);
  }

  toggleNpc(npcId: number): void {
    if (this.selectedNpcIds.has(npcId)) {
      this.selectedNpcIds.delete(npcId);
    } else {
      this.selectedNpcIds.add(npcId);
    }
  }

  isEncounterSelected(encounterId: number): boolean {
    return this.selectedEncounterIds.has(encounterId);
  }

  toggleEncounter(encounterId: number): void {
    if (this.selectedEncounterIds.has(encounterId)) {
      this.selectedEncounterIds.delete(encounterId);
    } else {
      this.selectedEncounterIds.add(encounterId);
    }
  }

  isLocationSelected(locationId: number): boolean {
    return this.selectedLocationIds.has(locationId);
  }

  toggleLocation(locationId: number): void {
    if (this.selectedLocationIds.has(locationId)) {
      this.selectedLocationIds.delete(locationId);
    } else {
      this.selectedLocationIds.add(locationId);
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
      story_paths: this.storyPathValues(),
      clues: this.lineItemValues('clues'),
      secrets: this.lineItemValues('secrets'),
      location_ids: [...this.selectedLocationIds],
      npc_ids: [...this.selectedNpcIds],
      encounter_ids: [...this.selectedEncounterIds],
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

  private createPathGroup(name: string, beats: string[]): FormGroup {
    return this.fb.group({
      name: [name, Validators.required],
      beats: this.fb.array(beats.map((beat) => this.fb.control(beat))),
    });
  }

  private setStoryPaths(paths: SessionStoryPath[]): void {
    while (this.storyPaths.length) {
      this.storyPaths.removeAt(0);
    }
    paths.forEach((path) => {
      this.storyPaths.push(this.createPathGroup(path.name, path.beats.map((beat) => beat.text)));
    });
  }

  private storyPathValues(): SessionWritePayload['story_paths'] {
    return this.storyPaths.controls
      .map((pathGroup) => {
        const name = String(pathGroup.controls['name'].value || '').trim();
        const beats = (pathGroup.controls['beats'] as FormArray).controls
          .map((control) => String(control.value || '').trim())
          .filter(Boolean);
        return { name, beats };
      })
      .filter((path) => path.name.length > 0);
  }

  private lineItems(field: 'clues' | 'secrets'): FormArray {
    return this.form.controls[field];
  }

  private setLineItems(field: 'clues' | 'secrets', values: string[]): void {
    const items = this.lineItems(field);
    while (items.length) {
      items.removeAt(0);
    }
    values.forEach((value) => items.push(this.fb.control(value)));
  }

  private lineItemValues(field: 'clues' | 'secrets'): string[] {
    return this.lineItems(field)
      .controls.map((control) => String(control.value || '').trim())
      .filter(Boolean);
  }

  private moveFormArrayItem(array: FormArray, index: number, direction: -1 | 1): void {
    const targetIndex = index + direction;
    if (targetIndex < 0 || targetIndex >= array.length) {
      return;
    }
    const current = array.at(index);
    array.setControl(index, array.at(targetIndex));
    array.setControl(targetIndex, current);
  }
}
