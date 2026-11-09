"""Application flow for Micro Quest."""

import re

import config
import game_data
import main_menu
import text_display
import world


class Game:
    """Coordinate menus, game data, configuration, and play."""

    def __init__(self) -> None:
        """Initialize game state, configuration, and terminal display."""
        self.display = text_display.TextDisplay(config.Config.DEFAULT_DATA.copy())
        self.config = config.Config(self.display)
        self.config.load_config()
        self.display.config = self.config.data
        self.game_data = game_data.GameData(self.display)
        self.main_menu = main_menu.MainMenu(
            self.display,
            self.config,
            self.game_data,
            self.await_input,
            self.play_game,
        )
        self.world = world.World(self.game_data, self.display)

    def await_input(self) -> None:
        """Pause until the player presses Enter."""
        input(f"{self.display.format("[Enter]", ansi_format="key")} to continue... ")

    def format_text(self, text: str) -> str:
        def replace(match):
            path = match.group(1).split(".")
            value = self.game_data.data

            for key in path:
                if not isinstance(value, dict) or key not in value:
                    return match.group(0)
                value = value[key]

            return str(value)

        return re.sub(r"\{([a-zA-Z0-9_.,]+)\}", replace, text)

    def loop_dialogue(self, dialogue: str | list[str]) -> None:
        if isinstance(dialogue, str):
            self.display.clear_terminal()
            self.display.text(self.format_text(dialogue))
            self.await_input()
            return

        if self.display.config.get("concatenate_dialogue", False):
            self.display.clear_terminal()
            combined_dialogue = "\n".join(
                self.format_text(dia) for dia in dialogue
            )
            self.display.text(combined_dialogue)
            self.await_input()
            return

        for dia in dialogue:
            self.display.clear_terminal()
            self.display.text(self.format_text(dia))
            self.await_input()

    @staticmethod
    def get_data_path(target: str) -> list[str] | None:
        """Convert a dotted target into a path in the game data."""
        path = target.split(".")
        if path[0] == "world" and len(path) > 1:
            path = ["attributes", *path[1:]]
        if not path or any(not part for part in path):
            return None
        return path

    def get_attribute_value(self, target: str) -> tuple[bool, object]:
        """Resolve a dotted game-data path, including the world alias."""
        path = self.get_data_path(target)
        if path is None:
            return False, None
        value = self.game_data.data
        for key in path:
            if not isinstance(value, dict) or key not in value:
                return False, None
            value = value[key]
        return True, value

    def conditions_met(self, conditions: list[dict]) -> bool:
        """Evaluate all supported conditions; every condition must pass."""
        for condition in conditions:
            condition_type = condition.get("type")
            match condition_type:
                case "has_item":
                    condition_item = condition.get("item")
                    condition_object = condition.get("object", "player")
                    quantity = condition.get("quantity")
                    min_quantity = condition.get("min_quantity", 1)
                    max_quantity = condition.get("max_quantity", None)
                    if (
                        not isinstance(condition_item, str)
                        or not condition_item
                        or not isinstance(condition_object, str)
                        or not (quantity is None or isinstance(quantity, int))
                        or isinstance(quantity, bool)
                        or not isinstance(min_quantity, int)
                        or isinstance(min_quantity, bool)
                        or not (max_quantity is None or isinstance(max_quantity, int))
                        or isinstance(max_quantity, bool)
                        or quantity is not None
                        and quantity < 1
                        or min_quantity < 1
                        or max_quantity is not None
                        and max_quantity < 1
                        or max_quantity is not None
                        and min_quantity > max_quantity
                        or quantity is not None
                        and (
                            quantity < min_quantity
                            or max_quantity is not None
                            and quantity > max_quantity
                        )
                    ):
                        return False

                    found, actual_value = self.get_attribute_value(condition_object)
                    if not found or not isinstance(actual_value, dict):
                        return False
                    inventory_object = actual_value.get("inventory")
                    if not isinstance(inventory_object, dict):
                        return False

                    item_quantity = inventory_object.get(condition_item, 0)
                    if (
                        not isinstance(item_quantity, int)
                        or isinstance(item_quantity, bool)
                        or (quantity is not None and item_quantity != quantity)
                        or item_quantity < min_quantity
                        or (
                            max_quantity is not None
                            and item_quantity > max_quantity
                        )
                    ):
                        return False
                case "attribute_equals":
                    attribute = condition.get("attribute")
                    if not isinstance(attribute, str):
                        return False
                    found, actual_value = self.get_attribute_value(attribute)
                    if not found or actual_value != condition.get("value"):
                        return False
                case _:
                    return False

        return True

    def check_conditions(self, condition_parent: dict) -> bool:
        """Evaluate conditions and run their associated messages and events."""
        if not self.conditions_met(condition_parent.get("conditions", [])):
            failure = condition_parent.get("failure")
            failure_dialogue = failure.get("message") if failure else None
            if failure_dialogue:
                self.loop_dialogue(failure_dialogue)
            return False

        success = condition_parent.get("success")
        if success:
            success_dialogue = success.get("message")
            if success_dialogue:
                self.loop_dialogue(success_dialogue)

        self.apply_events(condition_parent.get("events"))
        return True

    def apply_events(self, events: dict | list[dict] | None) -> None:
        """Apply game events shared by connections and entity interactions."""
        data = self.game_data.data
        player_data = data.get("player")
        if events:
            if isinstance(events, dict):
                events = [events]
            for event in events:
                match event.get("type"):
                    case "remove_item":
                        event_item = event.get("item")
                        if event_item:
                            player_data.setdefault("inventory", {}).pop(
                                event_item, None
                            )
                    case "set_attribute":
                        target = event.get("target")
                        if not isinstance(target, str) or not target:
                            continue

                        path = self.get_data_path(target)
                        if path is None or len(path) < 2:
                            continue

                        value = data
                        for key in path[:-1]:
                            child = value.get(key)
                            if not isinstance(child, dict):
                                child = {}
                                value[key] = child
                            value = child
                        value[path[-1]] = event.get("value")

    def is_collectable_entity(self, entity: dict) -> bool:
        """Return whether an entity can be picked up into inventory."""
        return (
            entity.get("collectable") is True
            and entity.get("item", True) is not False
        )

    def view_room_items(self) -> None:
        """Show items in the current room and collect eligible items."""
        room_items = self.world.get_room_items()
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
            interactions = entity.get("interactions") or {}
            is_collectable = self.is_collectable_entity(entity)

            if interactions:
                action = f"Interact with {entity_name}"
            elif is_collectable:
                action = f"Pick up {entity_name}"
            else:
                action = f"{entity_name} (not collectable)"

            options[option] = action
            option_items[option] = (index, item)

        options["0"] = "Back"

        selection = text_display.ListMenu(
            "Items in this room:", options, self.display
        ).get_input()
        if selection == "0":
            return

        index, item = option_items[selection]
        entity = entities.get(item, {})
        entity_name = entity.get("name") or item
        interactions = entity.get("interactions") or {}
        is_collectable = self.is_collectable_entity(entity)

        if interactions:
            interaction_options = {
                str(interaction_index): interaction.get("name") or interaction_id
                for interaction_index, (interaction_id, interaction) in enumerate(
                    interactions.items(), start=1
                )
            }
            pickup_option = None
            if is_collectable:
                pickup_option = str(len(interaction_options) + 1)
                interaction_options[pickup_option] = "Pick up"
            interaction_options["0"] = "Back"

            interaction_selection = text_display.ListMenu(
                entity_name, interaction_options, self.display
            ).get_input()
            if interaction_selection == "0":
                return

            if interaction_selection == pickup_option:
                self.collect_room_item(index, item, entity)
                return

            interaction = list(interactions.values())[
                int(interaction_selection) - 1
            ]
            message = interaction.get("message")
            if message:
                self.loop_dialogue(message)
            else:
                self.display.text(
                    f"{interaction.get("name") or "Interaction"} has no response."
                )
                self.await_input()
            self.apply_events(interaction.get("events"))
            return

        if not is_collectable:
            self.display.text(f"You cannot pick up {entity.get("name") or item}.")
            self.await_input()
            return

        self.collect_room_item(index, item, entity)

    def collect_room_item(self, index: int, item: str, entity: dict) -> None:
        """Move one collectable room item into the player"s inventory."""
        data = self.game_data.data
        room_items = self.world.get_room_items()
        inventory = data.get("player").setdefault("inventory", {})
        inventory[item] = inventory.get(item, 0) + 1
        room_items.pop(index)
        self.display.text(f"You picked up {entity.get("name") or item}.")
        self.await_input()

    def enter_room(self) -> None:
        room_data = self.world.get_room_data()

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
                if self.is_collectable_entity(entities.get(item, {})):
                    inventory[item] = inventory.get(item, 0) + 1
                else:
                    remaining_items.append(item)
            room_data["items"] = remaining_items
            self.game_data.data["completed"] = True
            self.game_data.save_game_file()

    def move_player(self) -> None:
        """Coordinate exit checks and room entry with the world navigator."""
        self.world.player_move(self.check_conditions, self.enter_room)

    def play_game(self) -> None:
        """Display the loaded game"s introduction and main choice menu."""
        data = self.game_data.data

        self.display.clear_terminal()
        self.display.text(self.display.format(data.get("title") or "Untitled", ansi_format="title"))
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
            self.display.text(f"Current Region: {self.display.format(self.world.get_region_string(), ansi_format="title")}")
            self.display.text(f"Current Room: [{px},{py}]")
            self.display.text(f"{self.world.get_map()}")
            self.await_input()


        def view_inventory() -> None:
            inventory = data.get("player").get("inventory")
            entities = data.get("entities", {})
            inventory_items = list(inventory.items())

            options = {}
            for index, (item, quantity) in enumerate(inventory_items):
                entity_name = entities.get(item, {}).get("name") or item
                options[str(index + 1)] = f"{quantity}x {entity_name}"
            options["0"] = "Back"

            item_menu = text_display.ListMenu(
                "Select an item or return to menu:", options, self.display
            )
            selection = item_menu.get_input()
            if selection == "0":
                return

            item, _ = inventory_items[int(selection) - 1]
            entity = entities.get(item, {})
            room_data = self.world.get_room_data()
            can_drop = not (
                entity.get("droppable", True) is False
                or room_data.get("contain_items", True) is False
            )

            item_name = entity.get("name") or item
            description = entity.get("description") or (
                "No additional information for this item."
            )
            item_options = {}
            option_index = 1
            if can_drop:
                item_options[option_index] = "Drop one"
                option_index += 1

            # TODO Add inventory interactions

            item_options["0"] = "Back"
            drop_selection = text_display.ListMenu(
                item_name, item_options, self.display, description=self.display.format(description, ansi_format="hint")
            ).get_input()
            if drop_selection == "0":
                return

            room_data.setdefault("items", []).append(item)
            if inventory[item] == 1:
                del inventory[item]
            else:
                inventory[item] -= 1
            self.display.text(f"You dropped {entity.get("name") or item}.")
            self.await_input()

        while True:
            self.display.clear_terminal()

            player_has_inventory = bool(data.get("player").get("inventory"))
            room_items = self.world.get_room_items() 

            index = 2

            room_options = {
                "1": "Move",
                "2": "View Location"
            }

            actions = {
                "1": self.move_player,
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

    def run(self, file_path: str | None = None) -> None:
        """Start the specified game or run the main menu loop."""
        if file_path is not None:
            if self.main_menu.load_game(file_path):
                self.play_game()
            return

        self.main_menu.run()
