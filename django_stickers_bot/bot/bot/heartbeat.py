__all__ = ("HEARTBEAT_PATH", "heartbeat_loop", "is_fresh", "write_stamp")

import asyncio
import logging
from pathlib import Path
import sys
import time

from aiogram import Bot

logger = logging.getLogger(__name__)

HEARTBEAT_PATH = Path("/tmp/bot-heartbeat")  # noqa: S108
INTERVAL = 60
MAX_AGE = 300


async def heartbeat_loop(bot: Bot) -> None:
    while True:
        try:
            await bot.get_me()
        except Exception:
            logger.exception("Telegram не ответил на проверку связи")
        else:
            await asyncio.to_thread(write_stamp, time.time())

        await asyncio.sleep(INTERVAL)


def write_stamp(stamp: float) -> None:
    temporary = HEARTBEAT_PATH.with_suffix(".tmp")
    temporary.write_text(str(stamp))
    temporary.replace(HEARTBEAT_PATH)


def is_fresh(max_age: float = MAX_AGE) -> bool:
    try:
        stamp = float(HEARTBEAT_PATH.read_text())
    except (OSError, ValueError):
        return False

    return time.time() - stamp < max_age


def main() -> None:
    sys.exit(0 if is_fresh() else 1)


if __name__ == "__main__":
    main()
