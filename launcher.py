from __future__ import annotations

import asyncio
import logging
import os

from dotenv import load_dotenv
from rich.logging import RichHandler

from bot.core import BotCore

load_dotenv()


DEBUG = os.getenv("DEBUG", "false") in ("true", "1")


def setup_logging() -> None:
    if DEBUG:
        logging.getLogger("bot").setLevel(logging.DEBUG)
        logging.getLogger("squarecloud").setLevel(logging.DEBUG)

    log = logging.getLogger()
    log.setLevel(logging.INFO)

    log.addHandler(
        RichHandler(
            omit_repeated_times=False,
            rich_tracebacks=True,
        )
    )


setup_logging()
log = logging.getLogger(__name__)
log.info("Starting bot...")


async def main():
    async with BotCore(debug=DEBUG) as bot:
        await bot.start(os.environ["BOT_TOKEN"])


try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
except Exception:
    log.exception("Error when running the bot:")
