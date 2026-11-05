"""Application flow for Micro Quest."""

from pathlib import Path

import config
import game_data
import text_display
import re

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

    def format_text(self, text: str) -> str:
        def replace(match):
            path = match.group(1).split(".")
            value = self.game_data.data

            for key in path:
                if not isinstance(value, dict) or key not in value:
                    return match.group(0)
                value = value[key]

            return str(value)

        return re.sub(r"\{([a-zA-Z0-9_.]+)\}", replace, text)

    def loop_dialogue(self, dialogue: str | list[str]) -> None:
        if isinstance(dialogue, str):
            self.display.clear_terminal()
            self.display.text(self.format_text(dialogue))
            self.await_input
        else:
            for dia in dialogue:
                self.display.clear_terminal()
                self.display.text(self.format_text(dia))
                self.await_input()

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

    def get_room_data(self) -> dict:
        data = self.game_data.data
        player_data = data.get("player")
        region = player_data["region"]
        room_position = player_data["room_position"]
        return data.get("regions").get(region).get("rooms").get(f"{room_position[0]},{room_position[1]}")

    def check_conditions(self, condition_parent: dict) -> bool:
        data = self.game_data.data
        player_data = data.get("player")
        conditions = condition_parent.get("conditions", [])
        player_inventory = player_data.get("inventory") or {}
        for condition in conditions:
            condition_type = condition.get("type")
            match condition_type:
                case "has_item":
                    condition_item = condition.get("item")
                    if condition_item is None:
                        return True
                    if condition_item not in player_inventory:
                        failure = condition_parent.get("failure")
                        if failure:
                            failure_dialogue = failure.get("message")
                            if failure_dialogue:
                                self.display.clear_terminal()
                                self.loop_dialogue(failure_dialogue)
                                self.await_input()
                        return False

        success = condition_parent.get("success")
        if success:
            success_dialogue = success.get("message")
            if success_dialogue:
                self.display.clear_terminal()
                self.loop_dialogue(success_dialogue)
                self.await_input()

        events = condition_parent.get("events")
        if events:
            if isinstance(events, dict):
                events = [events]
            for event in events:
                match event.get("type"):
                    case "remove_item":
                        event_item = event.get("item")
                        if event_item:
                            player_inventory.pop(event_item, None)

        return True

    def move_conditions(self, direction: str) -> bool:
        room_data = self.get_room_data()
        connections = room_data.get("connections")

        if connections:
            connection = connections.get(direction, {})
            conditions = connection.get("conditions")
            has_connection_actions = bool(
                conditions or connection.get("success") or connection.get("events")
            )
            if not has_connection_actions:
                return True

            if (
                not connection.get("repeat_condition", True)
                and connection.get("condition_executed", False)
            ):
                return True

            if not self.check_conditions(connection):
                return False

            if not connection.get("repeat_condition", True):
                connection["condition_executed"] = True

        return True

    def get_connection_destination(
        self, direction: str, offset: tuple[int, int]
    ) -> tuple[str, list[int]]:
        """Return a connection's explicit destination or its adjacent room."""
        player_data = self.game_data.data.get("player")
        connections = self.get_room_data().get("connections") or {}
        connection = connections.get(direction, {})
        current_position = player_data["room_position"]
        destination_region = connection.get("region", player_data["region"])
        destination_position = connection.get("room_position")

        if destination_position is None:
            destination_position = [
                current_position[0] + offset[0],
                current_position[1] + offset[1],
            ]

        return destination_region, destination_position

    def get_room_items(self) -> list[str]:
        room_data = self.get_room_data()
        return room_data.get("items", [])

    def view_room_items(self) -> None:
        """Show items in the current room and collect eligible items."""
        room_items = self.get_room_items()
        if not room_items:
            return

        data = self.game_data.data
        entities = data.get("entities", {})

        options = {}
        option_items = {}
        for index, item in enumerate(room_items):
            entity = entities.get(item, {})
            entity_name = entity.get("name") or item
            option = str(index + 1)
            options[option] = (
                f"Pick up {entity_name}"
                if entity.get("collectable") is True
                else f"{entity_name} (not collectable)"
            )
            option_items[option] = (index, item)

        options["0"] = "Back"

        selection = text_display.ListMenu(
            "Items in this room:", options, self.display
        ).get_input()
        if selection == "0":
            return

        index, item = option_items[selection]
        entity = entities.get(item, {})
        if entity.get("collectable") is not True:
            self.display.text(f"You cannot pick up {entity.get('name') or item}.")
            self.await_input()
            return

        inventory = data.get("player").setdefault("inventory", {})
        inventory[item] = inventory.get(item, 0) + 1
        room_items.pop(index)
        self.display.text(f"You picked up {entity.get('name') or item}.")
        self.await_input()

    def enter_room(self) -> None:
        room_data = self.get_room_data()

        room_dialogue = room_data.get("message", {}).get("text")

        repeat_dialogue = room_data.get("message", {}).get("repeat", True)
        played_dialogue = room_data.get("message", {}).get("played", False)

        if room_dialogue:
            if not played_dialogue:
                self.loop_dialogue(room_dialogue)
                if not repeat_dialogue:
                    room_data["message"]["played"] = True

        if room_data.get("ending") and not self.game_data.data.get("completed"):
            player_data = self.game_data.data.get("player")
            inventory = player_data.setdefault("inventory", {})
            entities = self.game_data.data.get("entities", {})
            remaining_items = []
            for item in room_data.get("items", []):
                if entities.get(item, {}).get("collectable") is True:
                    inventory[item] = inventory.get(item, 0) + 1
                else:
                    remaining_items.append(item)
            room_data["items"] = remaining_items
            self.game_data.data["completed"] = True
            self.game_data.save_game_file()

    def player_move(self) -> None:
        player_data = self.game_data.data.get("player")
        room_position = player_data["room_position"]
        rooms = self.get_player_region()["rooms"]

        directions = {
            "W": ("Up", (0, -1)),
            "A": ("Left", (-1, 0)),
            "S": ("Down", (0, 1)),
            "D": ("Right", (1, 0))
        }

        direction_options = {}

        for key, (label, offset) in directions.items():
            current_room = rooms.get(f"{room_position[0]},{room_position[1]}", {})
            blocked_directions = current_room.get("block", [])
            if label.lower() in blocked_directions:
                continue

            destination_region, destination_position = (
                self.get_connection_destination(label.lower(), offset)
            )
            destination_rooms = (
                self.game_data.data.get("regions", {})
                .get(destination_region, {})
                .get("rooms", {})
            )
            if (
                f"{destination_position[0]},{destination_position[1]}"
                in destination_rooms
            ):
                direction_options[key] = label

        direction_options["0"] = "Cancel"

        self.display.clear_terminal()

        direction_menu = text_display.ListMenu(
            f"{self.get_map()}\nChoose a Direction to Move:",
            direction_options,
            self.display
        )

        dir_selection = direction_menu.get_input().upper()

        if dir_selection == "0":
            return

        # Check conditions before entering
        if self.move_conditions(directions[dir_selection][0].lower()):
            direction = directions[dir_selection][0].lower()
            destination_region, destination_position = (
                self.get_connection_destination(
                    direction, directions[dir_selection][1]
                )
            )
            player_data["region"] = destination_region
            player_data["room_position"] = destination_position

            self.enter_room()
            
    def play_game(self) -> None:
        """Display the loaded game's introduction and main choice menu."""
        data = self.game_data.data

        self.display.clear_terminal()
        self.display.text(self.display.title(data.get("title") or "Untitled"))
        self.display.text(data.get("description") or "")
        self.await_input()

        if data.get("completed"):
            self.display.text("This game has already been completed.")
            self.await_input()
            return

        self.enter_room()
        if data.get("completed"):
            return

        def view_location():
            px, py = data.get("player").get("room_position")
            self.display.clear_terminal()
            self.display.text(f"Current Region: {self.display.title(self.get_region_string())}")
            self.display.text(f"Current Room: [{px},{py}]")
            self.display.text(f"{self.get_map()}")
            self.await_input()


        def view_inventory():
            self.display.clear_terminal()
            self.display.text("Inventory:")

            for item, quantity in data.get("player").get("inventory").items():
                entity_name = data.get("entities", {}).get(item, {}).get("name") or item
                self.display.text(f"{quantity}x {entity_name}")

            self.await_input()


        while True:
            self.display.clear_terminal()

            player_has_inventory = bool(data.get("player").get("inventory"))
            room_items = self.get_room_items()

            index = 2

            room_options = {
                "1": "Move",
                "2": "View Location"
            }

            actions = {
                "1": self.player_move,
                "2": view_location
            }

            if player_has_inventory:
                index += 1
                room_options[str(index)] = "View Inventory"
                actions[str(index)] = view_inventory

            if room_items:
                index += 1
                room_options[str(index)] = "View Room Items"
                actions[str(index)] = self.view_room_items  # Your room items method

            room_options["0"] = "Save and Exit"
            actions["0"] = self.game_data.save_game_file

            room_menu = text_display.ListMenu(
                "Choose an option:", room_options, self.display
            )

            selection = room_menu.get_input()

            action = actions.get(selection)

            if action:
                action()

                if data.get("completed"):
                    return

                if selection == "0":
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
