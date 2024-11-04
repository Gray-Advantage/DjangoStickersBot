from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.contrib.postgres.indexes import GinIndex

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
        "Контекстная дата, в зависимости от состояния пользователя",
        max_length=100,
        default="",
    )


class StickerSet(models.Model):
    name = models.CharField("Имя стикер пака", max_length=1024)
    user = models.ForeignKey(
        TelegramUser,
        on_delete=models.deletion.CASCADE,
        related_name="sticker_sets",
        verbose_name="Пользователь, добавивший этот стикер пак",
    )


class Sticker(models.Model):
    objects = StickerManager()

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
    text_search_vector = SearchVectorField(null=True)

    class Meta:
        indexes = (
            GinIndex(fields=["text_search_vector"]),
        )

    def __str__(self):
        return self.text

    def __repr__(self):
        return f"<Sticker {self.text}>"


@receiver(post_save, sender=Sticker)
def update_search_vector(sender, instance, **kwargs):
    sender.objects.filter(pk=instance.pk).update(
        text_search_vector=SearchVector("text", config="russian")
    )


__all__ = ["TelegramUser", "Sticker", "StickerSet"]
