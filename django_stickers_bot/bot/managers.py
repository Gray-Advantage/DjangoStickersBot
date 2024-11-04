from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db import models


class StickerManager(models.Manager):
    def search(self, query):
        return (
            self.get_queryset()
            .annotate(
                rank=SearchRank(
                    "text_search_vector",
                    SearchQuery(query, config="russian"),
                ),
            )
            .order_by("-rank")[:5]
        )


__all__ = ["StickerManager"]
