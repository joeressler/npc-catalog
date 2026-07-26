from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CampaignNPCViewSet, CampaignViewSet, NPCViewSet, TagViewSet

router = DefaultRouter()
router.register("campaigns", CampaignViewSet, basename="campaign")
router.register("npcs", NPCViewSet, basename="npc")
router.register("tags", TagViewSet, basename="tag")

campaign_npc_list = CampaignNPCViewSet.as_view({"get": "list", "post": "create"})

urlpatterns = [
    path("campaigns/<int:campaign_pk>/npcs/", campaign_npc_list, name="campaign-npc-list"),
    path("", include(router.urls)),
]
