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
import {
  EncounterEnemy,
  EncounterObject,
  EncounterWritePayload,
  NPC,
} from '../../models/npc.models';

@Component({
  selector: 'app-encounter-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './encounter-form.component.html',
  styleUrl: './encounter-form.component.scss',
})
export class EncounterFormComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  editing = false;
  encounterId: number | null = null;
  campaignId: number | null = null;
  campaignNpcs: NPC[] = [];
  selectedCharacterIds = new Set<number>();
  saving = false;
  error = '';

  form = this.fb.group({
    title: ['', Validators.required],
    short_description: [''],
    battlefield_description: [''],
    further_notes: [''],
    enemies: this.fb.array<FormGroup>([]),
    loot: this.fb.array<string>([]),
    objects: this.fb.array<FormGroup>([]),
  });

  ngOnInit(): void {
    const encounterIdParam = this.route.snapshot.paramMap.get('encounterId');
    const campaignIdParam = this.route.snapshot.paramMap.get('campaignId');
    this.campaignId = Number(campaignIdParam);

    this.api.getCampaignNpcs(this.campaignId).subscribe({
      next: (response) => {
        this.campaignNpcs = response.results;
      },
    });

    if (encounterIdParam && encounterIdParam !== 'new') {
      this.editing = true;
      this.encounterId = Number(encounterIdParam);

      this.api.getEncounter(this.encounterId).subscribe({
        next: (encounter) => {
          this.campaignId = encounter.campaign;
          this.form.patchValue({
            title: encounter.title,
            short_description: encounter.short_description,
            battlefield_description: encounter.battlefield_description,
            further_notes: encounter.further_notes,
          });
          this.setEnemies(encounter.enemies);
          this.setLoot(encounter.loot.map((item) => item.description));
          this.setObjects(encounter.objects);
          this.selectedCharacterIds = new Set(encounter.characters.map((character) => character.id));
        },
        error: () => {
          this.error = 'Encounter not found.';
        },
      });
    }
  }

  get enemies(): FormArray<FormGroup> {
    return this.form.controls.enemies;
  }

  get loot(): FormArray {
    return this.form.controls.loot;
  }

  get objects(): FormArray<FormGroup> {
    return this.form.controls.objects;
  }

  addEnemy(): void {
    this.enemies.push(this.createEnemyGroup(1, '', ''));
  }

  removeEnemy(index: number): void {
    this.enemies.removeAt(index);
  }

  moveEnemy(index: number, direction: -1 | 1): void {
    this.moveFormArrayItem(this.enemies, index, direction);
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
    const payload: EncounterWritePayload = {
      title: raw.title?.trim() || '',
      short_description: raw.short_description?.trim() || '',
      battlefield_description: raw.battlefield_description?.trim() || '',
      further_notes: raw.further_notes?.trim() || '',
      enemies: this.enemyValues(),
      loot: this.lootValues(),
      objects: this.objectValues(),
      character_ids: [...this.selectedCharacterIds],
    };

    this.saving = true;
    this.error = '';

    const request$ =
      this.editing && this.encounterId
        ? this.api.updateEncounter(this.encounterId, payload)
        : this.api.createEncounter(this.campaignId, payload);

    request$.subscribe({
      next: (encounter) => {
        this.router.navigate(['/campaigns', this.campaignId, 'encounters', encounter.id]);
      },
      error: () => {
        this.error = 'Could not save encounter.';
        this.saving = false;
      },
    });
  }

  backLink(): (string | number)[] {
    if (this.campaignId) {
      return ['/campaigns', this.campaignId, 'encounters'];
    }
    return ['/'];
  }

  private createEnemyGroup(quantity: number, name: string, creatureType: string): FormGroup {
    return this.fb.group({
      quantity: [quantity, [Validators.required, Validators.min(1)]],
      name: [name, Validators.required],
      creature_type: [creatureType],
    });
  }

  private createObjectGroup(name: string, description: string): FormGroup {
    return this.fb.group({
      name: [name, Validators.required],
      description: [description],
    });
  }

  private setEnemies(enemies: EncounterEnemy[]): void {
    while (this.enemies.length) {
      this.enemies.removeAt(0);
    }
    enemies.forEach((enemy) => {
      this.enemies.push(this.createEnemyGroup(enemy.quantity, enemy.name, enemy.creature_type));
    });
  }

  private setLoot(values: string[]): void {
    while (this.loot.length) {
      this.loot.removeAt(0);
    }
    values.forEach((value) => this.loot.push(this.fb.control(value)));
  }

  private setObjects(objects: EncounterObject[]): void {
    while (this.objects.length) {
      this.objects.removeAt(0);
    }
    objects.forEach((obj) => {
      this.objects.push(this.createObjectGroup(obj.name, obj.description));
    });
  }

  private enemyValues(): EncounterWritePayload['enemies'] {
    return this.enemies.controls
      .map((group) => {
        const name = String(group.controls['name'].value || '').trim();
        const creatureType = String(group.controls['creature_type'].value || '').trim();
        const quantity = Number(group.controls['quantity'].value) || 1;
        return { quantity, name, creature_type: creatureType };
      })
      .filter((enemy) => enemy.name.length > 0);
  }

  private lootValues(): string[] {
    return this.loot.controls
      .map((control) => String(control.value || '').trim())
      .filter(Boolean);
  }

  private objectValues(): EncounterWritePayload['objects'] {
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
