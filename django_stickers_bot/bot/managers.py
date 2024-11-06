from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    TrigramSimilarity,
)
from django.db.models import F, Manager


class StickerManager(Manager):
    def search(self, query):
        return (
            self.get_queryset()
            .annotate(
                similarity=TrigramSimilarity("text", query),
                rank=SearchRank(
                    "text_search_vector",
                    SearchQuery(query, config="russian"),
                ),
                combined_score=F("similarity") * 0.7 + F("rank") * 0.8,
            )
            .filter(similarity__gte=0.03)
            .order_by("-combined_score")[:3]
        )


__all__ = ["StickerManager"]
