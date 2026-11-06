"""World navigation and map operations for Micro Quest."""

from collections.abc import Callable
from typing import Any

import game_data
import text_display

# An odd map size keeps the player's room centered.
MAP_SIZE = 7

CONNECTION_OFFSETS: dict[str, tuple[int, int]] = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}

DIRECTIONS: dict[str, tuple[str, tuple[int, int]]] = {
    "W": ("up", (0, -1)),
    "A": ("left", (-1, 0)),
    "S": ("down", (0, 1)),
    "D": ("right", (1, 0)),
}

ConditionChecker = Callable[[dict[str, Any]], bool]
RoomEntryHandler = Callable[[], None]


class World:
    """Provide map, room, and movement operations for the current game."""

    def __init__(
        self,
        game_data_manager: game_data.GameData,
        display: text_display.TextDisplay,
    ) -> None:
        self.game_data = game_data_manager
        self.display = display

    @property
    def data(self) -> dict[str, Any]:
        """Return loaded game data, raising a clear error if none is loaded."""
        if self.game_data.data is None:
            raise RuntimeError("No game data is loaded.")
        return self.game_data.data

    def get_player_region(self) -> dict[str, Any]:
        """Return the region the player currently occupies."""
        player = self.data.get("player", {})
        return self.data.get("regions", {}).get(player.get("region"), {})

    def get_region_string(self) -> str:
        """Return the current region's display name or its identifier."""
        player = self.data.get("player", {})
        region_id = player.get("region")
        return self.get_player_region().get("name") or region_id

    def get_map(self) -> str:
        """Render the rooms and visible connections around the player."""
        player = self.data.get("player", {})
        room_position = player["room_position"]
        rooms = self.get_player_region().get("rooms", {})

        map_left = room_position[0] - MAP_SIZE // 2
        map_right = room_position[0] + MAP_SIZE // 2
        map_top = room_position[1] - MAP_SIZE // 2
        map_bottom = room_position[1] + MAP_SIZE // 2

        map_connections: dict[
            tuple[int, int], tuple[str, Any, bool]
        ] = {}
        map_errors: list[str] = []

        for y in range(map_top - 1, map_bottom + 2):
            for x in range(map_left - 1, map_right + 2):
                source_room = rooms.get(f"{x},{y}", {})
                connections = source_room.get("connections") or {}
                for direction, connection in connections.items():
                    if connection.get("show_in_map") is not True:
                        continue

                    offset = CONNECTION_OFFSETS.get(direction)
                    if offset is None:
                        continue

                    position = (x + offset[0], y + offset[1])
                    if (
                        map_left <= position[0] <= map_right
                        and map_top <= position[1] <= map_bottom
                    ):
                        map_connections[position] = (
                            direction,
                            connection.get("map_color"),
                            "map_color" in connection,
                        )

        rows: list[str] = []
        for y in range(map_top, map_bottom + 1):
            cells: list[str] = []
            for x in range(map_left, map_right + 1):
                position = (x, y)
                if [x, y] == room_position:
                    cells.append("[x]")
                elif position in map_connections:
                    direction, color, has_color = map_connections[position]
                    cell = "[ ]"
                    if has_color:
                        try:
                            cell = (
                                self.display.color_foreground("[", color)
                                + " "
                                + self.display.color_foreground("]", color)
                            )
                        except ValueError as error:
                            map_errors.append(
                                self.display.format(
                                    "Error: Invalid map_color for the "
                                    f"{direction} connection: {error}",
                                    ansi_format="error",
                                )
                            )
                    cells.append(cell)
                elif f"{x},{y}" in rooms:
                    cells.append("[ ]")
                else:
                    cells.append(
                        self.display.format(" . ", ansi_format="grid")
                    )

            rows.append("".join(cells))

        map_text = "\n".join(rows) + "\n"
        if map_errors:
            map_text += "\n".join(map_errors) + "\n"
        return map_text

    def get_room_data(self) -> dict[str, Any]:
        """Return the room at the player's current region and position."""
        player = self.data.get("player", {})
        region_id = player["region"]
        x, y = player["room_position"]
        return (
            self.data.get("regions", {})
            .get(region_id, {})
            .get("rooms", {})
            .get(f"{x},{y}", {})
        )

    def move_conditions(
        self,
        direction: str,
        check_conditions: ConditionChecker,
    ) -> bool:
        """Check any condition or event attached to an exit before moving."""
        connections = self.get_room_data().get("connections") or {}
        connection = connections.get(direction, {})
        has_connection_actions = bool(
            connection.get("conditions")
            or connection.get("success")
            or connection.get("events")
        )
        if not has_connection_actions:
            return True

        repeat_condition = connection.get("repeat_condition", True)
        if not repeat_condition and connection.get("condition_executed", False):
            return True

        if not check_conditions(connection):
            return False

        if not repeat_condition:
            connection["condition_executed"] = True
        return True

    def get_connection_destination(
        self,
        direction: str,
        offset: tuple[int, int],
    ) -> tuple[str, list[int]]:
        """Return an exit's explicit destination or its adjacent room."""
        player = self.data.get("player", {})
        connection = (
            self.get_room_data().get("connections") or {}
        ).get(direction, {})
        current_position = player["room_position"]
        destination_region = connection.get("region", player["region"])
        destination_position = connection.get("room_position")

        if destination_position is None:
            destination_position = [
                current_position[0] + offset[0],
                current_position[1] + offset[1],
            ]

        return destination_region, destination_position

    def get_room_items(self) -> list[str]:
        """Return the item identifiers in the current room."""
        return self.get_room_data().get("items", [])

    def player_move(
        self,
        check_conditions: ConditionChecker,
        enter_room: RoomEntryHandler,
    ) -> None:
        """Prompt for a valid exit and move the player when allowed."""
        player = self.data.get("player", {})
        room_position = player["room_position"]
        rooms = self.get_player_region().get("rooms", {})
        current_room = rooms.get(f"{room_position[0]},{room_position[1]}", {})
        blocked_directions = current_room.get("block", [])

        direction_options: dict[str, str] = {}
        for key, (label, offset) in DIRECTIONS.items():
            if label in blocked_directions:
                continue

            destination_region, destination_position = (
                self.get_connection_destination(label, offset)
            )
            destination_rooms = (
                self.data.get("regions", {})
                .get(destination_region, {})
                .get("rooms", {})
            )
            destination_key = (
                f"{destination_position[0]},{destination_position[1]}"
            )
            if destination_key not in destination_rooms:
                continue

            if destination_region != player["region"]:
                destination_name = (
                    self.data.get("regions", {})
                    .get(destination_region, {})
                    .get("name")
                    or destination_region
                )
                label = f"{label.title()} (To {destination_name})"
            else:
                label = label.title()
            direction_options[key] = label

        direction_options["0"] = "Cancel"
        self.display.clear_terminal()

        menu = text_display.ListMenu(
            "Choose a Direction to Move:",
            direction_options,
            self.display,
            description=self.get_map(),
        )
        selection = menu.get_input().upper()
        if selection == "0":
            return

        direction, offset = DIRECTIONS[selection]
        if not self.move_conditions(direction, check_conditions):
            return

        destination_region, destination_position = (
            self.get_connection_destination(direction, offset)
        )
        player["region"] = destination_region
        player["room_position"] = destination_position
        enter_room()
