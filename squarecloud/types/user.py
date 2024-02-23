from __future__ import annotations

from typing_extensions import TypedDict

from .application import PartialApplication


class PlanMemory(TypedDict):
    limit: int
    available: int
    used: int


class Plan(TypedDict):
    name: str
    memory: PlanMemory
    duration: int | None


class User(TypedDict):
    id: str
    tag: str
    email: str
    plan: Plan


class UserData(TypedDict):
    user: User
    applications: list[PartialApplication]
