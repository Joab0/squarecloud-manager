import pytest

from bot.utils.translator import Translator

Translator.locales = {
    "pt-BR": {
        "squarecloud": "Nuvem Quadrada",
        "hello": "Olá, {0}",
        "key-1": {"key-2": {"key-3": "Valor"}},
    },
    "en-US": {
        "squarecloud": "Square Cloud",
        "hello": "Hello, {0}",
        "key-1": {"key-2": {"key-3": "Value"}},
    },
}


@pytest.mark.parametrize(
    ("string", "locale", "expected"),
    [
        ("squarecloud", "pt-BR", "Nuvem Quadrada"),
        ("key-1.key-2.key-3", "pt-BR", "Valor"),
        ("squarecloud", "en-US", "Square Cloud"),
        ("key-1.key-2.key-3", "en-US", "Value"),
    ],
)
def test_translate(string: str, locale: str, expected: str) -> None:
    t = Translator(locale)
    assert t(string) == expected


@pytest.mark.parametrize(
    ("string", "locale", "expected", "values"),
    [
        ("hello", "pt-BR", "Olá, Mundo", ("Mundo",)),
        ("hello", "en-US", "Hello, World", ("World",)),
    ],
)
def test_translate_formatted(string: str, locale: str, expected: str, values: tuple[str, ...]) -> None:
    t = Translator(locale)
    assert t(string, *values) == expected


def test_translator_failures() -> None:
    t = Translator("pt-BR")

    # Imcomplete string
    with pytest.raises(ValueError):
        t("key-1.key-2")

    # Key does not exists
    with pytest.raises(KeyError):
        t("key-1.key-2.key-4")
