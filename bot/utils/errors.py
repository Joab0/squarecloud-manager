from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from discord import Interaction

    from ..core import BotCore


class GenericError(Exception):
    """Bot generic error."""

    def __init__(
        self,
        message: str | None = None,
        interaction: Interaction[BotCore] | None = None,
    ) -> None:
        # If interaction is not original.
        self.message = message
        self.interaction = interaction
        super().__init__(message)
