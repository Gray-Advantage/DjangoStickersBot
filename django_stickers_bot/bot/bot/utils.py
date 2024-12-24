from io import BytesIO

from django.conf import settings
from PIL import Image, ImageEnhance, ImageFilter
from telebot import types

from bot.bot import keyboards
from bot.models import Sticker, TelegramUser


if settings.RUNNING:
    from easyocr import Reader

    reader = Reader(["ru", "en"], model_storage_directory=settings.OCR_MODELS)


ALL_CONTENT_TYPES = [
    "text",
    "audio",
    "document",
    "photo",
    "sticker",
    "video",
    "video_note",
    "voice",
    "location",
    "contact",
    "new_chat_members",
    "left_chat_member",
    "new_chat_title",
    "new_chat_photo",
    "delete_chat_photo",
    "group_chat_created",
    "supergroup_chat_created",
    "channel_chat_created",
    "migrate_to_chat_id",
    "migrate_from_chat_id",
    "pinned_message",
]


def add_sticker(tg_sticker, db_sticker_set, bot):
    if tg_sticker.is_video or tg_sticker.is_animated:
        return True, "<Пусто>"

    content = bot.download_file(bot.get_file(tg_sticker.file_id).file_path)
    try:
        text_data = preprocess_text(reader.readtext(upscale_data(content)))
    except Exception:
        text_data = "<Пусто>"

    Sticker.objects.create(
        file_id=tg_sticker.file_id,
        file_unique_id=tg_sticker.file_unique_id,
        text=text_data,
        sticker_set=db_sticker_set,
    )
    return False, text_data


def show_sticker(chat_id, tg_sticker, bot, text=None, pretext=""):
    sticker_message = bot.send_sticker(chat_id, tg_sticker.file_id)

    if text is None:
        try:
            text = Sticker.objects.get(file_id=tg_sticker.file_id).text
        except Sticker.DoesNotExist:
            text = "<Пусто>"

    bot.reply_to(
        sticker_message,
        f"{pretext}\n" "```\n" f"{text}\n" "```",
        reply_markup=keyboards.edit_sticker_text(tg_sticker.file_unique_id),
        parse_mode="Markdown",
    )


def preprocess_text(results, vertical_shift=15, horizontal_shift=10):
    results.sort(key=lambda x: min(point[1] for point in x[0]))

    lines, current_line = [], []
    current_y = min(point[1] for point in results[0][0])

    for item in results:
        min_y = min(point[1] for point in item[0])
        if abs(min_y - current_y) > vertical_shift:
            lines.append(current_line)
            current_line, current_y = [item], min_y
        else:
            current_line.append(item)

    if current_line:
        lines.append(current_line)

    final_text = []
    for line in lines:
        line.sort(key=lambda x: min(point[0] for point in x[0]))

        line_text = []
        last_x = None
        for word in line:
            word_text = word[1]
            min_x = min(point[0] for point in word[0])

            if last_x is not None and min_x - last_x > horizontal_shift:
                line_text.append(" ")
            line_text.append(word_text)
            last_x = max(point[0] for point in word[0])

        final_text.append(" ".join(line_text))

    return "\n".join(final_text)


def connect_user(connect_obj: types.CallbackQuery | types.Message):
    return TelegramUser.objects.get_or_create(
        telegram_id=connect_obj.from_user.id,
        defaults={"telegram_id": connect_obj.from_user.id},
    )[0]


def upscale_data(content: bytes) -> bytes:
    with Image.open(BytesIO(content)) as img:
        img = img.convert("RGB")
        img = img.filter(ImageFilter.MedianFilter(size=3))
        img = ImageEnhance.Contrast(img).enhance(1.2)

        output = BytesIO()
        img.save(output, format="PNG")
        output.seek(0)

        return output.getvalue()


__all__ = [
    "ALL_CONTENT_TYPES",
    "connect_user",
    "add_sticker",
    "show_sticker",
]
