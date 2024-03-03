from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Self

from .types import application

if TYPE_CHECKING:
    from .client import Client
    from .types.application import VersionType

# Regex to extract network information. The api returns formatted.
NETWORK_RE = re.compile(r"\d+(?:\.\d+)?\s*[KMGT]?B")


__all__ = (
    "PartialApplication",
    "Application",
    "ApplicationStatus",
)


class PartialApplication:
    """Partial representation of an application.

    Attributes:
        id: The application's ID.
        name: The application's name.
        description: The application's description.
        ram: The application's RAM usage.
        lang: The application's language.
        cluster: The application's cluster.
        is_website: Indicates whether the application is a website.
    """

    __slots__ = (
        "id",
        "name",
        "description",
        "ram",
        "lang",
        "cluster",
        "is_website",
    )

    def __init__(self, data: application.PartialApplication) -> None:
        self.id: str = data["id"]
        self.name: str = data["tag"]
        self.description: str | None = data.get("desc")
        self.ram: int = data["ram"]
        self.lang: str = data["lang"]
        self.cluster: str = data["cluster"]
        self.is_website: bool = data["isWebsite"]

    def __repr__(self) -> str:
        attrs = (
            "id",
            "name",
            "description",
            "ram",
            "lang",
            "cluster",
            "is_website",
        )
        fmt = " ".join(f"{a}={getattr(self, a)!r}" for a in attrs)
        return f"<{self.__class__.__name__} {fmt}>"


class NetworkUsage:
    """Object representing network usage.

    Attributes:
        up: Amount of data sent over the network.
        down: Amount of data received over the network.
    """

    __all__ = ("up", "down")

    def __init__(self, up: str, down: str) -> None:
        self.up: str = up
        self.down: str = down

    def __str__(self) -> str:
        return f"{self.up} ↑ {self.down} ↓"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} up={self.up!r} down={self.down!r}>"

    def __bool__(self) -> bool:
        return not (self.up == "0KB" and self.down == "0KB")

    @classmethod
    def from_str(cls, string: str) -> Self:
        """Creates an instance of the class from a formatted string."""
        matches: list[str] = [match.replace(" ", "") for match in NETWORK_RE.findall(string)]
        return cls(*matches)


class ApplicationNetworkUsage:
    """Object that represents the application's network usage.

    Attributes:
        total: The application's total network usage.
        now: application's now network usage.
    """

    __all__ = ("total", "now")

    def __init__(self, data: application.ApplicationStatusNetwork) -> None:
        self.total: NetworkUsage = NetworkUsage.from_str(data["total"])
        self.now: NetworkUsage = NetworkUsage.from_str(data["now"])

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} total={self.total!r} now={self.now!r}>"


class ApplicationStatus:
    def __init__(self, data: application.ApplicationStatus) -> None:
        self.cpu: str = data["cpu"]
        self.ram: str = data["ram"]
        self.status: str = data["status"]
        self.running: bool = data["running"]
        self.storage: str = data["storage"]
        self.network: ApplicationNetworkUsage = ApplicationNetworkUsage(data["network"])
        self.requests: int = data["requests"]
        self.uptime: datetime | None = (
            datetime.fromtimestamp(data["uptime"] / 1000).astimezone(timezone.utc) if data["uptime"] else None
        )

    def __repr__(self) -> str:
        attrs = (
            "cpu",
            "ram",
            "status",
            "running",
            "storage",
            "network",
            "requests",
            "uptime",
        )
        fmt = " ".join(f"{a}={getattr(self, a)!r}" for a in attrs)
        return f"<{self.__class__.__name__} {fmt}>"


class PartialApplicationStatus:
    """An object that represents the partial status of an application.

    Attributes:
        id: The application ID.
        cpu: The CPU usage of the application.
        ram: The RAM usage of the application.
        running: Indicates whether the application is currently running.
    """

    __slots__ = (
        "id",
        "cpu",
        "ram",
        "running",
    )

    def __init__(self, data: application.PartialApplicationStatus) -> None:
        self.id: str = data["id"]
        self.cpu: str | None = data.get("cpu")
        self.ram: str | None = data.get("ram")
        self.running: bool = data["running"]

    def __repr__(self) -> str:
        attrs = (
            "id",
            "cpu",
            "ram",
            "running",
        )
        fmt = " ".join(f"{a}={getattr(self, a)!r}" for a in attrs)
        return f"<{self.__class__.__name__} {fmt}>"


class Application:
    """Object that represents an application.

    Attributes:
        id: The application's ID.
        name: The application's name.
        description: The application's description.
        cluster: The application's cluster.
        ram: The application's RAM usage in MB.
        language: The application's programming language.
        domain: The application's domain (null if not applicable).
        custom: Custom information about the application (null if not applicable).
        is_website: Indicates whether the application is a website.
        git_integration: if the application has git integration enabled.
        status: Application status cache. Filled after calling get_status() method.
        logs: Application logs cache. Filled after calling get_logs() method.
    """

    __slots__ = (
        "id",
        "name",
        "description",
        "cluster",
        "ram",
        "language",
        "domain",
        "custom",
        "is_website",
        "git_integration",
        "_client",
        "_status",
        "_logs",
    )

    def __init__(self, data: application.Application, client: Client) -> None:
        self.id: str = data["id"]
        self.name: str = data["name"]
        self.description: str | None = data.get("desc")
        self.cluster: str = data["cluster"]
        self.ram: int = data["ram"]
        self.language: str = data["language"]
        self.domain: str | None = data.get("domain")
        self.custom: str | None = data.get("custom")
        self.is_website: bool = data["isWebsite"]
        self.git_integration: bool = data["gitIntegration"]

        self._status: ApplicationStatus | None = None
        self._logs: str | None = None
        self._client: Client = client

    def __repr__(self) -> str:
        attrs = (
            "id",
            "name",
            "description",
            "cluster",
            "ram",
            "language",
            "domain",
            "custom",
            "is_website",
            "git_integration",
        )
        fmt = " ".join(f"{a}={getattr(self, a)!r}" for a in attrs)
        return f"<{self.__class__.__name__} {fmt}>"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self)) and self.id == other.id

    @property
    def status(self) -> ApplicationStatus | None:
        return self._status

    @property
    def logs(self) -> str | None:
        return self._logs

    def clear(self) -> None:
        """Clear internal cache."""
        self._status = None
        self._logs = None

    async def get_status(self) -> ApplicationStatus:
        """Get status of this application."""
        status = await self._client.get_app_status(self.id)
        self._status = status
        return status

    async def get_logs(self) -> str:
        """Get logs of this application."""
        logs = await self._client.get_app_logs(self.id)
        self._logs = logs
        return logs

    async def start(self) -> None:
        """Start this application."""
        await self._client.start_app(self.id)

    async def restart(self) -> None:
        """Restart this application."""
        await self._client.restart_app(self.id)

    async def stop(self) -> None:
        """Stop this application."""
        await self._client.stop_app(self.id)

    async def get_backup_url(self) -> str:
        """Returns a URL to download the backup of the application files."""
        url = await self._client.get_backup_url(self.id)
        return url


class ApplicationLanguage:
    """Object that represents the application's programming language.

    Attributes:
        name: Programming language name.
        name: Programming language version. Must be `recommended` or `latest`.
    """

    __slots__ = ("name", "version")

    def __init__(self, data: application.ApplicationLanguage) -> None:
        self.name: str = data["name"]
        self.version: VersionType = data["version"]

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r} version={self.version!r}>"


class UploadedApplication:
    """Object returned when upload an application to Square Cloud.

    Attributes:
        id: The ID of the uploaded application.
        name: The name of the uploaded application.
        description: The description of the uploaded application.
        subdomain: The subdomain of the uploaded application (null if not applicable).
        ram: The RAM usage of the uploaded application in MB.
        cpu: The CPU usage of the uploaded application.
    """

    __all__ = (
        "id",
        "name",
        "description",
        "subdomain",
        "ram",
        "cpu",
        "language",
    )

    def __init__(self, data: application.UploadedApplication) -> None:
        self.id: str = data["id"]
        self.name: str = data["tag"]
        self.description: str | None = data.get("description")
        self.subdomain: str | None = data["subdomain"]
        self.ram: int = data["ram"]
        self.cpu: int = data["cpu"]
        self.language: ApplicationLanguage = ApplicationLanguage(data["language"])

    def __repr__(self) -> str:
        attrs = (
            "id",
            "name",
            "description",
            "subdomain",
            "ram",
            "cpu",
            "language",
        )
        fmt = " ".join(f"{a}={getattr(self, a)!r}" for a in attrs)
        return f"<{self.__class__.__name__} {fmt}>"
