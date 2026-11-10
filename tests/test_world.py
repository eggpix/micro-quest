"""Tests for room lookup, maps, and player movement."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import game_data
import world as world_module
from tests.support import QueuedMenu, RecordingDisplay


def make_world(data: dict) -> world_module.World:
    display = RecordingDisplay()
    settings = SimpleNamespace(data={"mark_visited": True})
    manager = game_data.GameData(display)
    manager.data = data
    return world_module.World(manager, settings, display)


def connected_world() -> world_module.World:
    return make_world(
        {
            "player": {"region": "start", "room_position": [0, 0]},
            "regions": {
                "start": {
                    "name": "Starting Area",
                    "rooms": {
                        "0,0": {
                            "connections": {
                                "right": {
                                    "region": "next",
                                    "room_position": [1, 0],
                                    "conditions": [{"type": "test"}],
                                    "repeat_condition": False,
                                }
                            }
                        },
                        "1,0": {},
                    },
                },
                "next": {"rooms": {"1,0": {"items": ["coin"]}}},
            },
        }
    )


class WorldTests(unittest.TestCase):
    def test_room_and_region_lookups_use_current_player_location(self) -> None:
        world = connected_world()

        self.assertEqual(world.get_region_string(), "Starting Area")
        self.assertEqual(world.get_room_data()["connections"]["right"]["region"], "next")
        self.assertEqual(world.get_room_items(), [])

    def test_map_marks_player_and_visible_rooms(self) -> None:
        world = connected_world()
        map_text = world.get_map()

        self.assertIn("[x]", map_text)
        self.assertIn("[ ]", map_text)

    def test_move_conditions_block_failed_exit_and_mark_success_once(self) -> None:
        world = connected_world()
        connection = world.get_room_data()["connections"]["right"]
        calls: list[dict] = []

        self.assertFalse(
            world.move_conditions(
                "right", lambda action: calls.append(action) or False
            )
        )
        self.assertNotIn("condition_executed", connection)

        self.assertTrue(
            world.move_conditions(
                "right", lambda action: calls.append(action) or True
            )
        )
        self.assertTrue(connection["condition_executed"])

        self.assertTrue(
            world.move_conditions(
                "right",
                lambda _action: self.fail("A completed one-time check reran."),
            )
        )
        self.assertEqual(len(calls), 2)

    def test_player_move_changes_region_and_enters_destination_room(self) -> None:
        world = connected_world()
        QueuedMenu.prepare("D")
        entered: list[bool] = []

        with patch.object(world_module.text_display, "ListMenu", QueuedMenu):
            world.player_move(lambda _action: True, lambda: entered.append(True))

        self.assertEqual(world.data["player"]["region"], "next")
        self.assertEqual(world.data["player"]["room_position"], [1, 0])
        self.assertEqual(entered, [True])
        self.assertTrue(
            world.data["regions"]["start"]["rooms"]["0,0"]["visited"]
        )

    def test_player_move_does_not_move_when_exit_conditions_fail(self) -> None:
        world = connected_world()
        QueuedMenu.prepare("D")
        entered: list[bool] = []

        with patch.object(world_module.text_display, "ListMenu", QueuedMenu):
            world.player_move(lambda _action: False, lambda: entered.append(True))

        self.assertEqual(world.data["player"]["region"], "start")
        self.assertEqual(world.data["player"]["room_position"], [0, 0])
        self.assertEqual(entered, [])


if __name__ == "__main__":
    unittest.main()
