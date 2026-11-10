"""Shared test helpers for the Micro Quest test suite."""

from types import SimpleNamespace
from typing import Any

import game


class RecordingDisplay:
    """Capture display output without writing to the terminal."""

    def __init__(self) -> None:
        self.config = {"concatenate_dialogue": False}
        self.messages: list[str] = []

    def text(self, message: str) -> None:
        self.messages.append(message)

    def format(self, message: str, **_kwargs: Any) -> str:
        return message

    def clear_terminal(self) -> None:
        pass


class QueuedMenu:
    """A menu stub that returns predetermined choices and records options."""

    selections: list[str] = []
    instances: list["QueuedMenu"] = []

    def __init__(
        self,
        title: str,
        options: dict[str, str],
        _display: Any,
        **_kwargs: Any,
    ) -> None:
        self.title = title
        self.options = options
        self.instances.append(self)

    def get_input(self) -> str:
        if not self.selections:
            raise AssertionError("Unexpected menu prompt.")
        return self.selections.pop(0)

    @classmethod
    def prepare(cls, *selections: str) -> None:
        cls.selections = list(selections)
        cls.instances = []


def make_game(data: dict[str, Any]) -> game.Game:
    """Build a Game with in-memory data and captured display/dialogue."""
    instance = game.Game.__new__(game.Game)
    instance.display = RecordingDisplay()
    instance.game_data = SimpleNamespace(data=data)
    instance.dialogue: list[str | list[str]] = []
    instance.loop_dialogue = instance.dialogue.append
    instance.await_input = lambda: None
    return instance
