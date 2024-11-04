from telebot import types

from bot.models import TelegramUser

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


__all__ = ["ALL_CONTENT_TYPES", "preprocess_text", "connect_user"]
