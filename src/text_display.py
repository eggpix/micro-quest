"""Classes and functions for displaying text in the terminal."""

import re
import shutil
import textwrap


class TextDisplay:
    """Displays terminal text according to the user's configuration."""

    ANSI_ESCAPE = re.compile(
        r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
    )

    def __init__(self, config: dict) -> None:
        self.config = config

    def clear_terminal(self) -> None:
        """Clear the visible terminal screen."""
        print("\x1B[2J\x1B[H", end="")

    def remove_formatting(self, text: str) -> str:
        """Remove ANSI escape sequences from text."""
        return self.ANSI_ESCAPE.sub("", text)

    def _format_text(self, text: str | list[str]) -> str | list[str]:
        """Apply formatting and wrapping according to configuration."""

        if not self.config["text_formatting"]:
            if isinstance(text, list):
                text = [self.remove_formatting(line) for line in text]
            else:
                text = self.remove_formatting(text)

        if self.config["wrap_text"]:
            width = shutil.get_terminal_size().columns

            if isinstance(text, list):
                text = [textwrap.fill(line, width=width) for line in text]
            else:
                text = textwrap.fill(text, width=width)

        return text

    def display_title(self, title: str, clear: bool | None = None) -> None:
        """Display a title, optionally clearing the terminal."""
        if clear is None:
            clear = self.config["clear_terminal"]
        if clear:
            self.clear_terminal()

        if self.config["text_formatting"]:
            title = f"\x1B[33m{title}\x1B[0m"

        print(title)

    def display_dialogue(
        self, text: str | list[str], clear: bool | None = None
    ) -> None:
        """Display dialogue according to the user's settings."""
        if clear is None:
            clear = self.config["clear_terminal"]
        if clear:
            self.clear_terminal()

        if (
            self.config["concatenate_dialogue"]
            and isinstance(text, list)
        ):
            text = "\n".join(text)

        text = self._format_text(text)
        print(text)


class ListMenu:
    """A menu allowing selection from a list of options."""

    def __init__(
        self,
        title: str,
        options: dict[str, str],
        display: TextDisplay,
    ) -> None:
        self.title = title
        self.options = options
        self.display = display

    def show(self) -> None:
        """Display the menu, optionally clearing the terminal."""
        self.display.display_title(self.title)

        for key, option in self.options.items():
            print(f"[{key}] {option}")

    def get_input(self) -> str:
        """Display the menu until the user enters a valid selection."""
        while True:
            self.show()
            selection = input("> ").lower().strip()

            if selection in self.options:
                return selection
