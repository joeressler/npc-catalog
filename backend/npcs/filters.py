from django.db.models import Q
from django_filters import rest_framework as filters

from .models import NPC


class NPCFilter(filters.FilterSet):
    q = filters.CharFilter(method="filter_search")
    tag = filters.CharFilter(field_name="tags__name", lookup_expr="iexact")
    campaign = filters.NumberFilter(field_name="campaign_id")
    location = filters.CharFilter(field_name="location", lookup_expr="icontains")
    faction = filters.CharFilter(field_name="faction", lookup_expr="icontains")

    class Meta:
        model = NPC
        fields = ["alignment", "location", "faction", "campaign", "tag"]

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(role_occupation__icontains=value)
            | Q(aliases__name__icontains=value)
            | Q(tags__name__icontains=value)
        ).distinct()
