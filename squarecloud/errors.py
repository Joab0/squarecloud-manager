from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aiohttp import ClientResponse


__all__ = ("SquareCloudException", "HTTPException", "AuthenticationFailure", "NotFound")


class SquareCloudException(Exception):
    """Base exception."""


class HTTPException(SquareCloudException):
    """Exception raised when an HTTP operation fails."""

    def __init__(self, response: ClientResponse, data: dict[str, Any]) -> None:
        self.response: ClientResponse = response

        self.status: int = response.status
        self.code: str = data["code"]

        super().__init__(f"{self.status} {self.code}")


class AuthenticationFailure(HTTPException):
    """Exception raised when the client is not authorized to access a certain route."""


class NotFound(HTTPException):
    """Exception raised when something is not found."""
