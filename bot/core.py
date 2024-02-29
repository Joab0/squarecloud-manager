from __future__ import annotations

import logging
import os
import sqlite3
from contextlib import suppress
from typing import Any

import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands

from .utils.embeds import DefaultEmbed
from .utils.translator import Translator

log = logging.getLogger(__name__)


class BotCore(commands.Bot):
    """Bot core."""

    def __init__(self, *, debug: bool = False, **kwargs: Any) -> None:
        self.debug = debug

        # Intents setup
        # No need intents
        intents = discord.Intents.none()
        intents.guild_messages = True

        activity = discord.Activity(
            name="Manage your Square Cloud applications",
        )

        super().__init__(
            command_prefix=commands.when_mentioned,
            strip_after_prefix=True,
            help_command=None,
            intents=intents,
            activity=activity,
            status=discord.Status.online,
            **kwargs,
        )

        DefaultEmbed.set_default_color(0x2563EB)

        Translator.load("./locales")

        # App commands cache.
        # Useful to get the mention of a command.
        # NOTE: The bot was designed to work on just one server,
        # this cache is only for commands from the configured server.
        self.app_commands: dict[str, app_commands.AppCommand | app_commands.AppCommandGroup] = {}

    def update_app_commands_cache(self, commands: list[app_commands.AppCommand]) -> None:
        """Update application commands cache."""

        def unpack(options: list[app_commands.AppCommand | app_commands.AppCommandGroup | app_commands.Argument]):
            for option in options:
                if isinstance(option, app_commands.AppCommandGroup):
                    self.app_commands[option.qualified_name] = option
                    unpack(option.options)  # type: ignore

        for command in commands:
            unpack(command.options)  # type: ignore
            self.app_commands[command.name] = command

    def get_app_command(self, qualified_name: str) -> app_commands.AppCommand | app_commands.AppCommandGroup:
        """Get cached app command or group."""
        return self.app_commands[qualified_name]

    async def connect_db(self) -> None:
        """Creates the connection to the database."""

        # If not exists, init a new database.
        if not os.path.exists("database.db"):
            with open("init.sql", "r") as f:
                script = f.read()

            with sqlite3.connect("database.db") as conn:
                conn.executescript(script)
                conn.commit()

            log.info("The database was created")

        self.db = await aiosqlite.connect("database.db")

    async def load_extensions(self) -> None:
        """Load the bot extensions/cogs."""

        log.info("Loading extensions...")
        for element in os.listdir("bot/cogs"):
            # Python bytecodes
            if element == "__pycache__":
                continue

            # Cog is a file or folder.
            if not element.endswith(".py") and os.path.isfile(f"bot/cogs/{element}"):
                continue

            ext = element.removesuffix(".py")

            try:
                await self.load_extension(f"bot.cogs.{ext}")
                log.debug(f"{ext!r} has been loaded")
            except Exception:
                log.exception(f"Error when trying to load {ext!r}")
                raise

        # Load Jishaku if debug is enabled.
        if self.debug:
            try:
                await self.load_extension("jishaku")
                log.debug("Jishaku loaded.")
            except Exception:
                log.warning("It was not possible to load Jishaku.")
        log.info("All extensions loaded!")

    async def on_ready(self):
        assert self.user is not None
        latency = round(self.latency * 1000)
        log.info(f"Connected in: {self.user} (ID: {self.user.id})")
        log.info(f"Latency: {latency}ms")

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        await super().on_message(message)

    async def setup_hook(self) -> None:
        # Sync and cache commands.
        guild = discord.Object(os.environ["GUILD_ID"])

        log.info(f"Synchronizing commands in {guild.id}...")

        self.tree.copy_global_to(guild=guild)

        commands = await self.tree.sync(guild=guild)
        self.update_app_commands_cache(commands)
        log.info(f"{len(commands)} commands synchronized in {guild.id}!")

    async def start(self, token: str, *, reconnect: bool = True) -> None:
        # Before login
        await self.connect_db()
        await self.load_extensions()

        await super().start(token, reconnect=reconnect)

    async def close(self):
        log.info("Exiting...")
        with suppress(AttributeError):
            await self.db.close()

        await super().close()
