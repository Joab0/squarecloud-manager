from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from .application import PartialApplication

if TYPE_CHECKING:
    from .types import user


__all__ = ("User", "Plan")


class PlanMemory:
    """Object that represents the memory of a user's plan.

    Attributes:
        limit: Memory limit.
        available: Memory available.
        user: Memory used.
    """

    __slots__ = (
        "limit",
        "available",
        "used",
    )

    def __init__(self, data: user.PlanMemory) -> None:
        self.limit: int = data["limit"]
        self.available: int = data["available"]
        self.used: int = data["used"]

    def __repr__(self) -> str:
        attrs = (
            "limit",
            "available",
            "used",
        )
        fmt = " ".join(f"{a}={getattr(self, a)!r}" for a in attrs)
        return f"<{self.__class__.__name__} {fmt}>"


class Plan:
    """Object that represents the user's plan.

    Attributes:
        name: Plan name
        memory: Plan memory info.
        duration: Plan expiration date.
    """

    __slots__ = (
        "name",
        "memory",
        "duration",
    )

    def __init__(self, data: user.Plan) -> None:
        self.name: str = data["name"]
        self.memory: PlanMemory = PlanMemory(data["memory"])
        self.duration: datetime | None = datetime.fromtimestamp(data["duration"] // 1000) if data["duration"] else None

    def __repr__(self) -> str:
        attrs = (
            "name",
            "memory",
            "duration",
        )
        fmt = " ".join(f"{a}={getattr(self, a)!r}" for a in attrs)
        return f"<{self.__class__.__name__} {fmt}>"


class User:
    """Object that represents user.

    Attributes:
        id: The user's ID.
        tag: The user's tag.
        email: The user's email.
        plan: User plan info.
        apps: List of user application.
    """

    __slots__ = (
        "id",
        "tag",
        "email",
        "plan",
        "apps",
    )

    def __init__(self, data: user.UserData) -> None:
        self.id: str = data["user"]["id"]
        self.tag: str = data["user"]["tag"]
        self.email: str = data["user"]["email"]
        self.plan: Plan = Plan(data["user"]["plan"])
        self.apps: list[PartialApplication] = [PartialApplication(app) for app in data["applications"]]

    def __repr__(self) -> str:
        attrs = (
            "id",
            "tag",
            "email",
            "plan",
            "applications",
        )
        fmt = " ".join(f"{a}={getattr(self, a)!r}" for a in attrs)
        return f"<{self.__class__.__name__} {fmt}>"
