__all__ = ("add_stickers", "connect_user", "show_sticker")

import logging

from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from aiogram.types import Sticker as TgSticker
from aiogram.utils.formatting import Pre, Text

from bot.bot import keyboards
from bot.bot.ocr import recognize_stickers
from bot.bot.ocr_text import EMPTY_TEXT
from bot.models import Sticker, StickerSet, TelegramUser

logger = logging.getLogger(__name__)


async def connect_user(event: CallbackQuery | Message) -> TelegramUser:
    tg_user = event.from_user
    if tg_user is None:
        message = "Событие пришло без пользователя"
        raise ValueError(message)

    user, _ = await TelegramUser.objects.aget_or_create(
        telegram_id=tg_user.id,
        defaults={"telegram_id": tg_user.id},
    )
    return user


async def add_stickers(
    bot: Bot,
    tg_stickers: list[TgSticker],
    db_sticker_set: StickerSet,
) -> tuple[dict[str, str], int]:
    images: dict[str, bytes] = {}
    known: dict[str, TgSticker] = {}
    skipped = 0

    for tg_sticker in tg_stickers:
        if tg_sticker.is_video or tg_sticker.is_animated:
            skipped += 1
            continue

        content = await bot.download(tg_sticker.file_id)
        if content is None:
            skipped += 1
            logger.warning("Не удалось скачать стикер %s", tg_sticker.file_id)
            continue

        name = f"{tg_sticker.file_unique_id}.webp"
        images[name] = content.read()
        known[name] = tg_sticker

    texts = await recognize_stickers(images)

    saved: dict[str, str] = {}
    for name, tg_sticker in known.items():
        text = texts.get(name) or EMPTY_TEXT
        await Sticker.objects.acreate(
            file_id=tg_sticker.file_id,
            file_unique_id=tg_sticker.file_unique_id,
            text=text,
            sticker_set=db_sticker_set,
        )
        saved[tg_sticker.file_unique_id] = text

    return saved, skipped


async def show_sticker(
    bot: Bot,
    chat_id: int,
    tg_sticker: TgSticker,
    text: str | None = None,
    pretext: str = "",
) -> None:
    sticker_message = await bot.send_sticker(chat_id, tg_sticker.file_id)

    if text is None:
        sticker = await Sticker.objects.filter(
            file_unique_id=tg_sticker.file_unique_id,
        ).afirst()
        text = sticker.text if sticker is not None else EMPTY_TEXT

    caption = Text(pretext, "\n", Pre(text))
    await sticker_message.reply(
        **caption.as_kwargs(),
        reply_markup=keyboards.edit_sticker_text(tg_sticker.file_unique_id),
    )
