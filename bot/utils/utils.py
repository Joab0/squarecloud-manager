from datetime import timedelta
from typing import Literal

import humanize


def format_timedelta(
    delta: float | int | timedelta,
    /,
    *,
    locale: str | None = None,
    format: Literal["natural", "precise"] = "precise",
) -> str:
    """Humanize a timedelta."""
    if locale is None:
        humanize.deactivate()
    else:
        try:
            humanize.activate(locale.replace("-", "_"))
        except Exception:
            # Fallback to English
            humanize.deactivate()

    delta = delta if isinstance(delta, timedelta) else timedelta(seconds=delta)
    if format == "precise":
        return humanize.precisedelta(delta)
    return humanize.naturaldelta(delta)
