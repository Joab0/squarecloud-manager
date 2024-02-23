from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord.app_commands.errors import (
    CheckFailure,
    CommandInvokeError,
    CommandOnCooldown,
)
from discord.ext import commands

from ..utils.embeds import ErrorEmbed
from ..utils.errors import GenericError
from ..utils.translator import Translator
from ..utils.utils import format_timedelta

if TYPE_CHECKING:
    from ..core import BotCore


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class CommandHandler(commands.Cog):
    """Cog to handler commands."""

    def __init__(self, bot: BotCore) -> None:
        self.bot: BotCore = bot

        # Global handler for errors.
        self.bot.tree.on_error = self.on_app_command_error

        # Global handler.
        self.bot.tree.interaction_check = self.on_app_command

    async def on_app_command_error(self, interaction: discord.Interaction[BotCore], error: Exception) -> None:
        if interaction.command is not None:
            if interaction.command._has_any_error_handlers():
                return

        t: Translator = interaction.extras["translator"]

        # Custom error
        if isinstance(error, CommandInvokeError):
            error = error.original

        match error:
            case CommandOnCooldown():
                cd = format_timedelta(int(error.retry_after))
                msg = t("errors.on_cooldown", cd)

            case GenericError():
                msg = error.args[0]

                # If not the original interaction.
                if error.interaction is not None:
                    interaction = error.interaction

            case CheckFailure():
                return  # ignore

            case _:
                msg = t("errors.unexpected_error", error)
                log.exception(
                    f"Error in command {interaction.command.qualified_name!r}:",  # type: ignore
                    exc_info=error,
                )

        embed = ErrorEmbed(msg)

        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def on_app_command(self, interaction: discord.Interaction[BotCore]) -> bool:
        interaction.extras["translator"] = Translator(interaction.locale)
        return True


async def setup(bot: BotCore) -> None:
    await bot.add_cog(CommandHandler(bot))
