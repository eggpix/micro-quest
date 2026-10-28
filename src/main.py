"""
Micro Quest is a text-based adventure game engine allowing users to create and
play their own text-based adventure stories.

In Micro Quest, each game is stored in a single JSON file containing all the
information about the game, including the story, choices, and outcomes. Players
can load these files into the Micro Quest engine to play through the adventure.
"""

import argparse
from pathlib import Path

import config
import game_data
import text_display


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Micro Quest: A text-based adventure game engine."
    )
    parser.add_argument("-f", "--file", help="Quickly load a game from file path")
    args = parser.parse_args()

    game = Game()
    game.run(args.file)


class Game:
    """Main game class."""

    def __init__(self) -> None:
        self.display = text_display.TextDisplay(config.default_data.copy())
        self.config = config.load_config(self.display)
        self.display.config = self.config
        self.game_data: game_data.GameData = game_data.GameData(self.display)

    def await_input(self) -> None:
        input("Press Enter to continue... ")

    def play_game(self) -> None:
        data = self.game_data.data
        if data is None:
            return

        self.display.clear_terminal()
        self.display.text(self.display.title(data.get("title") or "Untitled"))
        self.display.text(data.get("description") or "")
        self.await_input()

        while True:
            self.display.clear_terminal()
            room_options = {
                "0": "Save and Exit",
            }
            room_menu = text_display.ListMenu(
                "Choose an option:", room_options, self.display
            )
            selection = room_menu.get_input()
            match selection:
                case "0":
                    self.game_data.save_game_file()
                    return

    def get_game_file(self) -> bool:
        """Prompt until a game file loads successfully or the user cancels."""
        while True:
            self.display.clear_terminal()
            self.display.text("Input the file path of your game to get started.")
            self.display.text(
                f"Current working directory: {self.display.path(str(Path.cwd()))}"
            )
            self.display.text(f"{self.display.key('[0]')} Cancel")
            file_path = input("> ")
            if file_path == "0":
                return False
            if self.load_game(file_path):
                return True

    def load_game(self, file_path: str) -> bool:
        """Load a game, activating template files into a separate copy."""
        if not self.game_data.load_game_file(file_path):
            self.await_input()
            return False

        data = self.game_data.data
        if data is None:
            return False

        if data.get("status") == "template":
            if not self.create_active_copy(file_path):
                return False
            file_path = self.game_data.data_path or file_path

        self.save_last_save(file_path)
        return True

    def create_active_copy(self, template_path: str) -> bool:
        """Prompt for and create a new active copy of the loaded template."""
        source = Path(template_path)
        default_path = source.with_name(f"{source.stem}_copy{source.suffix or '.json'}")
        while True:
            self.display.clear_terminal()
            self.display.text(
                "This game file is a template. To play, you must create a new "
                "copy to store your progress."
            )
            self.display.text(
                "Enter a file path to create a new copy "
                f"(default: {self.display.path(str(default_path))})."
            )
            self.display.text(f"{self.display.key('[0]')} Cancel")
            destination = input("> ").strip()
            if destination == "0":
                return False
            destination = destination or str(default_path)
            if Path(destination).exists():
                self.display.text(
                    "A file already exists at "
                    f"'{self.display.path(destination)}'. Choose another path."
                )
                continue

            self.game_data.data["status"] = "active"
            if self.game_data.save_game_file_as(destination):
                return True
            self.game_data.data["status"] = "template"

    def config_menu(self) -> None:
        """Display the configuration menu."""
        settings = {
            "1": ("clear_terminal", "Toggle clear terminal"),
            "2": ("text_formatting", "Toggle text formatting"),
            "3": ("concatenate_dialogue", "Toggle concatenate dialogue"),
            "4": ("wrap_text", "Toggle wrap text"),
        }
        while True:
            options = {
                key: f"{label} ({'Enabled' if self.config[name] else 'Disabled'})"
                for key, (name, label) in settings.items()
            }
            options["0"] = "Exit"
            menu = text_display.ListMenu("Configuration Menu", options, self.display)
            selection = menu.get_input()
            if selection == "0":
                return

            name, _ = settings[selection]
            self.config[name] = not self.config[name]

            config.save_config(self.config, self.display)

    def load_last_save(self) -> None:
        """Load the last save file if it exists."""
        last_save_file = self.config.get("last_save_file")
        if last_save_file and Path(last_save_file).exists():
            if self.load_game(last_save_file):
                self.display.clear_terminal()
                self.display.text(
                    f"Load game {self.display.path(last_save_file)}?"
                )
                self.display.text(self.display.key("[y/n]"))
                if input("> ").strip().lower() in ("y", "yes"):
                    self.play_game()
        else:
            self.display.text("No last save file found.")
            self.await_input()

    def save_last_save(self, file_path: str) -> None:
        """Save the current game state to the last save file."""
        self.config["last_save_file"] = file_path
        config.save_config(self.config, self.display)

    def run(self, file_path: str | None = None) -> None:
        """Run the game directly or display the main menu."""
        if file_path is not None:
            if self.load_game(file_path):
                self.play_game()
            return

        primary_options = {
            "1": "Load Game",
            "2": "Load Last Save",
            "3": "Options",
            "0": "Exit",
        }
        while True:
            primary_menu = text_display.ListMenu(
                "Welcome to Micro Quest!", primary_options, self.display
            )
            selection = primary_menu.get_input()
            match selection:
                case "0":
                    return
                case "1":
                    if self.get_game_file():
                        self.play_game()
                case "2":
                    self.load_last_save()
                case "3":
                    self.config_menu()


if __name__ == "__main__":
    main()
