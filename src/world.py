"""Handle game world"""

# MAP SIZE centered on player position, must be an odd number
MAP_SIZE = 7

class World:
    """Handle game world"""
    def __init__(self, game_data, display):
        self.game_data = game_data
        self.display = display

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
        connection_offsets: dict[str, tuple[int, int]] = {
            "up": (0, -1),
            "down": (0, 1),
            "left": (-1, 0),
            "right": (1, 0),
        }
        map_connections: dict[tuple[int, int], tuple[str, object, bool]] = {}
        map_errors: list[str] = []

        map_left = room_position[0] - MAP_SIZE // 2
        map_right = room_position[0] + MAP_SIZE // 2
        map_top = room_position[1] - MAP_SIZE // 2
        map_bottom = room_position[1] + MAP_SIZE // 2

        for y in range(map_top - 1, map_bottom + 2):
            for x in range(map_left - 1, map_right + 2):
                source_room = rooms.get(f"{x},{y}", {})
                for direction, connection in (
                    source_room.get("connections") or {}
                ).items():
                    if connection.get("show_in_map") is True:
                        offset = connection_offsets.get(direction)
                        if offset is not None:
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

        map_str = ""

        for y in range(
            room_position[1] - MAP_SIZE // 2,
            room_position[1] + MAP_SIZE // 2 + 1
        ):
            for x in range(
                room_position[0] - MAP_SIZE // 2,
                room_position[0] + MAP_SIZE // 2 + 1
            ):
                position = (x, y)
                if [x, y] == room_position:
                    map_str += "[x]"
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
                                    f"Error: Invalid map_color for the "
                                    f"{direction} connection: {error}",
                                    ansi_format="error"
                                )
                            )
                    map_str += cell
                elif f"{x},{y}" in rooms:
                    map_str += "[ ]"
                else:
                    map_str += self.display.format(" . ", ansi_format="grid")

            map_str += "\n"

        if map_errors:
            map_str += "\n".join(map_errors) + "\n"

        return map_str

    def get_room_data(self) -> dict:
        data = self.game_data.data
        player_data = data.get("player")
        region = player_data["region"]
        room_position = player_data["room_position"]
        return data.get("regions").get(region).get("rooms").get(f"{room_position[0]},{room_position[1]}")

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
        """Return a connection"s explicit destination or its adjacent room."""
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
                if destination_region != player_data["region"]:
                    destination_name = (
                        self.game_data.data.get("regions", {})
                        .get(destination_region, {})
                        .get("name")
                        or destination_region
                    )
                    label = f"{label} (To {destination_name})"
                direction_options[key] = label

        direction_options["0"] = "Cancel"

        self.display.clear_terminal()

        direction_menu = text_display.ListMenu(
            "Choose a Direction to Move:",
            direction_options,
            self.display,
            description=self.get_map()
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
