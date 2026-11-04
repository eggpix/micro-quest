"""Application flow for Micro Quest."""

from pathlib import Path

import config
import game_data
import text_display

# MAP SIZE centered on player position, must be an odd number
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
        region = data.get("player").get("region")
        return data.get("regions").get(region)

    def get_region_string(self) -> str:
        return self.get_player_region().get("name") or self.game_data.data.get("player").get("region")

    def get_map(self) -> str:
        player_data = self.game_data.data.get("player")
        room_position = player_data["room_position"]
        rooms = self.get_player_region()["rooms"]

        map_str = ""

        for y in range(
            room_position[1] - MAP_SIZE // 2,
            room_position[1] + MAP_SIZE // 2 + 1
        ):
            for x in range(
                room_position[0] - MAP_SIZE // 2,
                room_position[0] + MAP_SIZE // 2 + 1
            ):
                if [x, y] == room_position:
                    map_str += "[x]"
                elif f"{x},{y}" in rooms:
                    map_str += "[ ]"
                else:
                    map_str += self.display.grid(" . ")

            map_str += "\n"

        return map_str

    def player_move(self):
        player_data = self.game_data.data.get("player")
        room_position = player_data["room_position"]
        rooms = self.get_player_region()["rooms"]

        directions = {
            "W": ("Up", (0, -1)),
            "A": ("Left", (-1, 0)),
            "S": ("Down", (0, 1)),
            "D": ("Right", (1, 0))
        }

        direction_options = {"0": "Cancel"}

        for key, (label, offset) in directions.items():
            x = room_position[0] + offset[0]
            y = room_position[1] + offset[1]

            current_room = rooms.get(f"{room_position[0]},{room_position[1]}", {})
            blocked_directions = current_room.get("block", [])

            if f"{x},{y}" in rooms and label.lower() not in blocked_directions:
                direction_options[key] = label

        self.display.clear_terminal()

        direction_menu = text_display.ListMenu(
            "Choose a Direction to Move:",
            direction_options,
            self.display
        )

        dir_selection = direction_menu.get_input().upper()
        if dir_selection in directions:
            offset = directions[dir_selection][1]
            room_position[0] += offset[0]
            room_position[1] += offset[1]
            
    def play_game(self) -> None:
        """Display the loaded game's introduction and main choice menu."""
        data = self.game_data.data

        self.display.clear_terminal()
        self.display.text(self.display.title(data.get("title") or "Untitled"))
        self.display.text(data.get("description") or "")
        self.await_input()

        while True:
            self.display.clear_terminal()
            player_has_inventory = bool(data.get("player").get("inventory"))
            room_options = {
                "1": "Move",
                "2": "View Location",
                **({"3": "View Inventory"} if player_has_inventory else {}),
                "0": "Save and Exit"
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
                case "3" if player_has_inventory:
                    self.display.clear_terminal()
                    self.display.text("Inventory:")
                    for item, quantity in data.get("player").get("inventory").items():
                        entity_name = data.get("entities", {}).get(item, {}).get("name") or item
                        self.display.text(f"{quantity}x {entity_name}")
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
