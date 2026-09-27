__all__ = ("recognize_stickers",)

import asyncio
import json
import logging
from pathlib import Path
import sys
import tempfile

logger = logging.getLogger(__name__)

WORKER_MODULE = "bot.bot.ocr_worker"
WORKER_TIMEOUT = 900


async def recognize_stickers(images: dict[str, bytes]) -> dict[str, str]:
    if not images:
        return {}

    with tempfile.TemporaryDirectory(prefix="sticker-ocr-") as tmp:
        folder = Path(tmp)
        for name, content in images.items():
            (folder / name).write_bytes(content)

        return await _run_worker(folder)


async def _run_worker(folder: Path) -> dict[str, str]:
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        WORKER_MODULE,
        str(folder),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        out, err = await asyncio.wait_for(
            process.communicate(),
            WORKER_TIMEOUT,
        )
    except TimeoutError:
        process.kill()
        await process.wait()
        logger.exception("Распознавание не уложилось в %s с", WORKER_TIMEOUT)
        return {}

    if process.returncode != 0:
        logger.error(
            "Распознавание завершилось с кодом %s: %s",
            process.returncode,
            err.decode(errors="replace")[-1000:],
        )
        return {}

    texts: dict[str, str] = json.loads(out)
    return texts
