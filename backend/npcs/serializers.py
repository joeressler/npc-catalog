from rest_framework import serializers

from .models import Alias, Campaign, NPC, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class AliasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alias
        fields = ["id", "name"]


class CampaignWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = ["id", "name", "image", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class CampaignListSerializer(serializers.ModelSerializer):
    npc_count = serializers.IntegerField(read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = ["id", "name", "image", "npc_count", "created_at", "updated_at"]

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url


class CampaignDetailSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = ["id", "name", "image", "created_at", "updated_at"]

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url


class NPCListSerializer(serializers.ModelSerializer):
    alignment_display = serializers.CharField(source="get_alignment_display", read_only=True)
    aliases = AliasSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = NPC
        fields = [
            "id",
            "campaign",
            "name",
            "role_occupation",
            "alignment",
            "alignment_display",
            "location",
            "faction",
            "attitude",
            "party_relationship",
            "aliases",
            "tags",
            "created_at",
            "updated_at",
        ]


class NPCDetailSerializer(serializers.ModelSerializer):
    alignment_display = serializers.CharField(source="get_alignment_display", read_only=True)
    aliases = AliasSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = NPC
        fields = [
            "id",
            "campaign",
            "name",
            "role_occupation",
            "alignment",
            "alignment_display",
            "location",
            "faction",
            "attitude",
            "party_relationship",
            "appearance",
            "voice_mannerisms",
            "personality_traits",
            "motivation_goal",
            "secret_hook",
            "knowledge",
            "inventory",
            "dm_notes",
            "session_log",
            "aliases",
            "tags",
            "created_at",
            "updated_at",
        ]


class NPCWriteSerializer(serializers.ModelSerializer):
    aliases = serializers.ListField(
        child=serializers.CharField(max_length=200),
        required=False,
        allow_empty=True,
        write_only=True,
    )
    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_empty=True,
        write_only=True,
    )

    class Meta:
        model = NPC
        fields = [
            "campaign",
            "name",
            "role_occupation",
            "alignment",
            "location",
            "faction",
            "attitude",
            "party_relationship",
            "appearance",
            "voice_mannerisms",
            "personality_traits",
            "motivation_goal",
            "secret_hook",
            "knowledge",
            "inventory",
            "dm_notes",
            "session_log",
            "aliases",
            "tags",
        ]

    def _sync_aliases(self, npc, alias_names):
        cleaned = []
        seen = set()
        for name in alias_names:
            trimmed = name.strip()
            if trimmed and trimmed.lower() not in seen:
                seen.add(trimmed.lower())
                cleaned.append(trimmed)

        npc.aliases.all().delete()
        Alias.objects.bulk_create([Alias(npc=npc, name=name) for name in cleaned])

    def _sync_tags(self, npc, tag_names):
        tag_objects = []
        for name in tag_names:
            trimmed = name.strip()
            if trimmed:
                tag, _ = Tag.objects.get_or_create(name=trimmed)
                tag_objects.append(tag)
        npc.tags.set(tag_objects)

    def create(self, validated_data):
        alias_names = validated_data.pop("aliases", [])
        tag_names = validated_data.pop("tags", [])
        npc = NPC.objects.create(**validated_data)
        self._sync_aliases(npc, alias_names)
        self._sync_tags(npc, tag_names)
        return npc

    def update(self, instance, validated_data):
        alias_names = validated_data.pop("aliases", None)
        tag_names = validated_data.pop("tags", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if alias_names is not None:
            self._sync_aliases(instance, alias_names)
        if tag_names is not None:
            self._sync_tags(instance, tag_names)

        return instance

    def to_representation(self, instance):
        return NPCDetailSerializer(instance, context=self.context).data
