from html import escape
from typing import Any


def h(value: Any, *, fallback: str = "не указано") -> str:
    text = fallback if value is None or value == "" else str(value)
    return escape(text, quote=False)


def bold(value: Any, *, fallback: str = "не указано") -> str:
    return f"<b>{h(value, fallback=fallback)}</b>"


def code(value: Any, *, fallback: str = "не указано") -> str:
    return f"<code>{h(value, fallback=fallback)}</code>"
