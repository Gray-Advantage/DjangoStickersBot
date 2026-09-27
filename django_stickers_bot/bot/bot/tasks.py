__all__ = ("check_stickers_updates", "including_sticker_set", "sync_loop")

import asyncio
import logging

from aiogram import Bot
from aiogram.types import Message
from aiogram.types import Sticker as TgSticker

from bot.bot import keyboards
from bot.bot.ocr_text import EMPTY_TEXT
from bot.bot.utils import add_stickers, show_sticker
from bot.models import Sticker, StickerSet, TelegramUser

logger = logging.getLogger(__name__)

SYNC_INTERVAL = 3600
NEW_STICKERS_IN_DETAIL = 5


async def including_sticker_set(
    bot: Bot,
    progress: Message,
    db_sticker_set: StickerSet,
    tg_stickers: list[TgSticker],
) -> None:
    await progress.edit_text(
        f"Скачиваю и распознаю набор: стикеров {len(tg_stickers)}",
    )

    texts, skipped = await add_stickers(bot, tg_stickers, db_sticker_set)

    empty = sum(1 for text in texts.values() if text == EMPTY_TEXT)
    lines = [f"Набор добавлен, стикеров: {len(texts)}"]
    if empty:
        lines.append(f"без распознанного текста: {empty}")

    if skipped:
        lines.append(f"пропущено видео и анимаций: {skipped}")

    await progress.edit_text(
        "\n".join(lines),
        reply_markup=keyboards.open_sticker_set(db_sticker_set.pk),
    )


async def check_stickers_updates(bot: Bot) -> None:
    async for db_sticker_set in StickerSet.objects.all():
        tg_sticker_set = await bot.get_sticker_set(db_sticker_set.name)
        tg_stickers = {
            sticker.file_unique_id: sticker
            for sticker in tg_sticker_set.stickers
        }
        known_ids = {
            file_unique_id
            async for file_unique_id in Sticker.objects.filter(
                sticker_set=db_sticker_set,
            ).values_list("file_unique_id", flat=True)
        }

        await _remove_deleted(bot, db_sticker_set, tg_stickers, known_ids)
        await _refresh_file_ids(db_sticker_set, tg_stickers)
        await _add_new(bot, db_sticker_set, tg_stickers, known_ids)


async def sync_loop(bot: Bot) -> None:
    failing = False
    while True:
        await asyncio.sleep(SYNC_INTERVAL)
        try:
            await check_stickers_updates(bot)
        except Exception as error:
            logger.exception("Сверка наборов не удалась")
            if not failing:
                failing = True
                await notify_admins(bot, f"Сверка наборов падает: {error}")
        else:
            if failing:
                failing = False
                await notify_admins(bot, "Сверка наборов снова работает")


async def notify_admins(bot: Bot, text: str) -> None:
    try:
        async for admin in TelegramUser.objects.filter(is_admin=True):
            await bot.send_message(admin.telegram_id, text)
    except Exception:
        logger.exception("Не удалось предупредить админов")


async def _remove_deleted(
    bot: Bot,
    db_sticker_set: StickerSet,
    tg_stickers: dict[str, TgSticker],
    known_ids: set[str],
) -> None:
    deleted_ids = known_ids - set(tg_stickers)
    if not deleted_ids:
        return

    await Sticker.objects.filter(
        sticker_set=db_sticker_set,
        file_unique_id__in=deleted_ids,
    ).adelete()

    left_sticker = next(iter(tg_stickers.values()), None)
    text = f"Из набора {db_sticker_set.name} удалены стикеры"
    async for admin in TelegramUser.objects.filter(is_admin=True):
        if left_sticker is None:
            await bot.send_message(admin.telegram_id, text)
            continue

        message = await bot.send_sticker(
            admin.telegram_id,
            left_sticker.file_id,
        )
        await message.reply(text)


async def _refresh_file_ids(
    db_sticker_set: StickerSet,
    tg_stickers: dict[str, TgSticker],
) -> None:
    async for sticker in Sticker.objects.filter(sticker_set=db_sticker_set):
        tg_sticker = tg_stickers.get(sticker.file_unique_id)
        if tg_sticker is not None and tg_sticker.file_id != sticker.file_id:
            sticker.file_id = tg_sticker.file_id
            await sticker.asave(update_fields=["file_id"])


async def _add_new(
    bot: Bot,
    db_sticker_set: StickerSet,
    tg_stickers: dict[str, TgSticker],
    known_ids: set[str],
) -> None:
    new_stickers = [
        tg_stickers[file_unique_id]
        for file_unique_id in set(tg_stickers) - known_ids
    ]
    if not new_stickers:
        return

    texts, _ = await add_stickers(bot, new_stickers, db_sticker_set)

    if len(texts) > NEW_STICKERS_IN_DETAIL:
        summary = (
            f"В набор {db_sticker_set.name} добавились стикеры: {len(texts)}"
        )
        async for admin in TelegramUser.objects.filter(is_admin=True):
            await bot.send_message(
                admin.telegram_id,
                summary,
                reply_markup=keyboards.open_sticker_set(db_sticker_set.pk),
            )

        return

    async for admin in TelegramUser.objects.filter(is_admin=True):
        for tg_sticker in new_stickers:
            text = texts.get(tg_sticker.file_unique_id)
            if text is None:
                continue

            await show_sticker(
                bot,
                admin.telegram_id,
                tg_sticker,
                text,
                "В набор был автоматически добавлен новый стикер",
            )
