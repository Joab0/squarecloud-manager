from __future__ import annotations

import logging
import os
from difflib import get_close_matches
from typing import Any, ClassVar, Final

import yaml
from discord import Locale
from discord.app_commands import TranslationContextTypes
from discord.app_commands import Translator as _Translator
from discord.app_commands import locale_str

DEFAULT_LOCALE: Final[str] = "en-US"

log = logging.getLogger(__name__)


class AppCommandsTranslator(_Translator):
    """Translator for slash commands."""

    async def translate(self, string: locale_str, locale: Locale, context: TranslationContextTypes) -> str | None:
        if (id := string.extras.get("id")) is None:
            return None

        if str(locale) not in Translator.locales:
            return None

        try:
            return Translator.translate(id, locale)
        except (KeyError, ValueError):
            log.error(f"Unable to translate '{locale!s}.{id}' at {context.location.name}.")
            return None  # No translate


class Translator:
    """Object that represents the bot's translator."""

    locales: ClassVar[dict[str, dict[str, Any]]] = {}

    __slots__ = ("locale",)

    def __init__(self, locale: str | Locale = DEFAULT_LOCALE) -> None:
        self.locale: str = str(locale)

    def __call__(self, string: str, /, *args: Any) -> str:
        """
        Translate a string to current locale.

        Args:
            string: Translation string.
        """
        return self.translate(string, self.locale, *args)

    @classmethod
    def load(cls, path: str) -> None:
        """Load locales from path.

        Args:
            path: Should be the path to a folder with translation files in YAML format.
        """
        cls.locales.clear()

        available = [i.value for i in Locale]

        for locale_file in os.listdir(path):
            if not locale_file.endswith(("yml", "yaml")):
                continue

            locale = locale_file.split(".")[0]

            # Check if the locale is valid on Discord.
            if locale not in available:
                raise Exception(f"{locale!r} is not a valid locale.")

            with open(f"{path}/{locale_file}") as f:
                cls.locales[locale] = yaml.safe_load(f)

    @classmethod
    def translate(cls, string: str, locale: str | Locale, *args: Any) -> str:
        """Function that translates translation IDs into a string.

        Args:
            string: Translation strnig.
            locale: Locale to be translated.
        """
        keys = string.split(".")

        locale = str(locale)

        if locale not in cls.locales:
            locale = DEFAULT_LOCALE

        # Get all locale dict
        s = cls.locales[locale]

        for key in keys:
            try:
                s = s[key]
            except KeyError as e:
                # Remove invalid keys
                index = keys.index(key)
                del keys[index:]

                # Create helpful message
                helpful = f"'{locale}.{'.'.join(keys)}' has no key {key!r}. "

                if matches := get_close_matches(key, s.keys()):
                    helpful += f"Did you mean: {matches[0]!r}?"

                raise KeyError(helpful.strip()) from e

        if not isinstance(s, str):
            raise ValueError(f"Invalid translation string: {string!r}.")

        s = s.format(*args)

        return s
