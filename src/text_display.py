"""File containing functions and classes for displaying text in the terminal."""

import text_display
import re

def clear_terminal() -> None:
    print("\033[2J\033[H", end="")

def remove_ansi_formatting(text: str) -> str:
    """Comprehensive regex pattern covering standard 7-bit and 8-bit C1 ANSI escape sequences"""
    ansi_escape = re.compile(r'(?:\x1B[@-Z\\-_]|[\x80-\x9A\x9C-\x9F]|(?:\x1B\[|\x9B)[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

class ListMenu:
    """Represents a menu allowing selection from a list of items.

    Attributes:
        title (str): The title of the menu as a string. Will be displayed one
            line above the list of options.
        options (dict[str, str]): Dictionary containing each of the selectable
            options and their indices as keys.
    """

    def __init__(self, title: str, options: dict[str, str]) -> None:
        self.title = title
        self.options = options

    def show(self, clear_terminal: bool) -> None:
        """Clears terminal if enabled, then prints menu to terminal."""
        if clear_terminal:
            text_display.clear_terminal()
        print(self.title)
        for key, option in self.options.items():
            print(f"[{key}] {option}")

    def get_input(self, clear_terminal: bool) -> str:
        """Displays menu until user inputs valid input.
        
        Returns:
            user selection as a string matching a key in the dictionary.
        """
        while True:
            self.show(clear_terminal)
            selection = input("> ")
            selection = selection.lower().strip()
            if selection in self.options:
                return selection
