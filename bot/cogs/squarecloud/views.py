from __future__ import annotations

import asyncio
import io
import math
from contextlib import suppress
from typing import TYPE_CHECKING

import discord
from discord import ButtonStyle, ui
from discord.utils import format_dt, utcnow

import squarecloud
from squarecloud.application import UploadedApplication

from ...utils.embeds import DefaultEmbed
from ...utils.errors import GenericError
from ...utils.views import BaseView, ConfirmView

if TYPE_CHECKING:
    from squarecloud import Application, Client, PartialApplication

    from ...core import BotCore
    from ...utils.translator import Translator


# Max entries in a select menu.
SELECT_LIMIT = 25


class _BaseSelectApplicationView(BaseView):
    """A view to select applications, if you exceed the Discord limit,
    pagination buttons will be added.
    """

    def __init__(
        self,
        apps: list[PartialApplication],
        *,
        page: int = 1,
        timeout: float | None = 300,
    ) -> None:
        super().__init__(timeout=timeout)

        self.apps: list[PartialApplication] = apps
        self.current_page: int = min(page, self.max_page)

        self._update_state()

    @property
    def max_page(self) -> int:
        return math.ceil(len(self.apps) / SELECT_LIMIT)

    @property
    def current_page_apps(self) -> list[PartialApplication]:
        # To Python index.
        i = self.current_page - 1

        # Return current page apps.
        return self.apps[i * SELECT_LIMIT : i * SELECT_LIMIT + SELECT_LIMIT]

    @property
    def embed(self) -> DefaultEmbed:
        return NotImplemented

    def _update_state(self) -> None:
        # If there is only 1 page remove the navigation buttons.
        if self.max_page == 1:
            self.remove_item(self.previous_page)
            self.remove_item(self.next_page)

        # Create select
        self.select.options.clear()

        for app in self.current_page_apps:
            self.select.add_option(
                label=app.name,
                description=app.description,
                emoji="🌐" if app.is_website else "🖥️",
                value=app.id,
            )

        # Update buttons state
        self.previous_page.disabled = self.current_page == 1
        self.next_page.disabled = self.current_page == self.max_page

    async def callback(self, interaction: discord.Interaction[BotCore], partial_app: PartialApplication) -> None:
        raise NotImplementedError()

    @ui.select(row=0)
    async def select(self, interaction: discord.Interaction[BotCore], select: ui.Select) -> None:
        self.stop()

        app = next(app for app in self.current_page_apps if app.id == select.values[0])
        await self.callback(interaction, app)

    @ui.button(emoji="⬅️", style=ButtonStyle.secondary, row=1)
    async def previous_page(self, interaction: discord.Interaction[BotCore], _) -> None:
        self.current_page -= 1
        self._update_state()
        await interaction.response.edit_message(embed=self.embed, view=self)

    @ui.button(emoji="➡️", style=ButtonStyle.secondary, row=1)
    async def next_page(self, interaction: discord.Interaction[BotCore], _) -> None:
        self.current_page += 1
        self._update_state()
        await interaction.response.edit_message(embed=self.embed, view=self)


class SelectApplicationToManageView(_BaseSelectApplicationView):
    def __init__(
        self,
        t: Translator,
        client: Client,
        apps: list[PartialApplication],
        *,
        page: int = 1,
        timeout: float | None = 300,
    ) -> None:
        super().__init__(apps, page=page, timeout=timeout)

        self.t: Translator = t
        self.client: Client = client

        self.select.placeholder = t("apps.select_app.placeholder")

    @property
    def embed(self) -> DefaultEmbed:
        t = self.t
        return DefaultEmbed(
            title=t("apps.select_app.title"),
            description=t("apps.select_app.description"),
        ).set_footer(text=t("apps.select_app.footer", self.current_page, self.max_page))

    async def callback(self, interaction: discord.Interaction[BotCore], partial_app: PartialApplication) -> None:
        t = self.t
        # Get full app and status.
        embed = DefaultEmbed(description=f"⌛ **|** {t('apps.loading')}")

        await interaction.response.edit_message(embed=embed, view=None)

        # Get full app infos.
        app = await self.client.get_app(partial_app.id)
        # Get status and update internal cache.
        status = await app.get_status()
        if status.running:
            with suppress(squarecloud.NotFound):
                await app.get_logs()

        view = ManageApplicationView(t, app)
        await interaction.edit_original_response(embed=view.embed, view=view)


class ApplicationSettingsView(BaseView):
    def __init__(
        self,
        parent: ManageApplicationView,
        *,
        timeout: float | None = 300,
    ):
        super().__init__(timeout=timeout)

        self.t: Translator = parent.t
        self.app: Application = parent.app
        self.parent: ManageApplicationView = parent

        self.delete.label = self.t("apps.buttons.delete_app")
        self.back.label = self.t("common.back")

    @ui.button(emoji="🗑️", style=ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction[BotCore], _) -> None:
        t = self.t

        embed = DefaultEmbed(description=f"⚠️ **|** {t('apps.delete_confirm')}")
        view = ConfirmView(self.t, timeout=30)

        await interaction.response.edit_message(embed=embed, view=view)

        await view.wait()

        # Timeout
        if view.value is None:
            await interaction.edit_original_response(embed=self.parent.embed, view=self)
            return

        interaction = view.interaction

        # Cancel
        if not view.value:
            await interaction.response.edit_message(embed=self.parent.embed, view=self)
            return

        view.disable_all()
        await interaction.response.edit_message(view=view)

        await self.app.delete()

        client = self.app._client
        apps = await client.get_all_apps()

        if not apps:
            await interaction.delete_original_response()
            return

        view = SelectApplicationToManageView(self.t, client, apps)

        await interaction.edit_original_response(embed=view.embed, view=view)

    @ui.button(emoji="◀️", style=ButtonStyle.secondary, row=4)
    async def back(self, interaction: discord.Interaction[BotCore], _) -> None:
        # Back to parent view and stop self.
        view = type(self.parent)(self.t, self.parent.app)
        self.stop()

        await interaction.response.edit_message(embed=view.embed, view=view)


class ManageApplicationView(BaseView):
    def __init__(
        self,
        t: Translator,
        app: Application,
        *,
        timeout: float | None = 600,
    ):
        super().__init__(timeout=timeout)

        self.t: Translator = t
        self.app: Application = app

        self.logs.label = t("apps.buttons.logs")
        self.backup.label = t("apps.buttons.backup")
        self.settings.label = t("apps.buttons.settings")
        self.back.label = t("common.back")

        self._update_state()

    def _update_state(self) -> None:
        # Reset
        self.enable_all()

        app = self.app
        status = app.status
        assert status

        # Update buttons state.
        self.start.disabled = status.running
        self.restart.disabled = not status.running
        self._stop.disabled = not status.running
        self.logs.disabled = not status.running

        # Refresh timeout.
        self._refresh_timeout()

    async def _update(self) -> None:
        # Update application information cache.
        # Wait between each request to avoid ratelimit.
        self.app = await self.app._client.get_app(self.app.id)
        status = await self.app.get_status()
        if status.running:
            with suppress(squarecloud.NotFound):
                await self.app.get_logs()

    @property
    def embed(self) -> DefaultEmbed:
        t = self.t
        app = self.app

        embed = DefaultEmbed(title=app.name, description=app.description, timestamp=utcnow())

        if app.domain is not None:
            embed.url = "https://" + app.domain

        assert (status := app.status)

        # Defines the embed color according to the application status.
        if status.running:
            embed.color = discord.Color.brand_green()
        else:
            embed.color = discord.Color.brand_red()

        if status.uptime is not None:
            embed.add_field(name=t("apps.status.uptime"), value=format_dt(status.uptime, "R"))
        embed.add_field(name=t("apps.status.cpu"), value=status.cpu)
        embed.add_field(name=t("apps.status.ram"), value=status.ram)
        embed.add_field(name=t("apps.status.storage"), value=status.storage)
        # To keep the message shorter, avoid showing irrelevant information.
        if status.running:
            embed.add_field(name=t("apps.status.network_now"), value=str(status.network.now))
        embed.add_field(name=t("apps.status.network_total"), value=str(status.network.total))
        if status.requests:
            embed.add_field(name=t("apps.status.requests"), value=status.requests)
        if status.running and app.logs:
            # Last 5 lines or 512 chars.
            lines = app.logs.splitlines()[:-5:]
            logs = ""
            for line in lines:
                if len(logs + line) > 512:
                    break
                logs += line + "\n"

            if not logs and lines:
                logs = lines[-1][:512]

            embed.add_field(name=t("apps.last_logs"), value=f"```\n{logs}```", inline=False)

        return embed

    @ui.button(emoji="▶️", style=ButtonStyle.success, row=0)
    async def start(self, interaction: discord.Interaction[BotCore], _) -> None:
        self.disable_all()
        await interaction.response.edit_message(view=self)
        await self.app.start()
        await self._update()
        self._update_state()
        await interaction.edit_original_response(embed=self.embed, view=self)

    @ui.button(emoji="🔄", style=ButtonStyle.primary, row=0)
    async def restart(self, interaction: discord.Interaction[BotCore], _) -> None:
        self.disable_all()
        await interaction.response.edit_message(view=self)
        await self.app.restart()
        await self._update()
        self._update_state()
        await interaction.edit_original_response(embed=self.embed, view=self)

    @ui.button(emoji="⏹️", style=ButtonStyle.danger, row=0)
    async def _stop(self, interaction: discord.Interaction[BotCore], _) -> None:
        self.disable_all()
        await interaction.response.edit_message(view=self)
        await self.app.stop()
        await self._update()
        self._update_state()
        await interaction.edit_original_response(embed=self.embed, view=self)

    @ui.button(emoji="📄", style=ButtonStyle.secondary, row=1)
    async def logs(self, interaction: discord.Interaction[BotCore], _) -> None:
        self.disable_all()
        await interaction.response.edit_message(view=self)

        try:
            logs = await self.app.get_logs()
        except squarecloud.NotFound:
            # Ignore
            self._update_state()
            await interaction.edit_original_response(embed=self.embed, view=self)
            return

        lines = len(logs.splitlines())

        if lines > 30 or len(logs) > 2000:
            buffer = io.StringIO(logs)
            buffer.seek(0)
            file = discord.File(
                buffer,  # type: ignore
                f"logs-{self.app.name}.txt",
            )
            await interaction.followup.send(file=file, ephemeral=True)
        else:
            embed = DefaultEmbed(description=f"```\n{logs}```")
            await interaction.followup.send(embed=embed, ephemeral=True)

        await asyncio.sleep(5)
        self._update_state()
        await interaction.edit_original_response(embed=self.embed, view=self)

    @ui.button(emoji="☁️", style=ButtonStyle.secondary, row=1)
    async def backup(self, interaction: discord.Interaction[BotCore], _) -> None:
        t = self.t
        self.disable_all()
        await interaction.response.edit_message(view=self)

        backup_url = await self.app.get_backup_url()
        embed = DefaultEmbed(description=t("apps.backup.success"))
        view = ui.View().add_item(ui.Button(label=t("apps.backup.download"), url=backup_url))
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        await asyncio.sleep(5)
        self._update_state()
        await interaction.edit_original_response(embed=self.embed, view=self)

    @ui.button(emoji="⚙️", style=ButtonStyle.secondary, row=2)
    async def settings(self, interaction: discord.Interaction[BotCore], _) -> None:
        view = ApplicationSettingsView(self)
        await interaction.response.edit_message(view=view)
        self.stop()

    @ui.button(emoji="◀️", style=ButtonStyle.secondary, row=4)
    async def back(self, interaction: discord.Interaction[BotCore], _) -> None:
        self.stop()

        self.disable_all()
        await interaction.response.edit_message(view=self)

        client = self.app._client
        apps = await client.get_all_apps()
        view = SelectApplicationToManageView(self.t, client, apps)

        await interaction.edit_original_response(embed=view.embed, view=view)


class UploadedApplicationView(BaseView):
    def __init__(self, t: Translator, client: Client, app: UploadedApplication, *, timeout: float | None = 300):
        super().__init__(timeout=timeout)
        self.t = t
        self.client = client
        self.app = app

        self.add_item(ui.Button(label=t("up.go_to_dashboard"), url=f"https://squarecloud.app/dashboard/app/{app.id}"))
        self.manage_app.label = t("up.manage_app")

    @ui.button(emoji="⚙️", style=ButtonStyle.blurple)
    async def manage_app(self, interaction: discord.Interaction[BotCore], _) -> None:
        self.stop()

        self.disable_all()
        await interaction.response.edit_message(view=self)

        app = await self.client.get_app(self.app.id)
        await app.get_status()

        view = ManageApplicationView(self.t, app)

        await interaction.edit_original_response(embed=view.embed, view=view)


class SelectApplicationToCommitView(_BaseSelectApplicationView):
    def __init__(
        self,
        t: Translator,
        client: Client,
        apps: list[PartialApplication],
        file: squarecloud.File,
        *,
        restart: bool | None = None,
        page: int = 1,
        timeout: float | None = 300,
    ) -> None:
        super().__init__(apps, page=page, timeout=timeout)

        self.t: Translator = t
        self.client: Client = client
        self.file: squarecloud.File = file
        self.restart: bool | None = restart

        self.select.placeholder = t("commit.select_app.placeholder")

    @property
    def embed(self) -> DefaultEmbed:
        t = self.t
        return DefaultEmbed(
            title=t("commit.select_app.title"),
            description=t("commit.select_app.description"),
        ).set_footer(text=t("commit.select_app.footer", self.current_page, self.max_page))

    async def callback(self, interaction: discord.Interaction[BotCore], partial_app: PartialApplication) -> None:
        t = self.t

        embed = DefaultEmbed(description=f'⌛ **|** {t("commit.loading")}')

        await interaction.response.edit_message(embed=embed, view=None)

        try:
            await self.client.commit(id=partial_app.id, file=self.file, restart=self.restart)
        except squarecloud.HTTPException:
            raise GenericError(t("commit.error"), interaction)

        embed = DefaultEmbed(description=f'✅ **|** {t("commit.success")}')
        await interaction.edit_original_response(embed=embed)
