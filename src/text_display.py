"""Classes and functions for displaying text in the terminal."""

import re
import shutil
import sys
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
        sys.stdout.write("\x1B[2J\x1B[H")

    def title(self, text: str) -> str:
        return f"\x1B[1m{text}\x1B[0m\n"

    def path(self, text: str) -> str:
        return f"\x1B[34m{text}\x1B[0m"

    def key(self, text: str) -> str:
        return f"\x1B[36m{text}\x1B[0m"

    def error(self, text: str) -> str:
        return f"\x1B[31m{text}\x1B[0m"

    def remove_formatting(self, text: str) -> str:
        """Remove ANSI escape sequences from text."""
        return self.ANSI_ESCAPE.sub("", text)

    def format(self, text: str) -> str:
        """Apply formatting and wrapping according to configuration."""
        if not self.config["text_formatting"]:
            text = self.remove_formatting(text)

        if self.config["wrap_text"]:
            width = shutil.get_terminal_size().columns
            text = textwrap.fill(text, width=width)

        return text

    def text(self, text: str) -> None:
        """Display formatted text according to configuration."""
        print(self.format(text))


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
        self.display.text(self.display.title(self.title))

        for key, option in self.options.items():
            self.display.text(f"{self.display.key(f'[{key}]')} {option}")

    def get_input(self) -> str:
        """Display the menu until the user enters a valid selection."""
        while True:
            self.show()
            selection = input("> ").lower().strip()

            if selection in self.options:
                return selection
