from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import statistics


__all__ = ("ServiceStatistics",)


class ServiceStatistics:
    """Object that represents SquareCloud statistics.

    Attributes:
        worker: The number of the worker that handled the request.
        users: The number of users registered in the service.
        apps: The number of apps running in the service.
        websites: The number of websites running in the service.
        ping: The average ping of the service..
    """

    __slots__ = (
        "worker",
        "users",
        "apps",
        "websites",
        "ping",
    )

    def __init__(self, data: statistics.ServiceStatistics) -> None:
        self.worker: int = data["worker"]
        self.users: int = data["statistics"]["users"]
        self.apps: int = data["statistics"]["apps"]
        self.websites: int = data["statistics"]["websites"]
        self.ping: int = data["statistics"]["ping"]

    def __repr__(self) -> str:
        attrs = (
            "worker",
            "users",
            "apps",
            "websites",
            "ping",
        )
        fmt = " ".join(f"{a}={getattr(self, a)!r}" for a in attrs)
        return f"<{self.__class__.__name__} {fmt}>"
