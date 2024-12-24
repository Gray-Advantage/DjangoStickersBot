from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
from django.db.models import Count
from telebot import TeleBot, types

from bot.bot.utils import add_sticker, connect_user, show_sticker
from bot.models import Sticker, StickerSet, TelegramUser


def including_sticker_set(
    bot: TeleBot,
    call: types.CallbackQuery,
    tg_sticker_set: types.StickerSet,
):
    db_sticker_set = StickerSet.objects.create(
        name=tg_sticker_set.name,
        user=connect_user(call),
    )

    flag_warn_about_video = False
    for num, sticker in enumerate(tg_sticker_set.stickers, 1):
        bot.edit_message_text(
            f"Обработка: {num}/{len(tg_sticker_set.stickers)}",
            chat_id=call.message.chat.id,
            message_id=call.message.id,
        )

        warm, text = add_sticker(sticker, db_sticker_set, bot)

        if warm:
            flag_warn_about_video = True
            continue

        show_sticker(
            call.message.chat.id,
            sticker,
            bot,
            text,
            f"Стикер {num}/{len(tg_sticker_set.stickers)}:",
        )

    if flag_warn_about_video:
        bot.send_message(
            call.message.chat.id,
            "Некоторые стикеры не обработаны, так как это видео или анимация",
        )
    bot.send_message(
        call.message.chat.id,
        "Стикер пак весь добавлен!",
    )


def check_stickers_updates():
    bot = TeleBot(settings.BOT_TOKEN)

    db_stickers = StickerSet.objects.annotate(size=Count("stickers"))
    for db_sticker_set in db_stickers:
        tg_sticker_set = bot.get_sticker_set(db_sticker_set.name)
        if len(tg_sticker_set.stickers) < db_sticker_set.size:
            Sticker.objects.filter(sticker_set=db_sticker_set).exclude(
                file_id__in=[stic.file_id for stic in tg_sticker_set.stickers],
            ).delete()

            for admin in TelegramUser.objects.filter(is_admin=True):
                msg = bot.send_sticker(
                    admin.telegram_id,
                    tg_sticker_set.stickers[0].file_id,
                )
                bot.reply_to(
                    msg,
                    "Из этого стикерпака был(и) удален(ы) стикер(ы)",
                )
        elif len(tg_sticker_set.stickers) > db_sticker_set.size:
            db_stickers = Sticker.objects.filter(sticker_set=db_sticker_set)
            db_stickers = [sticker.file_id for sticker in db_stickers]
            new_stickers = [
                stic
                for stic in tg_sticker_set.stickers
                if stic.file_id not in db_stickers
            ]

            admins = TelegramUser.objects.filter(is_admin=True)
            for sticker in new_stickers:
                warm, text = add_sticker(sticker, db_sticker_set, bot)
                if warm:
                    continue
                for admin in admins:
                    show_sticker(
                        admin.telegram_id,
                        sticker,
                        bot,
                        text,
                        "В набор был автоматически добавлен новый стикер",
                    )


if settings.RUNNING:
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_stickers_updates, "interval", minutes=5)
    scheduler.start()


__all__ = ["including_sticker_set"]
