__all__ = ("Sticker", "StickerSet", "TelegramUser")

from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.db import models

from bot.managers import StickerManager


class TelegramUser(models.Model):
    telegram_id = models.PositiveBigIntegerField("ИД в телеграмме")
    is_admin = models.BooleanField("Администратор ли это", default=False)

    class UserStates(models.IntegerChoices):
        IDLE = 0
        EDIT_STICKER_TEXT = 1

    state = models.IntegerField(
        "Состояние пользователя",
        choices=UserStates.choices,
        default=UserStates.IDLE,
    )

    context_data = models.CharField(
        "Контекстные данные, в зависимости от состояния пользователя",
        max_length=100,
        default="",
    )

    def __str__(self) -> str:
        return str(self.telegram_id)


class StickerSet(models.Model):
    name = models.CharField("Имя стикер пака", max_length=1024, unique=True)
    user = models.ForeignKey(
        TelegramUser,
        on_delete=models.deletion.PROTECT,
        related_name="sticker_sets",
        verbose_name="Пользователь, добавивший этот стикер пак",
    )

    class Meta:
        ordering = ("id",)

    def __str__(self) -> str:
        return self.name


class Sticker(models.Model):
    file_id = models.CharField(
        "ИД файла для скачивания",
        max_length=100,
        unique=True,
    )
    file_unique_id = models.CharField(
        "ИД стикера для редактирования",
        max_length=64,
        unique=True,
    )
    sticker_set = models.ForeignKey(
        StickerSet,
        on_delete=models.CASCADE,
        related_name="stickers",
        verbose_name="Стикер пак, которому принадлежит этот стикер",
    )

    text = models.TextField("Текстовое содержимое стикера")
    text_search_vector = models.GeneratedField(
        expression=SearchVector("text", config="russian"),
        output_field=SearchVectorField(),
        db_persist=True,
        null=True,
    )

    objects = StickerManager()

    class Meta:
        ordering = ("id",)
        indexes = (
            GinIndex(
                name="sticker_text_vector_gin",
                fields=["text_search_vector"],
            ),
            GinIndex(
                name="sticker_text_trigram",
                fields=["text"],
                opclasses=["gin_trgm_ops"],
            ),
        )

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f"<Sticker {self.text}>"
