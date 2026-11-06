"""Classes and functions for displaying text in the terminal."""

import re
import shutil
import sys


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

    def color_foreground(self, text: str, color: object) -> str:
        """Return text with an ANSI 24-bit foreground color."""
        if (
            not isinstance(color, str)
            or re.fullmatch(r"#[0-9a-fA-F]{6}", color) is None
        ):
            raise ValueError("Expected a six-digit hex color such as '#12ABEF'.")

        red, green, blue = (
            int(color[index:index + 2], 16)
            for index in (1, 3, 5)
        )
        return format(f"\x1B[38;2;{red};{green};{blue}m{text}\x1B[0m")

    def _remove_formatting(self, text: str) -> str:
        """Remove ANSI escape sequences from text."""
        return self.ANSI_ESCAPE.sub("", text)

    def _wrap_line(self, text: str, width: int) -> str:
        """Wrap a line while counting only visible characters."""
        words: list[tuple[list[str], int]] = []
        word: list[str] = []
        word_width = 0

        for match in re.finditer(
            rf"{self.ANSI_ESCAPE.pattern}|.", text, flags=re.DOTALL
        ):
            token = match.group()
            if self.ANSI_ESCAPE.fullmatch(token):
                word.append(token)
            elif token.isspace():
                if word_width:
                    words.append((word, word_width))
                    word = []
                    word_width = 0
            else:
                word.append(token)
                word_width += 1

        if word:
            words.append((word, word_width))

        lines: list[str] = []
        line: list[str] = []
        line_width = 0

        for word, word_width in words:
            if not word_width:
                line.extend(word)
                continue

            if word_width <= width:
                if line_width and line_width + 1 + word_width > width:
                    lines.append("".join(line))
                    line = []
                    line_width = 0
                if line_width:
                    line.append(" ")
                line.extend(word)
                line_width += word_width + (1 if line_width else 0)
                continue

            if line:
                lines.append("".join(line))
                line = []
                line_width = 0

            for token in word:
                if self.ANSI_ESCAPE.fullmatch(token):
                    line.append(token)
                else:
                    if line_width == width:
                        lines.append("".join(line))
                        line = []
                        line_width = 0
                    line.append(token)
                    line_width += 1

        if line or not lines:
            lines.append("".join(line))

        return "\n".join(lines)

    def format(self, text: str, ansi_format: str | None = None) -> str:
        """Apply formatting and wrapping according to configuration."""
        match ansi_format:
            case "title":
                text = f"\x1B[1m{text}\x1B[0m\n"
            case "path":
                text = f"\x1B[34m{text}\x1B[0m"
            case "hint":
                text = f"\x1B[3m{text}\x1B[0m"
            case "key":
                text = f"\x1B[36m{text}\x1B[0m"
            case "error":
                text = f"\x1B[31m{text}\x1B[0m"
            case "grid":
                text = f"\x1B[2m{text}\x1B[0m"

        if not self.config["text_formatting"]:
            text = self._remove_formatting(text)

        if self.config["wrap_text"]:
            width = max(1, shutil.get_terminal_size().columns)
            text = "\n".join(
                self._wrap_line(line, width) if line else ""
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
        self.display.text(self.display.format(self.title, "title"))
        if self.description is not None:
            self.display.text(self.description)

        for key, option in self.options.items():
            self.display.text(f"{self.display.format(f'[{key}]', ansi_format="key")} {option}")

    def get_input(self) -> str:
        """Display the menu until the user enters a valid selection."""
        while True:
            self.show()
            selection = input("> ").lower().strip()

            if selection in [option.lower() for option in self.options]:
                return selection
