"""Application flow for Micro Quest."""

import math
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
        self.world = world.World(
            self.game_data,
            self.config,
            self.display
        )

    def await_input(self) -> None:
        """Pause until the player presses Enter."""
        try:
            input(
                f"{self.display.format('[Enter]', ansi_format='key')} to continue... "
            )
        except EOFError:
            return

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
                case "attribute_equals_value":
                    attribute = condition.get("attribute")
                    if not isinstance(attribute, str):
                        return False
                    found, actual_value = self.get_attribute_value(attribute)
                    if not found or actual_value != condition.get("value"):
                        return False
                case "attributes_equal":
                    attribute = condition.get("attribute")
                    other_attribute = condition.get("other_attribute")
                    if not isinstance(attribute, str) or not isinstance(other_attribute, str):
                        return False

                    found, actual_value = self.get_attribute_value(attribute)
                    other_found, other_value = self.get_attribute_value(other_attribute)
                    if not found or not other_found or actual_value != other_value:
                        return False
                case _:
                    return False

        return True

    def check_conditions(self, condition_parent: dict) -> bool:
        """Evaluate conditions and run their associated messages and events."""
        if not self.conditions_met(condition_parent.get("conditions", [])):
            failure = condition_parent.get("failure")
            failure_dialogue = (
                failure.get("message") if isinstance(failure, dict) else None
            )
            if failure_dialogue:
                self.loop_dialogue(failure_dialogue)
            return False

        success = condition_parent.get("success")
        if isinstance(success, dict):
            success_dialogue = success.get("message")
            if success_dialogue:
                self.loop_dialogue(success_dialogue)

        events = condition_parent.get("events")
        if isinstance(success, dict) and "events" in success:
            events = success["events"]
        self.apply_events(events)
        return True

    def get_player_input(self, event: dict) -> tuple[bool, object]:
        """Prompt for and validate a typed value described by an input event."""
        input_type = event.get("input_type", "string")
        prompt = event.get("prompt", "Enter a value:")
        if input_type not in ("string", "integer", "number", "boolean", "choice"):
            self.display.text(
                self.display.format(
                    f"Error: Unsupported input_type '{input_type}'.",
                    ansi_format="error",
                )
            )
            return False, None
        if not isinstance(prompt, str):
            self.display.text(
                self.display.format(
                    "Error: input prompt must be a string.",
                    ansi_format="error",
                )
            )
            return False, None

        minimum = event.get("min")
        maximum = event.get("max")
        if input_type in ("integer", "number"):
            valid_bounds = all(
                value is None
                or (
                    isinstance(value, (int, float))
                    and not isinstance(value, bool)
                    and (
                        not isinstance(value, float)
                        or math.isfinite(value)
                    )
                    and (input_type != "integer" or isinstance(value, int))
                )
                for value in (minimum, maximum)
            )
            if (
                not valid_bounds
                or minimum is not None
                and maximum is not None
                and minimum > maximum
            ):
                self.display.text(
                    self.display.format(
                        f"Error: Invalid {input_type} input bounds.",
                        ansi_format="error",
                    )
                )
                return False, None
        elif minimum is not None or maximum is not None:
            self.display.text(
                self.display.format(
                    "Error: min and max can only be used with integer or number input.",
                    ansi_format="error",
                )
            )
            return False, None

        choices = event.get("choices")
        if input_type == "choice":
            if (
                not isinstance(choices, list)
                or not choices
                or any(not isinstance(choice, str) or not choice for choice in choices)
            ):
                self.display.text(
                    self.display.format(
                        "Error: choice input requires a non-empty list of strings.",
                        ansi_format="error",
                    )
                )
                return False, None
        elif choices is not None:
            self.display.text(
                self.display.format(
                    "Error: choices can only be used with choice input.",
                    ansi_format="error",
                )
            )
            return False, None

        while True:
            self.display.text(self.format_text(prompt))
            if input_type == "choice":
                for index, choice in enumerate(choices, start=1):
                    self.display.text(f"[{index}] {self.format_text(choice)}")
            try:
                raw_value = input("> ").strip()
            except EOFError:
                return False, None

            try:
                match input_type:
                    case "string":
                        value = raw_value
                    case "integer":
                        value = int(raw_value)
                    case "number":
                        value = float(raw_value)
                        if not math.isfinite(value):
                            raise ValueError
                    case "boolean":
                        match raw_value.lower():
                            case "y" | "yes":
                                value = True
                            case "n" | "no":
                                value = False
                            case _:
                                raise ValueError
                    case "choice":
                        value = next(
                            choice
                            for index, choice in enumerate(choices, start=1)
                            if choice.casefold() == raw_value.casefold()
                            or str(index) == raw_value
                        )
            except (StopIteration, ValueError):
                self.display.text(
                    self.display.format(
                        "Invalid input. Please try again.",
                        ansi_format="error",
                    )
                )
                continue

            if input_type in ("integer", "number") and (
                minimum is not None and value < minimum
                or maximum is not None and value > maximum
            ):
                self.display.text(
                    self.display.format(
                        "Input is outside the allowed range. Please try again.",
                        ansi_format="error",
                    )
                )
                continue
            return True, value

    def apply_events(self, events: dict | list[dict] | None) -> None:
        """Apply game events shared by connections and entity interactions."""
        data = self.game_data.data
        player_data = data.get("player")
        if events:
            if isinstance(events, dict):
                events = [events]
            for event in events:
                if not isinstance(event, dict):
                    self.display.text(
                        self.display.format(
                            "Error: Each event must be an object.",
                            ansi_format="error",
                        )
                    )
                    continue
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

                        member = data
                        for key in path[:-1]:
                            child = member.get(key)
                            if not isinstance(child, dict):
                                child = {}
                                member[key] = child
                            member = child
                        member[path[-1]] = event.get("value")
                    case "input":
                        target = event.get("target")
                        if not isinstance(target, str) or not target:
                            self.display.text(
                                self.display.format(
                                    "Error: input requires a target path.",
                                    ansi_format="error",
                                )
                            )
                            continue

                        path = self.get_data_path(target)
                        if path is None or len(path) < 2:
                            self.display.text(
                                self.display.format(
                                    f"Error: Invalid input target '{target}'.",
                                    ansi_format="error",
                                )
                            )
                            continue

                        valid, value = self.get_player_input(event)
                        if not valid:
                            continue

                        member = data
                        for key in path[:-1]:
                            child = member.get(key)
                            if not isinstance(child, dict):
                                child = {}
                                member[key] = child
                            member = child
                        member[path[-1]] = value

                        response = event.get("response")
                        if response:
                            if not isinstance(response, (str, list)):
                                self.display.text(
                                    self.display.format(
                                        "Error: input response must be a string or list of strings.",
                                        ansi_format="error",
                                    )
                                )
                            elif isinstance(response, list) and any(
                                not isinstance(line, str) for line in response
                            ):
                                self.display.text(
                                    self.display.format(
                                        "Error: input response must contain only strings.",
                                        ansi_format="error",
                                    )
                                )
                            else:
                                self.loop_dialogue(response)
                    case "modify_attribute":
                        target = event.get("target")
                        if not isinstance(target, str) or not target:
                            self.display.text(
                                self.display.format(
                                    "Error: modify_attribute requires a target path.",
                                    ansi_format="error",
                                )
                            )
                            continue

                        operation = event.get("operation")
                        if operation not in ("+", "-", "*", "/"):
                            self.display.text(
                                self.display.format(
                                    "Error: modify_attribute operation must be "
                                    "+, -, *, or /.",
                                    ansi_format="error",
                                )
                            )
                            continue

                        value = event.get("value")
                        if (
                            isinstance(value, bool)
                            or not isinstance(value, (int, float))
                            or isinstance(value, float)
                            and not math.isfinite(value)
                        ):
                            self.display.text(
                                self.display.format(
                                    "Error: modify_attribute value must be a "
                                    "finite number.",
                                    ansi_format="error",
                                )
                            )
                            continue

                        path = self.get_data_path(target)
                        if path is None or len(path) < 2:
                            self.display.text(
                                self.display.format(
                                    f"Error: Invalid modify_attribute target '{target}'.",
                                    ansi_format="error",
                                )
                            )
                            continue

                        member = data
                        valid_target = True
                        for key in path[:-1]:
                            if not isinstance(member, dict) or key not in member:
                                valid_target = False
                                break
                            member = member[key]

                        if (
                            not valid_target
                            or not isinstance(member, dict)
                            or path[-1] not in member
                        ):
                            self.display.text(
                                self.display.format(
                                    f"Error: modify_attribute target '{target}' "
                                    "does not exist.",
                                    ansi_format="error",
                                )
                            )
                            continue

                        current_value = member[path[-1]]
                        if (
                            isinstance(current_value, bool)
                            or not isinstance(current_value, (int, float))
                            or isinstance(current_value, float)
                            and not math.isfinite(current_value)
                        ):
                            self.display.text(
                                self.display.format(
                                    f"Error: modify_attribute target '{target}' "
                                    "must contain a finite number.",
                                    ansi_format="error",
                                )
                            )
                            continue

                        if operation == "/" and value == 0:
                            self.display.text(
                                self.display.format(
                                    "Error: modify_attribute cannot divide by zero.",
                                    ansi_format="error",
                                )
                            )
                            continue

                        try:
                            match operation:
                                case "+":
                                    result = current_value + value
                                case "-":
                                    result = current_value - value
                                case "*":
                                    result = current_value * value
                                case "/":
                                    result = current_value / value
                        except ArithmeticError as error:
                            self.display.text(
                                self.display.format(
                                    f"Error: Could not modify '{target}': {error}.",
                                    ansi_format="error",
                                )
                            )
                            continue

                        if isinstance(result, float) and not math.isfinite(result):
                            self.display.text(
                                self.display.format(
                                    f"Error: modify_attribute result for '{target}' "
                                    "is not finite.",
                                    ansi_format="error",
                                )
                            )
                            continue

                        member[path[-1]] = result

    def is_collectable_entity(self, entity: dict) -> bool:
        """Return whether an entity can be picked up into inventory."""
        return (
            entity.get("collectable") is True
            and entity.get("item", True) is not False
        )

    def run_dialogue_tree(
        self, entity: dict, interaction: dict, entity_id: str
    ) -> None:
        """Run an NPC conversation whose choices lead between named nodes."""
        nodes = entity.get("dialogue")
        node_id = interaction.get("start_node")
        if (
            not isinstance(nodes, dict)
            or not isinstance(node_id, str)
            or not node_id
        ):
            self.display.text(
                self.display.format(
                    f"Error: Invalid dialogue tree for '{entity_id}'.",
                    ansi_format="error",
                )
            )
            return

        while True:
            node = nodes.get(node_id)
            if not isinstance(node, dict):
                self.display.text(
                    self.display.format(
                        f"Error: Dialogue node '{node_id}' not found for "
                        f"'{entity_id}'.",
                        ansi_format="error",
                    )
                )
                return

            message = node.get("message")
            if isinstance(message, str):
                self.loop_dialogue(message)
            elif (
                isinstance(message, list)
                and all(isinstance(line, str) for line in message)
            ):
                self.loop_dialogue(message)
            else:
                self.display.text(
                    self.display.format(
                        f"Error: Dialogue node '{node_id}' for '{entity_id}' "
                        "needs a message string or list of strings.",
                        ansi_format="error",
                    )
                )
                return

            choices = node.get("choices", [])
            if not isinstance(choices, list) or not all(
                isinstance(choice, dict) for choice in choices
            ):
                self.display.text(
                    self.display.format(
                        f"Error: Choices for dialogue node '{node_id}' must "
                        "be a list of objects.",
                        ansi_format="error",
                    )
                )
                return

            available_choices = []
            for choice in choices:
                choice_text = choice.get("text")
                next_node = choice.get("next")
                conditions = choice.get("conditions", [])
                if (
                    not isinstance(choice_text, str)
                    or not choice_text
                    or (
                        next_node is not None
                        and (not isinstance(next_node, str) or not next_node)
                    )
                    or not isinstance(conditions, list)
                    or not all(isinstance(condition, dict) for condition in conditions)
                ):
                    self.display.text(
                        self.display.format(
                            f"Error: Invalid choice in dialogue node "
                            f"'{node_id}' for '{entity_id}'.",
                            ansi_format="error",
                        )
                    )
                    return

                if self.conditions_met(conditions):
                    available_choices.append(choice)

            if not available_choices:
                return

            options = {
                str(index + 1): choice["text"]
                for index, choice in enumerate(available_choices)
            }
            options["0"] = "End conversation"
            selection = text_display.ListMenu(
                entity.get("name") or entity_id, options, self.display
            ).get_input()
            if selection == "0":
                return

            selected_choice = available_choices[int(selection) - 1]
            self.apply_events(selected_choice.get("events"))
            next_node = selected_choice.get("next")
            if next_node is None:
                return
            node_id = next_node

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
                action = entity_name

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

            description = entity.get("description") or (
                "No additional information for this item."
            )
            interaction_selection = text_display.ListMenu(
                entity_name,
                interaction_options,
                self.display,
                description=self.display.format(description, ansi_format="hint"),
            ).get_input()
            if interaction_selection == "0":
                return

            if interaction_selection == pickup_option:
                self.collect_room_item(index, item, entity)
                return

            interaction = list(interactions.values())[
                int(interaction_selection) - 1
            ]
            if "start_node" in interaction:
                self.run_dialogue_tree(entity, interaction, item)
            elif any(
                key in interaction
                for key in ("conditions", "success", "failure")
            ):
                if not self.check_conditions(interaction):
                    return

                success = interaction.get("success")
                if not (
                    isinstance(success, dict) and success.get("message")
                ):
                    message = interaction.get("message")
                    if message:
                        self.loop_dialogue(message)
            else:
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
            description = entity.get("description") or (
                "No additional information for this item."
            )
            text_display.ListMenu(
                entity_name,
                {"0": "Back"},
                self.display,
                description=self.display.format(description, ansi_format="hint"),
            ).get_input()
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

        if data.get("on_start") and not data.get("on_start_executed", False):
            self.apply_events(data["on_start"])
            data["on_start_executed"] = True
            self.game_data.save_game_file()

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
