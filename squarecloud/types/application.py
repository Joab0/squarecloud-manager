from __future__ import annotations

from typing import Literal

from typing_extensions import NotRequired, TypedDict

VersionType = Literal["recommended", "latest"]


# Returned in /user
class PartialApplication(TypedDict):
    id: str
    tag: str
    desc: NotRequired[str]
    ram: int
    lang: str
    cluster: str
    isWebsite: bool


class Application(TypedDict):
    id: str
    name: str
    desc: NotRequired[str]
    cluster: str
    ram: int
    language: str
    domain: NotRequired[str]
    custom: NotRequired[str]
    isWebsite: bool
    gitIntegration: bool


class ApplicationStatusNetwork(TypedDict):
    total: str
    now: str


class ApplicationStatus(TypedDict):
    cpu: str
    ram: str
    status: str
    running: bool
    storage: str
    network: ApplicationStatusNetwork
    requests: int
    uptime: int | None


class PartialApplicationStatus(TypedDict):
    id: str
    cpu: NotRequired[str]
    ram: NotRequired[str]
    running: bool


class ApplicationLogs(TypedDict):
    logs: str


class ApplicationBackup(TypedDict):
    downloadURL: str


class ApplicationLanguage(TypedDict):
    name: str
    version: VersionType


class UploadedApplication(TypedDict):
    id: str
    tag: str
    description: NotRequired[str]
    subdomain: str | None
    ram: int
    cpu: int
    language: ApplicationLanguage
