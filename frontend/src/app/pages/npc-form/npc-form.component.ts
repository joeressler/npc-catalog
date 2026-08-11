import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { ApiService } from '../../services/api.service';
import { ALIGNMENTS, AlignmentCode, LocationSummary, NPC, NPCWritePayload } from '../../models/domain.models';
import { MarkdownFieldComponent } from '../../shared/markdown-field.component';
import { AiImageGenerateComponent } from '../../shared/ai-image-generate/ai-image-generate.component';

@Component({
  selector: 'app-npc-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, MarkdownFieldComponent, AiImageGenerateComponent],
  templateUrl: './npc-form.component.html',
  styleUrl: './npc-form.component.scss',
})
export class NpcFormComponent implements OnInit, OnDestroy {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  editing = false;
  npcId: number | null = null;
  campaignId: number | null = null;
  saving = false;
  error = '';
  dossierOpen = false;
  alignments = ALIGNMENTS;
  campaignLocations: LocationSummary[] = [];
  currentImage: string | null = null;
  selectedFile: File | null = null;
  previewUrl: string | null = null;
  imageCleared = false;

  form = this.fb.group({
    name: ['', Validators.required],
    aliases: [''],
    role_occupation: ['', Validators.required],
    alignment: ['N' as AlignmentCode, Validators.required],
    location: [''],
    location_id: [''],
    faction: [''],
    attitude: ['', Validators.required],
    party_relationship: ['', Validators.required],
    tags: [''],
    appearance: [''],
    voice_mannerisms: [''],
    personality_traits: [''],
    motivation_goal: [''],
    secret_hook: [''],
    knowledge: [''],
    inventory: [''],
    dm_notes: [''],
    session_log: [''],
    player_visible: [false],
  });

  ngOnInit(): void {
    const npcIdParam = this.route.snapshot.paramMap.get('npcId');
    const campaignIdParam = this.route.snapshot.paramMap.get('campaignId');

    if (npcIdParam) {
      this.editing = true;
      this.npcId = Number(npcIdParam);
      this.api.getNpc(this.npcId).subscribe({
        next: (npc) => {
          this.patchNpcForm(npc);
        },
        error: () => {
          this.error = 'NPC not found.';
        },
      });
    } else if (campaignIdParam) {
      this.campaignId = Number(campaignIdParam);
      this.loadCampaignLocations(this.campaignId);
    }
  }

  private loadCampaignLocations(campaignId: number): void {
    this.api.getCampaignLocations(campaignId).subscribe({
      next: (response) => {
        this.campaignLocations = response.results;
      },
    });
  }

  private patchNpcForm(npc: NPC): void {
    this.campaignId = npc.campaign;
    this.loadCampaignLocations(npc.campaign);
    this.currentImage = this.api.mediaUrl(npc.image);
    this.form.patchValue({
      name: npc.name,
      aliases: npc.aliases.map((a) => a.name).join(', '),
      role_occupation: npc.role_occupation,
      alignment: npc.alignment,
      location: npc.location,
      location_id: npc.catalog_location ? String(npc.catalog_location.id) : '',
      faction: npc.faction,
      attitude: npc.attitude,
      party_relationship: npc.party_relationship,
      tags: npc.tags.map((t) => t.name).join(', '),
      appearance: npc.appearance,
      voice_mannerisms: npc.voice_mannerisms,
      personality_traits: npc.personality_traits,
      motivation_goal: npc.motivation_goal,
      secret_hook: npc.secret_hook,
      knowledge: npc.knowledge,
      inventory: npc.inventory,
      dm_notes: npc.dm_notes,
      session_log: npc.session_log,
      player_visible: !!npc.player_visible,
    });
    this.dossierOpen = this.hasDossierContent();
  }

  ngOnDestroy(): void {
    if (this.previewUrl) {
      URL.revokeObjectURL(this.previewUrl);
    }
  }

  toggleDossier(): void {
    this.dossierOpen = !this.dossierOpen;
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

  /** Fields snapshot for ComfyUI prompt building (current form values). */
  aiPromptFields(): Record<string, unknown> {
    const raw = this.form.getRawValue();
    return {
      name: raw.name,
      aliases: this.splitList(raw.aliases),
      role_occupation: raw.role_occupation,
      alignment: raw.alignment,
      location: raw.location,
      faction: raw.faction,
      attitude: raw.attitude,
      party_relationship: raw.party_relationship,
      tags: this.splitList(raw.tags),
      appearance: raw.appearance,
      voice_mannerisms: raw.voice_mannerisms,
      personality_traits: raw.personality_traits,
      motivation_goal: raw.motivation_goal,
      secret_hook: raw.secret_hook,
      knowledge: raw.knowledge,
      inventory: raw.inventory,
    };
  }

  onAiImageChosen(file: File): void {
    this.selectedFile = file;
    this.imageCleared = false;
    if (this.previewUrl) {
      URL.revokeObjectURL(this.previewUrl);
    }
    this.previewUrl = URL.createObjectURL(file);
  }

  submit(): void {
    if (this.form.invalid || this.saving) {
      this.form.markAllAsTouched();
      return;
    }

    const raw = this.form.getRawValue();
    const locationIdRaw = raw.location_id?.trim();
    const payload: NPCWritePayload = {
      name: raw.name!.trim(),
      role_occupation: raw.role_occupation!.trim(),
      alignment: raw.alignment as AlignmentCode,
      location: raw.location?.trim() || '',
      location_id: locationIdRaw ? Number(locationIdRaw) : null,
      faction: raw.faction?.trim() || '',
      attitude: raw.attitude!.trim(),
      party_relationship: raw.party_relationship!.trim(),
      appearance: raw.appearance?.trim() || '',
      voice_mannerisms: raw.voice_mannerisms?.trim() || '',
      personality_traits: raw.personality_traits?.trim() || '',
      motivation_goal: raw.motivation_goal?.trim() || '',
      secret_hook: raw.secret_hook?.trim() || '',
      knowledge: raw.knowledge?.trim() || '',
      inventory: raw.inventory?.trim() || '',
      dm_notes: raw.dm_notes?.trim() || '',
      session_log: raw.session_log?.trim() || '',
      player_visible: !!raw.player_visible,
      aliases: this.splitList(raw.aliases),
      tags: this.splitList(raw.tags),
    };

    this.saving = true;
    this.error = '';

    const request$ =
      this.editing && this.npcId
        ? this.api.updateNpc(
            this.npcId,
            payload,
            this.selectedFile,
            this.imageCleared && !this.selectedFile,
          )
        : this.api.createNpc(this.campaignId!, payload, this.selectedFile);

    request$.subscribe({
      next: (npc) => {
        this.router.navigate(['/npcs', npc.id]);
      },
      error: () => {
        this.error = 'Could not save NPC.';
        this.saving = false;
      },
    });
  }

  backLink(): (string | number)[] {
    if (this.editing && this.campaignId) {
      return ['/campaigns', this.campaignId];
    }
    if (this.campaignId) {
      return ['/campaigns', this.campaignId];
    }
    return ['/'];
  }

  private splitList(value: string | null | undefined): string[] {
    if (!value) {
      return [];
    }
    return value
      .split(',')
      .map((part) => part.trim())
      .filter(Boolean);
  }

  private hasDossierContent(): boolean {
    const raw = this.form.getRawValue();
    return Boolean(
      raw.appearance ||
        raw.voice_mannerisms ||
        raw.personality_traits ||
        raw.motivation_goal ||
        raw.secret_hook ||
        raw.knowledge ||
        raw.inventory ||
        raw.dm_notes ||
        raw.session_log,
    );
  }
}
