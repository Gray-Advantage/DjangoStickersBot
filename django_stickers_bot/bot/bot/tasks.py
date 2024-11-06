from io import BytesIO

from django.conf import settings
from easyocr import Reader
from PIL import Image, ImageEnhance, ImageFilter
from telebot import TeleBot, types

from bot.bot import keyboards
from bot.bot.utils import connect_user, preprocess_text
from bot.models import Sticker, StickerSet


reader = Reader(["ru", "en"], model_storage_directory=settings.OCR_MODELS)


def upscale_data(content: bytes) -> bytes:
    with Image.open(BytesIO(content)) as img:
        img = img.convert("RGB")
        img = img.filter(ImageFilter.MedianFilter(size=3))
        img = ImageEnhance.Contrast(img).enhance(1.2)

        output = BytesIO()
        img.save(output, format="PNG")
        output.seek(0)

        return output.getvalue()


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

        if sticker.is_video or sticker.is_animated:
            flag_warn_about_video = True
            continue

        content = bot.download_file(bot.get_file(sticker.file_id).file_path)
        try:
            text_data = preprocess_text(reader.readtext(upscale_data(content)))
        except Exception:
            text_data = "<Пусто>"

        Sticker.objects.create(
            file_id=sticker.file_id,
            file_unique_id=sticker.file_unique_id,
            text=text_data,
            sticker_set=db_sticker_set,
        )
        sticker_message = bot.send_sticker(
            call.message.chat.id,
            sticker.file_id,
        )
        bot.reply_to(
            sticker_message,
            f"Стикер {num}/{len(tg_sticker_set.stickers)}:\n"
            "```\n"
            f"{text_data}\n"
            "```",
            reply_markup=keyboards.edit_sticker_text(sticker.file_unique_id),
            parse_mode="Markdown",
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


__all__ = ["including_sticker_set"]
