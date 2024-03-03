from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any

import discord
from discord import ButtonStyle, ui
from discord.ui.select import BaseSelect
from discord.utils import MISSING

from .embeds import ErrorEmbed
from .errors import GenericError

if TYPE_CHECKING:
    from ..core import BotCore
    from .translator import Translator


class BaseView(ui.View):
    """Bot base view."""

    def __init__(self, *, timeout: float | None = 300):
        super().__init__(timeout=timeout)

    def disable_all(self) -> None:
        for item in self.children:
            if isinstance(item, (ui.Button, BaseSelect)):
                item.disabled = True

    def enable_all(self) -> None:
        for item in self.children:
            if isinstance(item, (ui.Button, BaseSelect)):
                item.disabled = False

    async def on_error(  # type: ignore
        self,
        interaction: discord.Interaction[BotCore],
        error: Exception,
        item: ui.Item[Any],
    ) -> None:
        # Error handler for views.
        if isinstance(error, GenericError):
            interaction = error.interaction or interaction
            embed = ErrorEmbed(error.args[0])

            with suppress(discord.HTTPException):
                if interaction.response.is_done():
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await super().on_error(interaction, error, item)

    async def send_error(self, interaction: discord.Interaction[BotCore], error: str) -> None:
        embed = ErrorEmbed(error)

        with suppress(discord.HTTPException):
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)


class InputText(ui.Modal):
    """A base class to build modals.
    This modal does not have a callback, you must use a wait for logic.
    On submit, it fills the interaction attribute with the submit interaction.
    """

    def __init__(
        self,
        *inputs: ui.TextInput,
        title: str,
        timeout: float | None = 600,
        custom_id: str = MISSING,
    ) -> None:
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)

        for text_input in inputs:
            self.add_item(text_input)

    async def on_submit(self, interaction: discord.Interaction[BotCore]) -> None:  # type: ignore
        self.interaction = interaction
        self.stop()


class ConfirmView(BaseView):
    """A view for confirm prompts."""

    def __init__(self, t: Translator, *, timeout: float | None = 60):
        super().__init__(timeout=timeout)

        self.confirm.label = t("common.confirm")
        self.cancel.label = t("common.cancel")

        self.value: bool | None = None

    @ui.button(style=ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction[BotCore], _) -> None:
        self.value = True
        self.interaction = interaction
        self.stop()

    @ui.button(style=ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction[BotCore], _) -> None:
        self.value = False
        self.interaction = interaction
        self.stop()
