"""Classes and functions for displaying text in the terminal."""

import re
import shutil
import sys
import textwrap


class TextDisplay:
    """Format and display terminal text using the user's settings."""

    ANSI_ESCAPE = re.compile(
        r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
    )

    def __init__(self, config: dict) -> None:
        """Create a display that uses the provided configuration."""
        self.config = config

    def clear_terminal(self) -> None:
        """Clear the visible terminal screen."""
        if self.config["clear_terminal"]:
            sys.stdout.write("\x1B[2J\x1B[H")
            sys.stdout.flush()

    def title(self, text: str) -> str:
        """Return text styled as a title."""
        return f"\x1B[1m{text}\x1B[0m\n"

    def path(self, text: str) -> str:
        """Return text styled as a file-system path."""
        return f"\x1B[34m{text}\x1B[0m"

    def key(self, text: str) -> str:
        """Return text styled as a menu key or response prompt."""
        return f"\x1B[36m{text}\x1B[0m"

    def error(self, text: str) -> str:
        """Return text styled as an error message."""
        return f"\x1B[31m{text}\x1B[0m"

    def grid(self, text: str) -> str:
        """Return text styled as dim background grid for maps."""
        return f"\x1B[2m{text}\x1B[0m"

    def remove_formatting(self, text: str) -> str:
        """Remove ANSI escape sequences from text."""
        return self.ANSI_ESCAPE.sub("", text)

    def format(self, text: str) -> str:
        """Apply formatting and wrapping according to configuration."""
        if not self.config["text_formatting"]:
            text = self.remove_formatting(text)

        if self.config["wrap_text"]:
            width = shutil.get_terminal_size().columns
            text = "\n".join(
                textwrap.fill(line, width=width) if line else ""
                for line in text.splitlines()
            )

        return text

    def text(self, text: str) -> None:
        """Display formatted text according to configuration."""
        print(self.format(text))


class ListMenu:
    """A menu allowing selection from a list of options."""

    def __init__(
        self,
        title: str, # Formatted
        options: dict[str, str],
        display: TextDisplay,
        description: str | None = None, # Not Formatted
        context: str | None = None # Displayed before title
    ) -> None:
        """Create a menu with a title, keyed options, and a display."""
        self.title = title
        self.options = options
        self.display = display
        self.description = description
        self.context = context

    def show(self) -> None:
        """Display the menu, optionally clearing the terminal."""
        self.display.clear_terminal()

        if self.context is not None:
            self.display.text(self.context)
        self.display.text(self.display.title(self.title))
        if self.description is not None:
            self.display.text(self.description)

        for key, option in self.options.items():
            self.display.text(f"{self.display.key(f'[{key}]')} {option}")

    def get_input(self) -> str:
        """Display the menu until the user enters a valid selection."""
        while True:
            self.show()
            selection = input("> ").lower().strip()

            if selection in [option.lower() for option in self.options]:
                return selection
