__all__ = ("build_dispatcher", "router")

import asyncio
from collections.abc import Coroutine
import logging
from typing import Any

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineQuery,
    InlineQueryResultCachedSticker,
    InlineQueryResultUnion,
    Message,
)
from aiogram.utils.formatting import Pre, Text

from bot.bot import filters, keyboards, tasks, utils
from bot.bot.callbacks import (
    AddSetCallback,
    SetAction,
    SetCallback,
    StickerAction,
    StickerCallback,
)
from bot.models import Sticker, StickerSet, TelegramUser

logger = logging.getLogger(__name__)

INLINE_PAGE_SIZE = 50
INLINE_CACHE_TIME = 30

# Telegram пускает в один чат примерно одно сообщение в секунду, поэтому в
# личку отдаём только самые подходящие стикеры, а за остальными — в инлайн
SEARCH_RESULTS_LIMIT = 8
# Набор бывает и на 120 стикеров, поэтому показываем его страницами
SET_PAGE_SIZE = 5

router = Router(name="stickers")

# Ссылки на фоновые задачи: без них сборщик мусора может убить задачу на лету
_background_tasks: set[asyncio.Task[None]] = set()


def background(coro: Coroutine[Any, Any, None]) -> None:
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


def build_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    return dispatcher


@router.message(CommandStart())
async def start(message: Message) -> None:
    user = await utils.connect_user(message)

    extra_text = ""
    if user.is_admin:
        extra_text = (
            "\n\nА ещё ты админ! Можешь мне прислать доп. стикеры и я буду "
            "искать ещё и среди них при следующих запросах пользователей"
        )

    await message.answer(
        "Привет, я бот, который поможет найти тебе тот самый стикер с "
        "специализации Django\n"
        "\n"
        "Достаточно написать отрывок текста, а я попробую найти подходящий"
        f"{extra_text}",
    )

    if user.state != user.UserStates.IDLE or user.context_data != "":
        user.state = user.UserStates.IDLE
        user.context_data = ""
        await user.asave()
        await message.answer("Кстати, я ещё сделал сброс твоего состояния")


@router.message(Command("all"))
async def all_sticker_sets(message: Message) -> None:
    async for sticker_set in StickerSet.objects.all():
        first_sticker = await sticker_set.stickers.afirst()
        if first_sticker is None:
            continue

        await message.answer_sticker(first_sticker.file_id)


@router.message(F.text)
async def on_text(message: Message, bot: Bot) -> None:
    user = await utils.connect_user(message)
    if user.state == user.UserStates.EDIT_STICKER_TEXT and user.is_admin:
        await edit_sticker_text(message, user)
        return

    if user.state != user.UserStates.IDLE:
        user.state = user.UserStates.IDLE
        user.context_data = ""
        await user.asave()

    await search(message, bot)


@router.message(F.sticker, filters.Admin())
async def on_admin_sticker(message: Message, bot: Bot) -> None:
    await process_sticker(message, bot)


@router.message(F.sticker)
async def on_foreign_sticker(message: Message) -> None:
    await message.delete()


@router.message()
async def on_other_content(message: Message) -> None:
    await message.delete()


async def search(message: Message, bot: Bot) -> None:
    if message.text is None:
        return

    searching = await message.answer("Происходит поиск...")

    # Берём на один больше предела, чтобы понять, есть ли что-то ещё
    page = Sticker.objects.search(message.text)[: SEARCH_RESULTS_LIMIT + 1]
    found = [sticker async for sticker in page]

    for sticker in found[:SEARCH_RESULTS_LIMIT]:
        await message.answer_sticker(sticker.file_id)

    if not found:
        await message.answer("К сожалению, ничего не найдено")
    elif len(found) > SEARCH_RESULTS_LIMIT:
        me = await bot.me()
        await message.answer(
            f"Показал {SEARCH_RESULTS_LIMIT} самых подходящих. Если нужного "
            f"нет, уточните запрос или листайте все через инлайн: "
            f"@{me.username} {message.text}",
        )

    await searching.delete()


async def edit_sticker_text(message: Message, user: TelegramUser) -> None:
    if message.text is None:
        return

    sticker = await Sticker.objects.filter(
        file_unique_id=user.context_data,
    ).afirst()
    if sticker is None:
        await message.answer("Этого стикера у меня больше нет")
    else:
        sticker.text = message.text
        await sticker.asave()
        await message.answer("Текст стикера обновлен!")

    user.context_data = ""
    user.state = user.UserStates.IDLE
    await user.asave()


async def process_sticker(message: Message, bot: Bot) -> None:
    sticker = message.sticker
    if sticker is None:
        return

    if sticker.set_name is None:
        await message.answer(
            "Сорри, принимаю стикеры только из наборов, одиночные не подойдут",
        )
        return

    tg_sticker_set = await bot.get_sticker_set(sticker.set_name)
    db_sticker_set = await StickerSet.objects.filter(
        name=tg_sticker_set.name,
    ).afirst()

    if db_sticker_set is not None:
        await message.reply(
            "Этот стикер пак у меня уже есть",
            reply_markup=keyboards.see_sticker_set(
                db_sticker_set.pk,
                sticker.file_unique_id,
            ),
        )
        return

    await message.reply(
        "О, такого стикер пака у меня нет, начать процесс добавления?",
        reply_markup=keyboards.add_sticker_set(),
    )


@router.callback_query(AddSetCallback.filter(), filters.Admin())
async def add_sticker_set(
    call: CallbackQuery,
    bot: Bot,
    user: TelegramUser,
) -> None:
    await call.answer()
    if not isinstance(call.message, Message):
        return

    # Имя набора берём из стикера, на который отвечает сообщение с кнопкой:
    # в callback_data оно бы не влезло в отведённые Telegram 64 байта
    source = call.message.reply_to_message
    sticker = source.sticker if source is not None else None
    if sticker is None or sticker.set_name is None:
        await call.message.answer(
            "Не вижу, какой набор добавлять — пришлите стикер ещё раз",
        )
        return

    await call.message.edit_reply_markup(reply_markup=None)

    tg_sticker_set = await bot.get_sticker_set(sticker.set_name)
    # get_or_create, а не create: имя набора уникально, и два админа могли
    # нажать «Да» одновременно
    db_sticker_set, created = await StickerSet.objects.aget_or_create(
        name=tg_sticker_set.name,
        defaults={"user": user},
    )
    if not created:
        await call.message.answer(
            "Этот набор уже добавляется или добавлен",
            reply_markup=keyboards.open_sticker_set(db_sticker_set.pk),
        )
        return

    # Добавление набора долгое (скачивание и распознавание), поэтому уходит в
    # отдельную задачу и не блокирует остальные обновления
    background(
        tasks.including_sticker_set(
            bot,
            call.message,
            db_sticker_set,
            list(tg_sticker_set.stickers),
        ),
    )


@router.callback_query(
    StickerCallback.filter(F.action == StickerAction.EDIT),
    filters.Admin(),
)
async def ask_new_text(
    call: CallbackQuery,
    callback_data: StickerCallback,
    user: TelegramUser,
) -> None:
    await call.answer()
    if not isinstance(call.message, Message):
        return

    user.state = user.UserStates.EDIT_STICKER_TEXT
    user.context_data = callback_data.file_unique_id
    await user.asave()

    await call.message.reply("Ожидаю новый текст для этого стикера")


@router.callback_query(
    SetCallback.filter(F.action == SetAction.SHOW),
    filters.Admin(),
)
async def see_sticker_set(
    call: CallbackQuery,
    callback_data: SetCallback,
    bot: Bot,
) -> None:
    await call.answer()
    if not isinstance(call.message, Message):
        return

    stickers = Sticker.objects.filter(sticker_set_id=callback_data.set_id)
    total = await stickers.acount()
    if total == 0:
        await call.message.answer("В этом наборе стикеров не осталось")
        return

    offset = callback_data.offset
    end = offset + SET_PAGE_SIZE
    num = offset
    async for sticker in stickers[offset:end]:
        num += 1
        sticker_message = await bot.send_sticker(
            call.message.chat.id,
            sticker.file_id,
        )
        caption = Text(f"Стикер {num}/{total}:", "\n", Pre(sticker.text))
        await sticker_message.reply(
            **caption.as_kwargs(),
            reply_markup=keyboards.edit_sticker_text(sticker.file_unique_id),
        )

    if num < total:
        await call.message.answer(
            f"Показано {num} из {total}",
            reply_markup=keyboards.more_stickers(callback_data.set_id, num),
        )


@router.callback_query(
    StickerCallback.filter(F.action == StickerAction.SHOW),
    filters.Admin(),
)
async def see_sticker(
    call: CallbackQuery,
    callback_data: StickerCallback,
) -> None:
    await call.answer()
    if not isinstance(call.message, Message):
        return

    sticker = await Sticker.objects.filter(
        file_unique_id=callback_data.file_unique_id,
    ).afirst()
    if sticker is None:
        await call.message.answer("Этого стикера у меня больше нет")
        return

    sticker_message = await call.message.answer_sticker(sticker.file_id)
    caption = Text(Pre(sticker.text))
    await sticker_message.reply(
        **caption.as_kwargs(),
        reply_markup=keyboards.edit_sticker_text(sticker.file_unique_id),
    )


@router.callback_query(
    SetCallback.filter(F.action == SetAction.DELETE),
    filters.Admin(),
)
async def delete_sticker_set(
    call: CallbackQuery,
    callback_data: SetCallback,
) -> None:
    await call.answer()
    if not isinstance(call.message, Message):
        return

    await StickerSet.objects.filter(pk=callback_data.set_id).adelete()
    await call.message.edit_text("Стикер пак удалён")


# Регистрируется последним: сюда попадают кнопки, не прошедшие проверку прав
@router.callback_query()
async def denied_callback(call: CallbackQuery) -> None:
    await call.answer("Эти кнопки только для админов", show_alert=True)


@router.inline_query()
async def inline_search(query: InlineQuery) -> None:
    if not query.query:
        await query.answer(results=[], cache_time=INLINE_CACHE_TIME)
        return

    offset = int(query.offset) if query.offset.isdigit() else 0
    end = offset + INLINE_PAGE_SIZE
    page = Sticker.objects.search(query.query)[offset:end]

    results: list[InlineQueryResultUnion] = [
        InlineQueryResultCachedSticker(
            id=sticker.file_unique_id,
            sticker_file_id=sticker.file_id,
        )
        async for sticker in page
    ]
    next_offset = ""
    if len(results) == INLINE_PAGE_SIZE:
        next_offset = str(end)

    await query.answer(
        results=results,
        cache_time=INLINE_CACHE_TIME,
        next_offset=next_offset,
    )
