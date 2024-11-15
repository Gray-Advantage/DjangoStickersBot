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
                quality=SearchRank(
                    "text_search_vector",
                    SearchQuery(query, config="russian"),
                ),
                similarity=TrigramSimilarity("text", query),
                rank=F("quality") + F("similarity") * 0.6,
            )
            .filter(quality__gte=0.01, similarity__gte=0.01)
            .order_by("-rank")
        )


__all__ = ["StickerManager"]
