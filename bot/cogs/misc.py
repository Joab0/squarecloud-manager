from __future__ import annotations

import time
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands

from ..utils.embeds import DefaultEmbed
from ..utils.translator import Translator

if TYPE_CHECKING:
    from ..core import BotCore

_t = Translator()


class Misc(commands.Cog):
    """Cog for misc commands."""

    def __init__(self, bot: BotCore) -> None:
        self.bot: BotCore = bot

    @app_commands.command(
        name=locale_str(_t("ping.name"), id="ping.name"),
        description=locale_str(_t("ping.description"), id="ping.description"),
    )
    async def ping(self, interaction: discord.Interaction[BotCore]) -> None:
        t: Translator = interaction.extras["translator"]

        latency = round(self.bot.latency * 1000)

        start = time.perf_counter()
        await interaction.response.defer(ephemeral=True)
        end = time.perf_counter()

        response_time = round((end - start) * 1000)

        embed = DefaultEmbed(title=f"🏓 {t('ping.pong')}")

        embed.add_field(name=f"📡 {t('ping.latency')}", value=f"{latency}ms", inline=False)
        embed.add_field(
            name=f"⚡ {t('ping.response_time')}",
            value=f"{response_time}ms",
            inline=False,
        )

        embed.set_thumbnail(url=self.bot.user.display_avatar)  # type: ignore

        await interaction.edit_original_response(embed=embed)

    @app_commands.command(
        name=locale_str(_t("help.name"), id="help.name"),
        description=locale_str(_t("help.description"), id="help.description"),
    )
    async def _help(self, interaction: discord.Interaction[BotCore]) -> None:
        t: Translator = interaction.extras["translator"]

        embed = DefaultEmbed(title=t("help.command_list"), description="")

        embed.set_thumbnail(url=self.bot.user.avatar)  # type: ignore

        # Create command list
        for cmd_name, command in self.bot.app_commands.items():
            if isinstance(command, app_commands.AppCommandGroup):
                continue

            desc_key = f"{cmd_name.replace(' ', '.')}.description"
            embed.description += f"🔹 {command.mention}: {t(desc_key)}\n"  # type: ignore

        t_args = (
            interaction.user.global_name,
            "https://squarecloud.app/",
            self.bot.get_app_command("login").mention,
        )

        await interaction.response.send_message(t("help.response", *t_args), embed=embed, ephemeral=True)


async def setup(bot: BotCore) -> None:
    await bot.add_cog(Misc(bot))
