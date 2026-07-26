from django.contrib import admin

from .models import Alias, Campaign, NPC, Tag


class AliasInline(admin.TabularInline):
    model = Alias
    extra = 1


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(NPC)
class NPCAdmin(admin.ModelAdmin):
    list_display = ("name", "campaign", "alignment", "location", "updated_at")
    list_filter = ("campaign", "alignment", "location", "faction")
    search_fields = ("name", "role_occupation", "aliases__name", "tags__name")
    filter_horizontal = ("tags",)
    inlines = [AliasInline]
