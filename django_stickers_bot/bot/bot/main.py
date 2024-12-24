from threading import Thread

from django.conf import settings
from telebot import TeleBot
import telebot.types

from bot.bot import keyboards, tasks, utils
from bot.models import Sticker, StickerSet, TelegramUser

bot = TeleBot(settings.BOT_TOKEN)


@bot.message_handler(commands=["start"])
def start(message: telebot.types.Message):
    user = utils.connect_user(message)

    extra_text = ""
    if user.is_admin:
        extra_text = (
            "\n\nА ещё ты админ! Можешь мне прислать доп. стикеры и я буду "
            "искать ещё и среди них при следующих запросах пользователей"
        )

    bot.send_message(
        message.chat.id,
        "Привет, я бот, который поможет найти тебе тот самый стикер с "
        "специализации Django\n"
        "\n"
        "Достаточно написать отрывок текста, а я попробую найти подходящий"
        f"{extra_text}",
    )

    if user.state != user.UserStates.IDLE or user.context_data != "":
        user.state = user.UserStates.IDLE
        user.context_data = ""
        user.save()
        bot.send_message(
            message.chat.id,
            "Кстати, я ещё сделал сброс твоего состояния",
        )


@bot.message_handler(commands=["all"])
def all_sticker_sets(message: telebot.types.Message):
    sticker_sets = StickerSet.objects.all()
    for sticker_set in sticker_sets:
        first_sticker = sticker_set.stickers.first()
        bot.send_sticker(
            message.chat.id,
            first_sticker.file_id,
        )


@bot.message_handler(content_types=utils.ALL_CONTENT_TYPES)
def router(message: telebot.types.Message):
    if message.content_type not in ["text", "sticker"]:
        bot.delete_message(message.chat.id, message.message_id)
        return None

    user = utils.connect_user(message)

    if message.content_type == "text":
        if user.state == user.UserStates.IDLE:
            return search(message)
        return edit_sticker_text(message, user)

    if user.is_admin:
        return process_sticker(message)
    return bot.delete_message(message.chat.id, message.message_id)


def search(message: telebot.types.Message):
    start_search_msg = bot.send_message(message.chat.id, "Происходит поиск...")

    result = Sticker.objects.search(message.text)
    for sticker in result:
        message = bot.send_sticker(message.chat.id, sticker.file_id)
        if settings.DEBUG:
            bot.reply_to(
                message,
                f"quality: {sticker.quality}\n"
                f"similarity: {sticker.similarity}\n"
                f"rank: {sticker.rank}\n",
            )

    if len(result) == 0:
        bot.send_message(message.chat.id, "К сожалению, ничего не найдено")
    bot.delete_message(message.chat.id, start_search_msg.message_id)


def edit_sticker_text(message: telebot.types.Message, user: TelegramUser):
    sticker_id = user.context_data

    sticker = Sticker.objects.get(file_unique_id=sticker_id)
    sticker.text = message.text
    sticker.save()

    bot.send_message(message.chat.id, "Текст стикера обновлен!")

    user.context_data = ""
    user.state = user.UserStates.IDLE
    user.save()


def process_sticker(message: telebot.types.Message):
    sticker = message.sticker
    if sticker.set_name is None:
        bot.send_message(
            message.chat.id,
            "Сорри, принимаю стикеры только из наборов, одиночные не подойдут",
        )
        return

    tg_sticker_set = bot.get_sticker_set(sticker.set_name)

    if StickerSet.objects.filter(name=tg_sticker_set.name).exists():
        bot.reply_to(
            message,
            "Этот стикер пак у меня уже есть",
            reply_markup=keyboards.see_sticker_set(
                tg_sticker_set.name,
                sticker.file_unique_id,
            ),
        )
    else:
        bot.reply_to(
            message,
            "О, такого стикер пака у меня нет, начать процесс добавления?",
            reply_markup=keyboards.add_sticker_set(tg_sticker_set.name),
        )


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call: telebot.types.CallbackQuery):
    bot.answer_callback_query(call.id)
    data = call.data

    if data.startswith("add_sticker_set"):
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None,
        )
        Thread(
            target=tasks.including_sticker_set,
            args=(bot, call, bot.get_sticker_set(data.split(":", 1)[1])),
        ).start()

    elif data.startswith("edit_sticker_text"):
        user = utils.connect_user(call)
        user.state = user.UserStates.EDIT_STICKER_TEXT
        user.context_data = data.split(":", 1)[1]
        user.save()

        bot.reply_to(
            call.message,
            "Ожидаю новый текст для этого стикера",
        )

    elif data.startswith("see_sticker_set"):
        stickers = Sticker.objects.filter(
            sticker_set__name=data.split(":", 1)[1],
        )
        for num, sticker in enumerate(stickers, 1):
            utils.show_sticker(
                call.message.chat.id,
                sticker,
                bot,
                sticker.text,
                f"Стикер {num}/{len(stickers)}:",
            )

    elif data.startswith("see_sticker"):
        sticker = Sticker.objects.get(file_unique_id=data.split(":", 1)[1])
        utils.show_sticker(call.message.chat.id, sticker, bot, sticker.text)

    elif data.startswith("delete_sticker_set"):
        StickerSet.objects.filter(name=data.split(":", 1)[1]).delete()
        bot.edit_message_text(
            "Стикер пак удалён",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
        )


@bot.inline_handler(lambda query: True)
def handle_inline_query(inline_query: telebot.types.InlineQuery):
    if inline_query.query == "":
        return

    result = Sticker.objects.search(inline_query.query)

    bot.answer_inline_query(
        inline_query.id,
        results=[
            telebot.types.InlineQueryResultCachedSticker(
                id=sticker.file_unique_id,
                sticker_file_id=sticker.file_id,
            )
            for sticker in result
        ],
    )


def start_polling():
    while True:
        try:
            bot.polling()
        except Exception:
            continue


if settings.RUNNING:
    if not settings.BOT_USE_WEBHOOK:
        bot.remove_webhook()
        thread = Thread(target=start_polling, daemon=True)
        thread.start()
    else:
        bot.set_webhook(f"https://{settings.BOT_WEBHOOK_URL}/bot/")


__all__ = ["bot"]
