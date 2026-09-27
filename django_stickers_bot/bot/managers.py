__all__ = ("StickerManager",)

from typing import TYPE_CHECKING

from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    TrigramWordSimilarity,
)
from django.db.models import F, Manager, Q, QuerySet

if TYPE_CHECKING:
    from bot.models import Sticker

# Полнотекстовый поиск ловит слово в любой форме, но пасует перед опечаткой.
# Триграммное сходство слова, наоборот, вытягивает «дедлан» к «дедлайну».
# Достаточно любого из двух совпадений, поэтому условия соединены через «или».
#
# Отбор идёт операторами (`@@` и `%>`), а не сравнением результата функций:
# только операторы умеют пользоваться индексами sticker_text_vector_gin и
# sticker_text_trigram. Сравнение вида `word_similarity(...) >= 0.6` дало бы
# тот же ответ, но всегда полным проходом по таблице.
#
# Порог для `%>` задаётся настройкой базы pg_trgm.word_similarity_threshold,
# по умолчанию это 0.6. Функции ниже нужны только для сортировки по
# релевантности.
SIMILARITY_WEIGHT = 0.6


class StickerManager(Manager["Sticker"]):
    def search(self, query: str) -> QuerySet["Sticker"]:
        search_query = SearchQuery(query, config="russian")

        return (
            self.get_queryset()
            .annotate(
                quality=SearchRank("text_search_vector", search_query),
                similarity=TrigramWordSimilarity(query, "text"),
                rank=F("quality") + F("similarity") * SIMILARITY_WEIGHT,
            )
            .filter(
                Q(text_search_vector=search_query)
                | Q(text__trigram_word_similar=query),
            )
            .order_by("-rank")
        )
