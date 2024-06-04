from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar
from urllib.parse import quote

import aiohttp

from .errors import AuthenticationFailure, HTTPException, NotFound
from .types import application, statistics, user

if TYPE_CHECKING:
    from .file import File

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

    def __init__(self, api_key: str | None = None, session: aiohttp.ClientSession | None = None) -> None:
        self.__session = session or None
        self.__api_key = api_key

    def __del__(self) -> None:
        # Close aiohttp session
        import asyncio

        if self.__session is not None and not self.__session.closed:
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self.__session.close())
            except RuntimeError:
                asyncio.run(self.__session.close())

    async def request(self, route: Route, **kwargs: Any) -> Any:
        # Can only be instantiated in an async function.
        if self.__session is None:
            self.__session = aiohttp.ClientSession()

        method, url = route.method, route.url

        headers = {}

        if self.__api_key is not None:
            headers["Authorization"] = self.__api_key

        kwargs["headers"] = headers

        if "file" in kwargs:
            file: File = kwargs.pop("file")

            form = aiohttp.FormData()
            form.add_field("file", file.fp, filename=file.filename)
            kwargs["data"] = form

        async with self.__session.request(method, url, **kwargs) as response:
            _log.debug(f"{method} {url} with {kwargs.get('json', '{}')} has retuned {response.status}")

            try:
                data = await response.json()
            except aiohttp.ContentTypeError:
                data = None

            match response.status:
                case _ as status if 200 <= status < 300:
                    _log.debug(f"{method} {url} has received {data}")

                    # For some reason the API returns 200 even if there is an error.
                    # In the upload route for example.
                    if data and data.get("status") == "error":
                        raise HTTPException(response, data)  # type: ignore

                    return data.get("response") if data else data
                case 401:
                    exc = AuthenticationFailure
                case 404:
                    exc = NotFound
                case _:
                    exc = HTTPException

            _log.error(f"Error in {method} {url}: {response.status} returned: {data}")
            raise exc(response, data or {})

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

    async def upload(self, file: File) -> application.UploadedApplication:
        file.fp.seek(0)
        data = await self.request(Route("POST", "/apps/upload"), file=file)
        return data

    async def delete_app(self, id: str) -> None:
        await self.request(Route("DELETE", "/apps/{app_id}/delete", app_id=id))

    async def commit(self, id: str, file: File, restart: bool) -> None:
        file.fp.seek(0)
        await self.request(
            Route("POST", "/apps/{app_id}/commit?restart={restart}", app_id=id, restart=restart), file=file
        )
