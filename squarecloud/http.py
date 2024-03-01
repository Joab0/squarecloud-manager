from __future__ import annotations

import logging
from typing import Any, ClassVar
from urllib.parse import quote

import httpx

from .errors import AuthenticationFailure, HTTPException, NotFound
from .types import application, statistics, user

_log = logging.getLogger(__name__)


class Route:
    BASE: ClassVar[str] = "https://api.squarecloud.app/v2"

    def __init__(self, method: str, path: str, **parameters: Any) -> None:
        self.path: str = path
        self.method: str = method
        url = self.BASE + self.path
        if parameters:
            url = url.format_map({k: quote(v) if isinstance(v, str) else v for k, v in parameters.items()})
        self.url: str = url


class HTTPClient:
    """HTTP client responsible for sending http requests to SqaureCloud."""

    def __init__(self, api_key: str | None = None, client: httpx.AsyncClient | None = None) -> None:
        self.__client = client or httpx.AsyncClient(timeout=60.0)  # Some routes require more time to respond
        self.__api_key = api_key

    async def request(self, route: Route, **kwargs: Any) -> Any:
        method, url = route.method, route.url

        headers = {}

        if self.__api_key is not None:
            headers["Authorization"] = self.__api_key

        if "json" in kwargs:
            headers["Content-Type"] = "application/json"

        kwargs["headers"] = headers

        request = self.__client.build_request(method, url, **kwargs)
        response = await self.__client.send(request)
        _log.debug(f"{method} {url} with {kwargs.get('json', '{}')} has retuned {response.status_code}")

        if response.headers["content-type"] == "application/json; charset=utf-8":
            data = response.json()
        else:
            data = None

        match response.status_code:
            case _ as status if 200 <= status < 300:
                _log.debug(f"{method} {url} has received {data}")
                return data.get("response") if data else data
            case 401:
                exc = AuthenticationFailure
            case 404:
                exc = NotFound
            case _:
                exc = HTTPException

        _log.error(f"Error in {method} {url}: {response.status_code} returned: {data}")
        raise exc(response)

    # Service
    async def get_service_statistics(self) -> statistics.ServiceStatistics:
        data = await self.request(Route("GET", "/service/statistics"))
        return data

    # User
    async def me(self) -> user.UserData:
        data = await self.request(Route("GET", "/user"))
        return data

    # Applications
    async def get_app(self, id: str) -> application.Application:
        data = await self.request(Route("GET", "/apps/{app_id}", app_id=id))
        return data

    async def get_app_status(self, id: str) -> application.ApplicationStatus:
        data = await self.request(Route("GET", "/apps/{app_id}/status", app_id=id))
        return data

    async def get_all_apps_status(self) -> list[application.PartialApplicationStatus]:
        data = await self.request(Route("GET", "/apps/all/status"))
        return data

    async def get_app_logs(self, id: str) -> application.ApplicationLogs:
        data = await self.request(Route("GET", "/apps/{app_id}/logs", app_id=id))
        return data

    async def start_app(self, id: str) -> None:
        data = await self.request(Route("POST", "/apps/{app_id}/start", app_id=id))
        return data

    async def restart_app(self, id: str) -> None:
        data = await self.request(Route("POST", "/apps/{app_id}/restart", app_id=id))
        return data

    async def stop_app(self, id: str) -> None:
        data = await self.request(Route("POST", "/apps/{app_id}/stop", app_id=id))
        return data

    async def backup(self, id: str) -> application.ApplicationBackup:
        data = await self.request(Route("GET", "/apps/{app_id}/backup", app_id=id))
        return data
