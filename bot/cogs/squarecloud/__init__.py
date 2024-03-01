from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

import discord
from discord import app_commands, ui
from discord.app_commands import locale_str
from discord.ext import commands
from discord.utils import utcnow

import squarecloud

from ...utils.embeds import DefaultEmbed, ErrorEmbed
from ...utils.errors import GenericError
from ...utils.translator import Translator
from ...utils.views import InputText
from .views import ManageApplication, SelectApplication

if TYPE_CHECKING:
    from ...core import BotCore

_t = Translator()


class SquareCloud(commands.Cog):
    """Cog to interact with Square Cloud."""

    def __init__(self, bot: BotCore) -> None:
        self.bot: BotCore = bot

        # API keys cache
        # {user_id: api_key}
        self._api_keys_cache: dict[int, str] = {}

    async def interaction_check(self, interaction: discord.Interaction[BotCore], /) -> bool:  # type: ignore
        # Checks if a command needs authentication.
        need_auth: bool = interaction.command.extras.get("need_auth", False)  # type: ignore
        if need_auth:
            api_key = await self.get_user_api_key(interaction.user)
            if api_key is None:
                t: Translator = interaction.extras["translator"]
                cmd = self.bot.get_app_command("login")
                embed = ErrorEmbed(t("errors.unauthenticated", cmd.mention))
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return False
            interaction.extras["square_client"] = squarecloud.Client(api_key)
        else:
            # Client without authentication, useful for statistics command.
            interaction.extras["square_client"] = squarecloud.Client(None)
        return True

    async def get_user_api_key(self, user: discord.abc.Snowflake, *, use_cached: bool = True) -> str | None:
        """Returns a user's API key."""
        # Checks if the user has a cached API key.
        if use_cached and user.id in self._api_keys_cache:
            api_key = self._api_keys_cache[user.id]
            return api_key

        # Fetch user API key in database.
        async with self.bot.db.cursor() as cursor:
            await cursor.execute(
                """
                SELECT
                    api_key
                FROM
                    api_keys
                WHERE
                    user_id = ?
                """,
                (user.id,),
            )
            if (row := await cursor.fetchone()) is None:
                api_key = None
            else:
                api_key = row[0]

        client = squarecloud.Client(api_key)

        # Validades API key.
        if api_key is not None:
            try:
                await client.me()
            except squarecloud.AuthenticationFailure:
                # The API key is invalid, remove it from the database.
                await self.remove_api_key(user)
                return None

        return api_key

    async def save_api_key(self, user: discord.abc.Snowflake, api_key: str) -> None:
        """Save the user's API key in database."""
        # Check if the user is already in the database.
        exists = await self.get_user_api_key(user, use_cached=False) is not None

        # Save or update API key.
        async with self.bot.db.cursor() as cursor:
            if exists:
                await cursor.execute(
                    """
                    UPDATE
                    FROM
                        api_keys
                    SET
                        api_key = ?
                    WHERE
                        user_id = ?
                    """,
                    (api_key, user.id),
                )
            else:
                await cursor.execute(
                    """
                    INSERT INTO
                        api_keys
                    VALUES
                        (?, ?)
                    """,
                    (user.id, api_key),
                )

            await self.bot.db.commit()

        # Saves to cache to avoid fetch and validation in future
        self._api_keys_cache[user.id] = api_key

    async def remove_api_key(self, user: discord.abc.Snowflake) -> None:
        """Delete user's API key from database."""
        async with self.bot.db.cursor() as cursor:
            await cursor.execute(
                """
                DELETE FROM api_keys
                WHERE
                    user_id = ?
                """,
                (user.id,),
            )

            await self.bot.db.commit()

    @app_commands.command(
        name=locale_str(_t("statistics.name"), id="statistics.name"),
        description=locale_str(_t("statistics.description"), id="statistics.description"),
    )
    @app_commands.checks.cooldown(1, 5)
    async def statistics(self, interaction: discord.Interaction[BotCore]) -> None:
        """Command to get current host statistics."""
        t: Translator = interaction.extras["translator"]
        client: squarecloud.Client = interaction.extras["square_client"]
        stats = await client.get_services_statistics()

        embed = DefaultEmbed(
            title=t("statistics.title"),
            description=(
                f"**{t('statistics.users')}:** {stats.users}\n"
                f"**{t('statistics.apps')}:** {stats.apps}\n"
                f"**{t('statistics.websites')}:** {stats.websites}\n"
                f"**{t('statistics.ping')}:** {stats.ping}ms\n"
            ),
            timestamp=utcnow(),
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name=locale_str(_t("login.name"), id="login.name"),
        description=locale_str(_t("login.description"), id="login.description"),
    )
    @app_commands.checks.cooldown(1, 5)
    async def login(self, interaction: discord.Interaction[BotCore]) -> None:
        """Command to setup Square Cloud API key."""

        t: Translator = interaction.extras["translator"]

        # Create login form.
        api_key_input = ui.TextInput(
            label=t("login.modal.api_key_input.label"),
            placeholder=t("login.modal.api_key_input.placeholder"),
            min_length=10,
            max_length=100,
        )

        modal = InputText(api_key_input, title=t("login.modal.title"))

        await interaction.response.send_modal(modal)

        if await modal.wait():
            return

        # Use modal interaction
        interaction = modal.interaction

        api_key = api_key_input.value.strip()

        try:
            client = squarecloud.Client(api_key)
            # Check if API key is valid.
            await client.me()
        except squarecloud.errors.AuthenticationFailure:
            raise GenericError(t("login.failure"), interaction)

        await self.save_api_key(interaction.user, api_key)

        embed = DefaultEmbed(description=f"✅ **|** {t('login.success')}")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name=locale_str(_t("up.name"), id="up.name"),
        description=locale_str(_t("up.description"), id="up.description"),
        extras={"need_auth": True},
    )
    @app_commands.checks.cooldown(1, 15)
    async def up(self, interaction: discord.Interaction[BotCore]) -> None:
        """Upload an app to Square Cloud."""

    @app_commands.command(
        name=locale_str(_t("apps.name"), id="apps.name"),
        description=locale_str(_t("apps.description"), id="apps.description"),
        extras={"need_auth": True},
    )
    @app_commands.checks.cooldown(1, 5)
    async def apps(self, interaction: discord.Interaction[BotCore]) -> None:
        """Command to show this user's informations."""
        t: Translator = interaction.extras["translator"]
        client: squarecloud.Client = interaction.extras["square_client"]

        apps = await client.get_all_apps()
        if not apps:
            raise GenericError(t("apps.no_apps"))

        # If the user only has 1 app, skip the select part.
        if len(apps) == 1:
            selected = apps[0]
        else:
            view = SelectApplication(t, apps)

            await interaction.response.send_message(embed=view.embed, view=view, ephemeral=True)

            if await view.wait():
                return

            interaction = view.interaction

            selected = view.selected

        # Get full app and status.
        await interaction.response.edit_message(content=t("apps.loading"), embed=None, view=None)
        app = await client.get_app(selected.id)
        # Get status and update internal cache.
        status = await app.get_status()
        if status.running:
            with suppress(squarecloud.NotFound):
                await app.get_logs()

        view = ManageApplication(t, client, app)

        await interaction.edit_original_response(content=None, embed=view.embed, view=view)


async def setup(bot: BotCore) -> None:
    await bot.add_cog(SquareCloud(bot))
