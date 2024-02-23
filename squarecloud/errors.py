from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from httpx import Response


__all__ = ("SquareCloudException", "HTTPException", "AuthenticationFailure", "NotFound")


class SquareCloudException(Exception):
    """Base exception."""


class HTTPException(SquareCloudException):
    """Exception thrown when an HTTP operation fails."""

    def __init__(self, response: Response) -> None:
        self.response: Response = response
        self.status: int = response.status_code

        data = response.json()
        self.code: str = data["code"]

        super().__init__(f"{self.status} {self.code}")


class AuthenticationFailure(HTTPException):
    """Exception thrown when the client is not authorized to access a certain route."""


class NotFound(HTTPException):
    """Exception thrown when something is not found."""
