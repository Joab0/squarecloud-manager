from __future__ import annotations

from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from typing_extensions import NotRequired, TypedDict

    from .types.application import VersionType

    class _ConfigFile(TypedDict):
        main: str
        memory: int
        version: VersionType
        display_name: str
        subdomain: NotRequired[str]
        description: NotRequired[str]
        autorestart: NotRequired[bool]
        start: NotRequired[str]


__all__ = ("ConfigFile",)


class ConfigFile:
    """An object representing the Square Cloud configuration file.

    Attributes:
        main: Main file of your application.
        memory: Amount of RAM memory.
        version: Version of your application. Can be `recommended` or `latest`.
        display_name: Name of application.
        subdomain: If you are sending a website.
        description: Description of your application.
        autorestart: Restart your application if it crashes.
        start: Custom startup command.
    """

    __slots__ = (
        "main",
        "memory",
        "version",
        "display_name",
        "subdomain",
        "description",
        "autorestart",
        "start",
    )

    def __init__(
        self,
        main: str,
        memory: int,
        version: VersionType,
        display_name: str,
        subdomain: str | None = None,
        description: str | None = None,
        autorestart: bool | None = None,
        start: str | None = None,
    ) -> None:
        if not isinstance(memory, int):
            raise TypeError(f"The memory parameter must be int not {memory.__class__.__name__}.")

        if version not in ("recommended", "latest"):
            raise TypeError("The version parameter must be int 'recommended' or 'latest'.")

        if autorestart is not None and not isinstance(autorestart, bool):
            raise TypeError(f"The autorestart parameter must be bool not {autorestart.__class__.__name__}.")

        self.main: str = main
        self.memory: int = memory
        self.version: VersionType = version
        self.display_name: str = display_name
        self.subdomain: str | None = subdomain
        self.description: str | None = description
        self.autorestart: bool | None = autorestart
        self.start: str | None = start

    def __str__(self) -> str:
        data = self.to_dict()
        ret = ""

        for key, value in data.items():
            ret += f"{key.upper()}={value}\n"

        return ret.strip()

    def __repr__(self) -> str:
        attrs = self.to_dict().keys()
        fmt = " ".join(f"{a}={getattr(self, a)!r}" for a in attrs)
        return f"<{self.__class__.__name__} {fmt}>"

    def to_dict(self) -> _ConfigFile:
        """Returns a config file as dict."""
        data: _ConfigFile = {
            "main": self.main,
            "memory": self.memory,
            "version": self.version,
            "display_name": self.display_name,
        }

        if self.subdomain is not None:
            data["subdomain"] = self.subdomain

        if self.description is not None:
            data["description"] = self.description

        if self.autorestart is not None:
            data["autorestart"] = self.autorestart

        if self.start is not None:
            data["start"] = self.start

        return data

    @classmethod
    def from_str(cls, value: str) -> Self:
        """Create an instance of the class from a configuration file."""
        fields: dict[str, str] = {}

        # Converts to a dict.
        for line in value.splitlines():
            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            fields[key.lower()] = value

        # Adjusts the type of keys.
        try:
            data: _ConfigFile = {
                # Required
                "main": fields["main"],
                "memory": int(fields["memory"]),
                "version": fields["version"],  # type: ignore
                "display_name": fields["display_name"],
                # Not required
                "subdomain": fields.get("subdomain"),
                "description": fields.get("description"),
                "autorestart": fields.get("autorestart", "false").lower() == "true",
                "start": fields.get("start"),
            }
        except KeyError as e:
            forget = e.args[0].upper()
            raise ValueError(f"Bad config file. You forget {forget!r} key.", forget)

        return cls(**data)
