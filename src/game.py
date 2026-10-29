"""Application flow for Micro Quest."""

from pathlib import Path

import config
import game_data
import text_display

MAP_SIZE = 7

class Game:
    """Coordinate menus, game data, configuration, and play."""

    def __init__(self) -> None:
        """Initialize game state, configuration, and terminal display."""
        self.display = text_display.TextDisplay(config.Config.DEFAULT_DATA.copy())
        self.config = config.Config(self.display)
        self.config.load_config()
        self.display.config = self.config.data
        self.game_data: game_data.GameData = game_data.GameData(self.display)

    def await_input(self) -> None:
        """Pause until the player presses Enter."""
        input(f"{self.display.key('[Enter]')} to continue... ")

    def get_player_region(self) -> dict:
        data = self.game_data.data
        subregions = data.get("player").get("region").split(":")
        sub = data.get("regions").get(subregions[0])
        for s in range(1, len(subregions)):
            sub = sub.get("subregions").get(subregions[s])
        return sub     

    def get_region_string(self) -> str:
        data = self.game_data.data
        subregions = data.get("player").get("region").split(":")
        name_list = []
        sub = data.get("regions").get(subregions[0])
        for s in range(1, len(subregions)):
            name_list.append(sub.get("name"))
            sub = sub.get("subregions").get(subregions[s])
        name_list.append(sub.get("name"))
        return " / ".join(name_list)

    def get_map(self) -> str:
        player_data = self.game_data.data.get("player")
        map_str = ""
        for y in range(
            player_data.get("room_position")[0] - MAP_SIZE // 2,
            player_data.get("room_position")[1] + MAP_SIZE // 2 + 1
        ):
            for x in range(
                player_data.get("room_position")[0] - MAP_SIZE // 2,
                player_data.get("room_position")[1] + MAP_SIZE // 2 + 1
            ):
                if [x,y] == player_data.get("room_position"):
                    map_str += "[x]"
                elif self.get_player_region().get("rooms").get(f"{x},{y}"):
                    map_str += "[ ]"
                else:
                    map_str += self.display.grid(" . ")
            map_str += "\n"
        return map_str

    def player_move(self):
        player_data = self.game_data.data.get("player")
        available = []
        self.display.clear_terminal()
        direction_menu = text_display.ListMenu(
            f"Available Directions: {", ".join(available)}\nChoose a Direction to Move:",
            {
                "W": "Up",
                "A": "Left",
                "S": "Down",
                "D": "Right",
                "0": "Cancel"
            },
            self.display
        )
        dir_selection = direction_menu.get_input()

        match dir_selection:
            case "w":
                player_data["room_position"][1] -= 1
            case "a":
                player_data["room_position"][0] -= 1
            case "s":
                player_data["room_position"][1] += 1
            case "d":
                player_data["room_position"][0] += 1
            
    def play_game(self) -> None:
        """Display the loaded game's introduction and main choice menu."""
        data = self.game_data.data

        self.display.clear_terminal()
        self.display.text(self.display.title(data.get("title") or "Untitled"))
        self.display.text(data.get("description") or "")
        self.await_input()

        while True:
            self.display.clear_terminal()
            room_options = {
                "1": "Move",
                "2": "View Location",
                "0": "Save and Exit",
            }
            room_menu = text_display.ListMenu(
                "Choose an option:", room_options, self.display
            )
            selection = room_menu.get_input()
            match selection:
                case "1":
                    self.player_move()
                case "2":
                    px = data.get("player").get("room_position")[0] # Player room x
                    py = data.get("player").get("room_position")[1] # Player room y
                    self.display.clear_terminal()
                    self.display.text(f"Current Region: {self.display.title(self.get_region_string())}")
                    self.display.text(f"Current Room: [{px},{py}]")
                    self.display.text(f"{self.get_map()}")
                    self.await_input()
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
                    f"({'Enabled' if self.config.data[name] else 'Disabled'})"
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
                    f"Load game {self.display.path(last_save_file)}?"
                )
                self.display.text(self.display.key("[Y/N]"))
                if input("> ").strip().lower() in ("y", "yes"):
                    self.play_game()
        else:
            self.display.text("No last save file found.")
            self.await_input()

    def store_last_save(self, file_path: str) -> None:
        """Record and persist the path of the current game file."""
        self.config.data["last_save_file"] = file_path
        self.config.save_config()

    def run(self, file_path: str | None = None) -> None:
        """Start the specified game or run the main menu loop."""
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
