from __future__ import annotations

import io
import os
import zipfile
from contextlib import suppress
from typing import TYPE_CHECKING

import discord
from discord import app_commands, ui
from discord.app_commands import locale_str
from discord.ext import commands

import squarecloud

from ...utils.embeds import DefaultEmbed, ErrorEmbed
from ...utils.errors import GenericError
from ...utils.translator import Translator
from ...utils.views import InputText
from .views import ManageApplicationView, SelectApplicationView, UploadedApplicationView

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
                self._api_keys_cache[user.id] = api_key
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
            raise GenericError(t("login.error"), interaction)

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
                            squarecloud.ConfigFile.from_str(f.read().decode())
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
            raise GenericError(t("up.error", e.code))

        embed = DefaultEmbed(description=f"✅ **|** {t('up.success', app.id)}")

        view = UploadedApplicationView(t, client, app)

        await interaction.edit_original_response(embed=embed, view=view)

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
            raise GenericError(t("errors.no_apps"))

        view = SelectApplicationView(t, client, apps, context="apps")
        await interaction.response.send_message(embed=view.embed, view=view, ephemeral=True)

        if await view.wait():
            return
        interaction = view.interaction
        selected = view.selected

        # Get full app and status.
        embed = DefaultEmbed(description=f"⌛ **|** {t('apps.loading')}")

        await interaction.response.edit_message(embed=embed, view=None)

        # Get full app infos.
        app = await client.get_app(selected.id)
        # Get status and update internal cache.
        status = await app.get_status()
        if status.running:
            with suppress(squarecloud.NotFound):
                await app.get_logs()

        view = ManageApplicationView(t, app)
        await interaction.edit_original_response(embed=view.embed, view=view)

    @app_commands.command(
        name=locale_str(_t("commit.name"), id="commit.name"),
        description=locale_str(_t("commit.description"), id="commit.description"),
        extras={"need_auth": True},
    )
    @app_commands.rename(
        file=locale_str(_t("commit.file.name"), id="commit.file.name"),
        restart=locale_str(_t("commit.restart.name"), id="commit.restart.name"),
    )
    @app_commands.describe(
        file=locale_str(_t("commit.file.description"), id="commit.file.description"),
        restart=locale_str(_t("commit.restart.description"), id="commit.restart.description"),
    )
    @app_commands.checks.cooldown(1, 15)
    async def commit(
        self,
        interaction: discord.Interaction[BotCore],
        file: discord.Attachment,
        restart: bool | None = None,
    ) -> None:
        t: Translator = interaction.extras["translator"]
        client: squarecloud.Client = interaction.extras["square_client"]

        apps = await client.get_all_apps()
        if not apps:
            raise GenericError(t("errors.no_apps"))

        view = SelectApplicationView(t, client, apps, context="commit")
        await interaction.response.send_message(embed=view.embed, view=view, ephemeral=True)

        if await view.wait():
            return

        interaction = view.interaction
        app = view.selected

        embed = DefaultEmbed(description=t("commit.loading"))

        await interaction.response.edit_message(embed=embed, view=None)

        data = await file.read()
        commit_file = squarecloud.File(data, filename=file.filename)

        try:
            await client.commit(id=app.id, file=commit_file, restart=restart)
        except squarecloud.HTTPException:
            raise GenericError(t("commit.error"), interaction=interaction)

        embed.description = t("commit.success")
        await interaction.edit_original_response(embed=embed)

    # If the bot is running on Square Cloud,
    # there is an env var called "HOSTNAME" with the value of "squarecloud.app".
    if os.getenv("HOSTNAME") != "squarecloud.app":

        @app_commands.command(
            name=locale_str(_t("host.name"), id="host.name"),
            description=locale_str(_t("host.description"), id="host.description"),
            extras={"need_auth": True},
        )
        @app_commands.checks.cooldown(1, 15)  # Avoid multi uploads.
        async def host(self, interaction: discord.Interaction[BotCore]) -> None:
            """Automatically hosts this bot."""
            t: Translator = interaction.extras["translator"]
            client: squarecloud.Client = interaction.extras["square_client"]

            embed = DefaultEmbed(
                description=t("host.uploading"),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "a", zipfile.ZIP_DEFLATED) as zf:
                for dirname, _, files in os.walk("./"):
                    zf.write(dirname)
                    for filename in files:
                        zf.write(os.path.join(dirname, filename))

            buffer.seek(0)
            file = squarecloud.File(buffer, "bot.zip")

            try:
                await client.upload(file)
            except squarecloud.HTTPException as e:
                raise GenericError(t("host.error", e.code))

            embed.description = t("host.success")

            await interaction.edit_original_response(embed=embed)

            await self.bot.close()


async def setup(bot: BotCore) -> None:
    await bot.add_cog(SquareCloud(bot))
