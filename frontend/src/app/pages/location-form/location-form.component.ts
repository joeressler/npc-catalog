import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import {
  FormArray,
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';

import { MarkdownFieldComponent } from '../../shared/markdown-field.component';
import { ApiService } from '../../services/api.service';
import {
  LocationObject,
  LocationWritePayload,
  NPC,
} from '../../models/domain.models';

@Component({
  selector: 'app-location-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, MarkdownFieldComponent],
  templateUrl: './location-form.component.html',
  styleUrl: './location-form.component.scss',
})
export class LocationFormComponent implements OnInit, OnDestroy {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  editing = false;
  locationId: number | null = null;
  campaignId: number | null = null;
  campaignNpcs: NPC[] = [];
  selectedNpcIds = new Set<number>();
  saving = false;
  error = '';
  currentImage: string | null = null;
  selectedFile: File | null = null;
  previewUrl: string | null = null;
  imageCleared = false;

  form = this.fb.group({
    title: ['', Validators.required],
    description: [''],
    loot: this.fb.array<string>([]),
    objects: this.fb.array<FormGroup>([]),
  });

  ngOnInit(): void {
    const locationIdParam = this.route.snapshot.paramMap.get('locationId');
    const campaignIdParam = this.route.snapshot.paramMap.get('campaignId');
    this.campaignId = Number(campaignIdParam);

    this.api.getCampaignNpcs(this.campaignId).subscribe({
      next: (response) => {
        this.campaignNpcs = response.results;
      },
    });

    if (locationIdParam && locationIdParam !== 'new') {
      this.editing = true;
      this.locationId = Number(locationIdParam);

      this.api.getLocation(this.locationId).subscribe({
        next: (location) => {
          this.campaignId = location.campaign;
          this.currentImage = this.api.mediaUrl(location.image);
          this.form.patchValue({
            title: location.title,
            description: location.description,
          });
          this.setLoot(location.loot.map((item) => item.description));
          this.setObjects(location.objects);
          this.selectedNpcIds = new Set(location.npcs.map((npc) => npc.id));
        },
        error: () => {
          this.error = 'Location not found.';
        },
      });
    }
  }

  ngOnDestroy(): void {
    if (this.previewUrl) {
      URL.revokeObjectURL(this.previewUrl);
    }
  }

  get loot(): FormArray {
    return this.form.controls.loot;
  }

  get objects(): FormArray<FormGroup> {
    return this.form.controls.objects;
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    this.selectedFile = file;
    this.imageCleared = false;
    if (this.previewUrl) {
      URL.revokeObjectURL(this.previewUrl);
    }
    this.previewUrl = file ? URL.createObjectURL(file) : null;
  }

  clearImage(): void {
    this.selectedFile = null;
    this.imageCleared = true;
    this.currentImage = null;
    if (this.previewUrl) {
      URL.revokeObjectURL(this.previewUrl);
      this.previewUrl = null;
    }
  }

  addLoot(): void {
    this.loot.push(this.fb.control(''));
  }

  removeLoot(index: number): void {
    this.loot.removeAt(index);
  }

  moveLoot(index: number, direction: -1 | 1): void {
    this.moveFormArrayItem(this.loot, index, direction);
  }

  addObject(): void {
    this.objects.push(this.createObjectGroup('', ''));
  }

  removeObject(index: number): void {
    this.objects.removeAt(index);
  }

  moveObject(index: number, direction: -1 | 1): void {
    this.moveFormArrayItem(this.objects, index, direction);
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

  submit(): void {
    if (this.form.invalid || this.saving || !this.campaignId) {
      this.form.markAllAsTouched();
      return;
    }

    const raw = this.form.getRawValue();
    const payload: LocationWritePayload = {
      title: raw.title?.trim() || '',
      description: raw.description?.trim() || '',
      loot: this.lootValues(),
      objects: this.objectValues(),
      npc_ids: [...this.selectedNpcIds],
    };

    this.saving = true;
    this.error = '';

    const request$ =
      this.editing && this.locationId
        ? this.api.updateLocation(
            this.locationId,
            payload,
            this.selectedFile,
            this.imageCleared && !this.selectedFile,
          )
        : this.api.createLocation(this.campaignId, payload, this.selectedFile);

    request$.subscribe({
      next: (location) => {
        this.router.navigate(['/campaigns', this.campaignId, 'locations', location.id]);
      },
      error: () => {
        this.error = 'Could not save location.';
        this.saving = false;
      },
    });
  }

  backLink(): (string | number)[] {
    if (this.campaignId) {
      return ['/campaigns', this.campaignId, 'locations'];
    }
    return ['/'];
  }

  private createObjectGroup(name: string, description: string): FormGroup {
    return this.fb.group({
      name: [name, Validators.required],
      description: [description],
    });
  }

  private setLoot(values: string[]): void {
    while (this.loot.length) {
      this.loot.removeAt(0);
    }
    values.forEach((value) => this.loot.push(this.fb.control(value)));
  }

  private setObjects(objects: LocationObject[]): void {
    while (this.objects.length) {
      this.objects.removeAt(0);
    }
    objects.forEach((obj) => {
      this.objects.push(this.createObjectGroup(obj.name, obj.description));
    });
  }

  private lootValues(): string[] {
    return this.loot.controls
      .map((control) => String(control.value || '').trim())
      .filter(Boolean);
  }

  private objectValues(): LocationWritePayload['objects'] {
    return this.objects.controls
      .map((group) => {
        const name = String(group.controls['name'].value || '').trim();
        const description = String(group.controls['description'].value || '').trim();
        return { name, description };
      })
      .filter((obj) => obj.name.length > 0);
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
