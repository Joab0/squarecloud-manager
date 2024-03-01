from __future__ import annotations

from .application import (
    Application,
    ApplicationStatus,
    PartialApplication,
    PartialApplicationStatus,
)
from .http import HTTPClient
from .statistics import ServiceStatistics
from .user import User

__all__ = ("Client",)


class Client:
    """Client to interact with Square Cloud API."""

    # The api key may be none. This is useful for public routes.
    def __init__(self, api_key: str | None = None, *, http_client: HTTPClient | None = None) -> None:
        self._http = http_client or HTTPClient(api_key)

    # Public
    async def get_services_statistics(self) -> ServiceStatistics:
        """Returns statistics about the service.."""
        data = await self._http.get_service_statistics()
        return ServiceStatistics(data)

    # User
    async def me(self) -> User:
        """Get information about your account."""
        data = await self._http.me()
        return User(data)

    # Applications
    async def get_app(self, id: str) -> Application:
        """Get an application by ID.

        Args:
            id: The application's ID.
        """
        data = await self._http.get_app(id)
        return Application(data, self)

    async def get_all_apps(self) -> list[PartialApplication]:
        """A helper function to return all user applications.
        This is equivalent to:

        ```py
        async def get_all_apps():
            me = await client.me()
            apps = me.apps
            return apps
        ```
        """
        me = await self.me()
        return me.apps

    async def get_app_status(self, id: str) -> ApplicationStatus:
        """Get application status.

        Args:
            id: The application's ID.
        """
        data = await self._http.get_app_status(id)
        return ApplicationStatus(data)

    async def get_all_apps_status(self) -> list[PartialApplicationStatus]:
        """Get all applications status."""
        data = await self._http.get_all_apps_status()
        return [PartialApplicationStatus(d) for d in data]

    async def get_app_logs(self, id: str) -> str:
        """Collect the latest logs from your application.

        Args:
            id: The application's ID.
        """
        data = await self._http.get_app_logs(id)
        return data["logs"]

    async def start_app(self, id: str) -> None:
        """Start the application.

        Args:
            id: The application's ID.
        """
        await self._http.start_app(id)

    async def restart_app(self, id: str) -> None:
        """Restart the application.

        Args:
            id: The application's ID.
        """
        await self._http.restart_app(id)

    async def stop_app(self, id: str) -> None:
        """Stop the application.

        Args:
            id: The application's ID.
        """
        await self._http.stop_app(id)

    async def get_backup_url(self, id: str) -> str:
        """Returns a URL to download the backup of the application files.

        Args:
            id: The application's ID.
        """
        data = await self._http.backup(id)
        return data["downloadURL"]
