from django.db.models import Count
from rest_framework import mixins, parsers, status, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from .filters import NPCFilter
from .models import Campaign, NPC, Tag
from .serializers import (
    CampaignDetailSerializer,
    CampaignListSerializer,
    CampaignWriteSerializer,
    NPCDetailSerializer,
    NPCListSerializer,
    NPCWriteSerializer,
    TagSerializer,
)


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.annotate(npc_count=Count("npcs")).order_by("name")
    parser_classes = [parsers.JSONParser, parsers.FormParser, parsers.MultiPartParser]

    def get_serializer_class(self):
        if self.action == "list":
            return CampaignListSerializer
        if self.action in ("create", "update", "partial_update"):
            return CampaignWriteSerializer
        return CampaignDetailSerializer


class NPCViewSet(viewsets.ModelViewSet):
    queryset = NPC.objects.select_related("campaign").prefetch_related("aliases", "tags")
    filterset_class = NPCFilter
    filter_backends = viewsets.ModelViewSet.filter_backends + [OrderingFilter]
    ordering_fields = ["name", "updated_at", "created_at"]
    ordering = ["name"]

    def get_serializer_class(self):
        if self.action == "list":
            return NPCListSerializer
        if self.action in ("create", "update", "partial_update"):
            return NPCWriteSerializer
        return NPCDetailSerializer


class CampaignNPCViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    filterset_class = NPCFilter
    filter_backends = viewsets.GenericViewSet.filter_backends + [OrderingFilter]
    ordering_fields = ["name", "updated_at", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        return (
            NPC.objects.filter(campaign_id=self.kwargs["campaign_pk"])
            .select_related("campaign")
            .prefetch_related("aliases", "tags")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return NPCWriteSerializer
        return NPCListSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data["campaign"] = self.kwargs["campaign_pk"]
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class TagViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Tag.objects.order_by("name")
    serializer_class = TagSerializer
