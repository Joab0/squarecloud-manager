from __future__ import annotations

from typing_extensions import TypedDict


class Statistics(TypedDict):
    users: int
    apps: int
    websites: int
    ping: int


class ServiceStatistics(TypedDict):
    worker: int
    statistics: Statistics
