from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from discord import Color, Embed
from discord.colour import Colour
from discord.utils import MISSING

if TYPE_CHECKING:
    from datetime import datetime

    from discord.types.embed import EmbedType


class DefaultEmbed(Embed):
    """Default embed for bot messages."""

    _default_color: ClassVar[Colour | None] = None

    def __init__(
        self,
        *,
        color: int | Colour | None = MISSING,
        title: Any | None = None,
        type: EmbedType = "rich",
        url: Any | None = None,
        description: Any | None = None,
        timestamp: datetime | None = None,
    ):
        if color is MISSING:
            color = self.default_color

        super().__init__(
            colour=color,
            title=title,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )

    @property
    def default_color(cls) -> Colour | None:
        return cls._default_color

    @classmethod
    def set_default_color(cls, value: Colour | int | None) -> None:
        cls._default_color = Colour(value) if isinstance(value, int) else value

    def to_dict(self) -> dict[str, Any]:  # type: ignore
        res = super().to_dict()
        if "type" in res.keys():
            del res["type"]  # useless
        return res  # type: ignore


class ErrorEmbed(Embed):
    """Error messages default embed."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(color=Color.brand_red(), **kwargs)

        self.description = f"❌ **|** {message}"
