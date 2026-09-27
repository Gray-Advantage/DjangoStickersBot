__all__ = ()

import asyncio
import contextlib
import logging
from typing import Any

from aiogram import Bot
from aiogram.types import BotCommand
from django.conf import settings
from django.core.management.base import BaseCommand

from bot.bot.heartbeat import heartbeat_loop
from bot.bot.main import build_dispatcher
from bot.bot.tasks import sync_loop

COMMANDS = (
    BotCommand(command="start", description="Как пользоваться ботом"),
    BotCommand(command="all", description="Показать все наборы стикеров"),
)


class Command(BaseCommand):
    help = "Запустить бота: опрос Telegram и фоновая сверка наборов"

    def handle(self, *args: Any, **options: Any) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
        self.stdout.write(
            self.style.SUCCESS("Бот запущен, опрашиваю Telegram"),
        )
        asyncio.run(self.run_bot())

    async def run_bot(self) -> None:
        bot = Bot(token=settings.BOT_TOKEN)
        dispatcher = build_dispatcher()
        background = [
            asyncio.create_task(sync_loop(bot)),
            asyncio.create_task(heartbeat_loop(bot)),
        ]
        try:
            await bot.delete_webhook(drop_pending_updates=False)
            await bot.set_my_commands(list(COMMANDS))
            await dispatcher.start_polling(bot)
        finally:
            for task in background:
                task.cancel()

            for task in background:
                with contextlib.suppress(asyncio.CancelledError):
                    await task

            await bot.session.close()
