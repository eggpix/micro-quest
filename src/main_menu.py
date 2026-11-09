"""Main menu handling"""

import text_display

from pathlib import Path

class MainMenu:
    """Responsible for prompting user to edit config or load a game."""

    def __init__(self, display, config, game_data, await_input, play_game) -> None:
        self.display = display
        self.config = config
        self.game_data = game_data
        self.await_input = await_input
        self.play_game = play_game

    def run(self) -> None:
        options = {
            "1": "Load Game",
            "2": "Load Last Save",
            "3": "Options",
            "0": "Exit",
        }

        while True:
            menu = text_display.ListMenu(
                "Welcome to Micro Quest!", options, self.display
            )
            selection = menu.get_input()

            match selection:
                case "0":
                    return
                case "1":
                    self.get_game_file()
                case "2":
                    self.load_last_save()
                case "3":
                    self.config_menu()

    def get_game_file(self) -> None:
        """Prompt until a game file loads successfully or the user cancels."""
        while True:
            self.display.clear_terminal()
            self.display.text("Input the file path of your game to get started.")
            self.display.text(
                f"Current working directory: {self.display.format(str(Path.cwd()), ansi_format="path")}"
            )
            self.display.text(f"{self.display.format('[0]', ansi_format='key')} Cancel")
            try:
                file_path = input("> ")
            except EOFError:
                return
            if file_path == "0":
                return
            if self.load_game(file_path):
                self.play_game()
                return
            
    def load_game(self, file_path: str) -> bool:
        """Load a game and make a playable copy when the file is a template."""
        if not self.game_data.load_game_file(file_path):
            self.await_input()
            return False

        data = self.game_data.data
        if data is None:
            return False

        if data.get("status") == "template":
            if not self.copy_template(file_path):
                return False
            file_path = self.game_data.data_path or file_path

        self.store_last_save(file_path)
        return True
    
    def copy_template(self, template_path: str) -> bool:
        """Prompt for and create a new active copy of the loaded template."""
        source = Path(template_path)
        default_path = source.with_name(f"{source.stem}_copy{source.suffix or ".json"}")
        while True:
            self.display.clear_terminal()
            self.display.text(
                "This game file is a template. To play, you must create a new "
                "copy to store your progress."
            )
            self.display.text(
                "Enter a file path to create a new copy "
                f"(default: {self.display.format(str(default_path), ansi_format="path")})."
            )
            self.display.text(f"{self.display.format('[0]', ansi_format='key')} Cancel")
            try:
                destination = input("> ").strip()
            except EOFError:
                return False
            if destination == "0":
                return False
            destination = destination or str(default_path)
            if Path(destination).exists():
                self.display.text(
                    "A file already exists at "
                    f"'{self.display.format(destination, ansi_format="path")}'. Choose another path."
                )
                continue

            self.game_data.data["status"] = "active"
            if self.game_data.copy_game_file(destination):
                return True
            self.game_data.data["status"] = "template"

    def config_menu(self) -> None:
        """Display settings and save each changed option."""
        settings = {
            "1": ("clear_terminal", "Toggle clear terminal"),
            "2": ("text_formatting", "Toggle text formatting"),
            "3": ("concatenate_dialogue", "Toggle concatenate dialogue"),
            "4": ("wrap_text", "Toggle wrap text"),
        }
        while True:
            options = {
                key: (
                    f"{label} "
                    f"({"Enabled" if self.config.data[name] else "Disabled"})"
                )
                for key, (name, label) in settings.items()
            }
            options["0"] = "Exit"
            menu = text_display.ListMenu("Configuration Menu", options, self.display)
            selection = menu.get_input()
            if selection == "0":
                return

            name, _ = settings[selection]
            self.config.data[name] = not self.config.data[name]

            self.config.save_config()

    def load_last_save(self) -> None:
        """Offer to resume the last saved game when its file exists."""
        last_save_file = self.config.data.get("last_save_file")
        if last_save_file and Path(last_save_file).exists():
            if self.load_game(last_save_file):
                self.display.clear_terminal()
                self.display.text(
                    f"Load game {self.display.format(last_save_file, ansi_format="path")}?"
                )
                self.display.text(self.display.format("[Y/N]", ansi_format="key"))
                try:
                    choice = input("> ").strip().lower()
                except EOFError:
                    return
                if choice in ("y", "yes"):
                    self.play_game()
        else:
            self.display.text("No last save file found.")
            self.await_input()

    def store_last_save(self, file_path: str) -> None:
        """Record and persist the path of the current game file."""
        self.config.data["last_save_file"] = file_path
        self.config.save_config()