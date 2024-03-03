from __future__ import annotations

import asyncio
import io
import zipfile
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
from .views import SelectApplication

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
            interaction.extras["square_client"] = squarecloud.Client(api_key, session=self.bot.session)
        else:
            # Client without authentication, useful for statistics command.
            interaction.extras["square_client"] = squarecloud.Client(None, session=self.bot.session)
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
    @app_commands.rename(file=locale_str(_t("up.file.name"), id="up.file.name"))
    @app_commands.describe(file=locale_str(_t("up.file.description"), id="up.file.description"))
    @app_commands.checks.cooldown(1, 15)
    async def up(self, interaction: discord.Interaction[BotCore], file: discord.Attachment) -> None:
        """Upload an app to Square Cloud."""
        t: Translator = interaction.extras["translator"]
        client: squarecloud.Client = interaction.extras["square_client"]

        # Check here to avoid API errors.
        if not file.filename.endswith(".zip"):
            raise GenericError(t("up.invalid_file"))

        embed = DefaultEmbed(description=f"⏳ **|** {t('up.loading')}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

        buffer = io.BytesIO()
        await file.save(buffer)

        # Prevents errors before upload by opening and verifying the file.
        try:
            with zipfile.ZipFile(buffer) as zip_file:
                try:
                    with zip_file.open("squarecloud.app") as f:
                        try:
                            config = squarecloud.ConfigFile.from_str(f.read().decode())
                        # Bad config file.
                        except TypeError:
                            raise GenericError(t("up.bad_config_file"))
                        # Missing keys.
                        except ValueError as e:
                            # The exception returns forget key.
                            forget: str = e.args[1]
                            raise GenericError(t("up.config_file_forget_key", forget))
                # Config file not found.
                except KeyError:
                    raise GenericError(t("up.missing_config_file"))
        # Bad zip file.
        except zipfile.BadZipFile:
            raise GenericError(t("up.invalid_zip_file"))

        # After this verification, send the application.
        square_file = squarecloud.File(buffer, file.filename)
        try:
            app = await client.upload(square_file)
        except squarecloud.HTTPException as e:
            raise GenericError(t("up.failure", e.code))

        embed = DefaultEmbed(description=f"✅ **|** {t('up.success', app.id)}")
        await interaction.edit_original_response(embed=embed)

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

        view = SelectApplication(t, client, apps)
        await interaction.response.send_message(embed=view.embed, view=view, ephemeral=True)


async def setup(bot: BotCore) -> None:
    await bot.add_cog(SquareCloud(bot))
