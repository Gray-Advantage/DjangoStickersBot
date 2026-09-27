__all__ = ("Admin",)

from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message

from bot.bot import utils
from bot.models import TelegramUser


class Admin(Filter):
    async def __call__(
        self,
        event: CallbackQuery | Message,
    ) -> bool | dict[str, TelegramUser]:
        user = await utils.connect_user(event)
        if not user.is_admin:
            return False

        return {"user": user}
