"""Tests for conditions, events, dialogue, and room interactions."""

import unittest
from unittest.mock import Mock, patch

import game as game_module
from tests.support import QueuedMenu, make_game


def base_data() -> dict:
    return {
        "attributes": {"bell_rung": False},
        "player": {
            "inventory": {"key": 3},
            "attributes": {"health": 10, "code": "246"},
            "region": "tower",
            "room_position": [0, 0],
        },
        "entities": {
            "bell": {
                "attributes": {"inspected": False, "rung": False},
                "inventory": {"coin": 2},
            }
        },
        "regions": {"tower": {"rooms": {"0,0": {"items": ["bell"]}}}},
    }


class GameConditionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.game = make_game(base_data())

    def test_empty_condition_list_passes(self) -> None:
        self.assertTrue(self.game.conditions_met([]))

    def test_attribute_conditions_resolve_regular_and_world_paths(self) -> None:
        self.assertTrue(
            self.game.conditions_met(
                [
                    {
                        "type": "attribute_equals_value",
                        "attribute": "player.attributes.health",
                        "value": 10,
                    },
                    {
                        "type": "attribute_equals_value",
                        "attribute": "world.bell_rung",
                        "value": False,
                    },
                    {
                        "type": "attributes_equal",
                        "attribute": "player.attributes.code",
                        "other_attribute": "player.attributes.code",
                    },
                ]
            )
        )

    def test_missing_or_unknown_attribute_conditions_fail(self) -> None:
        for condition in (
            {
                "type": "attribute_equals_value",
                "attribute": "player.attributes.missing",
                "value": None,
            },
            {
                "type": "attributes_equal",
                "attribute": "player.attributes.health",
                "other_attribute": "missing.value",
            },
            {"type": "not_a_condition"},
        ):
            with self.subTest(condition=condition):
                self.assertFalse(self.game.conditions_met([condition]))

    def test_has_item_supports_exact_and_inclusive_quantity_bounds(self) -> None:
        self.assertTrue(
            self.game.conditions_met(
                [
                    {"type": "has_item", "item": "key", "quantity": 3},
                    {
                        "type": "has_item",
                        "item": "coin",
                        "object": "entities.bell",
                        "min_quantity": 2,
                        "max_quantity": 2,
                    },
                ]
            )
        )
        self.assertFalse(
            self.game.conditions_met(
                [{"type": "has_item", "item": "key", "quantity": 2}]
            )
        )

    def test_invalid_item_condition_fails_safely(self) -> None:
        invalid_conditions = (
            {"type": "has_item", "item": ""},
            {"type": "has_item", "item": "key", "quantity": True},
            {"type": "has_item", "item": "key", "min_quantity": 4, "max_quantity": 2},
        )
        for condition in invalid_conditions:
            with self.subTest(condition=condition):
                self.assertFalse(self.game.conditions_met([condition]))

    def test_failed_condition_shows_failure_and_skips_events(self) -> None:
        action = {
            "conditions": [
                {
                    "type": "attribute_equals_value",
                    "attribute": "entities.bell.attributes.inspected",
                    "value": True,
                }
            ],
            "failure": {"message": "Inspect first."},
            "success": {
                "message": "Rung.",
                "events": {
                    "type": "set_attribute",
                    "target": "entities.bell.attributes.rung",
                    "value": True,
                },
            },
        }

        self.assertFalse(self.game.check_conditions(action))
        self.assertEqual(self.game.dialogue, ["Inspect first."])
        self.assertFalse(self.game.game_data.data["entities"]["bell"]["attributes"]["rung"])

    def test_successful_condition_shows_message_and_runs_nested_events(self) -> None:
        self.game.game_data.data["entities"]["bell"]["attributes"]["inspected"] = True
        action = {
            "conditions": [
                {
                    "type": "attribute_equals_value",
                    "attribute": "entities.bell.attributes.inspected",
                    "value": True,
                }
            ],
            "success": {
                "message": "Rung.",
                "events": {
                    "type": "set_attribute",
                    "target": "entities.bell.attributes.rung",
                    "value": True,
                },
            },
        }

        self.assertTrue(self.game.check_conditions(action))
        self.assertEqual(self.game.dialogue, ["Rung."])
        self.assertTrue(self.game.game_data.data["entities"]["bell"]["attributes"]["rung"])

    def test_top_level_events_remain_supported_with_conditions(self) -> None:
        action = {
            "conditions": [],
            "events": {
                "type": "set_attribute",
                "target": "world.bell_rung",
                "value": True,
            },
        }

        self.assertTrue(self.game.check_conditions(action))
        self.assertTrue(self.game.game_data.data["attributes"]["bell_rung"])


class GameEventTests(unittest.TestCase):
    def setUp(self) -> None:
        self.game = make_game(base_data())

    def test_set_attribute_creates_missing_objects_and_supports_world_alias(self) -> None:
        self.game.apply_events(
            [
                {
                    "type": "set_attribute",
                    "target": "entities.bell.attributes.inspected",
                    "value": True,
                },
                {
                    "type": "set_attribute",
                    "target": "world.new_flag",
                    "value": "set",
                },
            ]
        )

        self.assertTrue(self.game.game_data.data["entities"]["bell"]["attributes"]["inspected"])
        self.assertEqual(self.game.game_data.data["attributes"]["new_flag"], "set")

    def test_remove_item_removes_only_the_named_inventory_item(self) -> None:
        self.game.apply_events({"type": "remove_item", "item": "key"})

        self.assertNotIn("key", self.game.game_data.data["player"]["inventory"])

    def test_modify_attribute_performs_arithmetic(self) -> None:
        self.game.apply_events(
            [
                {
                    "type": "modify_attribute",
                    "target": "player.attributes.health",
                    "operation": "+",
                    "value": 2.5,
                },
                {
                    "type": "modify_attribute",
                    "target": "player.attributes.health",
                    "operation": "*",
                    "value": 2,
                },
            ]
        )

        self.assertEqual(self.game.game_data.data["player"]["attributes"]["health"], 25)

    def test_invalid_modify_attribute_does_not_change_data(self) -> None:
        self.game.apply_events(
            {
                "type": "modify_attribute",
                "target": "player.attributes.health",
                "operation": "/",
                "value": 0,
            }
        )

        self.assertEqual(self.game.game_data.data["player"]["attributes"]["health"], 10)
        self.assertTrue(
            any("Error:" in text for text in self.game.display.messages)
        )

    def test_input_event_stores_typed_value_and_formats_response(self) -> None:
        self.game.loop_dialogue = game_module.Game.loop_dialogue.__get__(
            self.game, game_module.Game
        )
        with patch("builtins.input", return_value="42"):
            self.game.apply_events(
                {
                    "type": "input",
                    "target": "player.attributes.age",
                    "input_type": "integer",
                    "prompt": "Age?",
                    "min": 1,
                    "max": 100,
                    "response": "Recorded {player.attributes.age}.",
                }
            )

        self.assertEqual(self.game.game_data.data["player"]["attributes"]["age"], 42)
        self.assertIn("Recorded 42.", self.game.display.messages)


class GameInteractionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.game = make_game(base_data())
        self.game.world = type(
            "TestWorld",
            (),
            {"get_room_items": lambda _world: self.game.game_data.data["regions"]["tower"]["rooms"]["0,0"]["items"]},
        )()
        self.game.entities = self.game.game_data.data["entities"]

    def _select(self, *selections: str) -> None:
        QueuedMenu.prepare(*selections)

    def test_conditioned_interaction_requires_inspection_before_ringing(self) -> None:
        bell = self.game.game_data.data["entities"]["bell"]
        bell["name"] = "Bell"
        bell["interactions"] = {
            "inspect": {
                "name": "Inspect",
                "message": "You inspect the bell.",
                "events": {
                    "type": "set_attribute",
                    "target": "entities.bell.attributes.inspected",
                    "value": True,
                },
            },
            "ring": {
                "name": "Ring",
                "conditions": [
                    {
                        "type": "attribute_equals_value",
                        "attribute": "entities.bell.attributes.inspected",
                        "value": True,
                    }
                ],
                "success": {
                    "message": "The bell rings.",
                    "events": {
                        "type": "set_attribute",
                        "target": "entities.bell.attributes.rung",
                        "value": True,
                    },
                },
                "failure": {"message": "Inspect it first."},
            },
        }
        with patch.object(game_module.text_display, "ListMenu", QueuedMenu):
            self._select("1", "2")
            self.game.view_room_items()
            self.assertFalse(bell["attributes"]["rung"])
            self.assertEqual(self.game.dialogue, ["Inspect it first."])

            self._select("1", "1")
            self.game.view_room_items()
            self.assertTrue(bell["attributes"]["inspected"])

            self._select("1", "2")
            self.game.view_room_items()

        self.assertTrue(bell["attributes"]["rung"])
        self.assertEqual(self.game.dialogue[-1], "The bell rings.")

    def test_dialogue_choices_are_filtered_and_events_apply(self) -> None:
        entity = {
            "name": "Sailor",
            "dialogue": {
                "start": {
                    "message": "Choose a response.",
                    "choices": [
                        {
                            "text": "Locked choice",
                            "conditions": [
                                {
                                    "type": "attribute_equals_value",
                                    "attribute": "player.attributes.health",
                                    "value": 0,
                                }
                            ],
                        },
                        {
                            "text": "Open choice",
                            "events": {
                                "type": "set_attribute",
                                "target": "player.attributes.talked",
                                "value": True,
                            },
                        },
                    ],
                }
            },
        }
        QueuedMenu.prepare("1")

        with patch.object(game_module.text_display, "ListMenu", QueuedMenu):
            self.game.run_dialogue_tree(
                entity, {"start_node": "start"}, "sailor"
            )

        self.assertEqual(QueuedMenu.instances[0].options, {
            "1": "Open choice",
            "0": "End conversation",
        })
        self.assertTrue(self.game.game_data.data["player"]["attributes"]["talked"])


class RoomEntryTests(unittest.TestCase):
    def test_non_repeating_room_message_is_marked_played(self) -> None:
        data = base_data()
        room = data["regions"]["tower"]["rooms"]["0,0"]
        room["message"] = {
            "text": "You enter the tower.",
            "repeat": False,
            "played": False,
        }
        instance = make_game(data)
        instance.world = type(
            "TestWorld", (), {"get_room_data": lambda _world: room}
        )()

        instance.enter_room()
        instance.enter_room()

        self.assertEqual(instance.dialogue, ["You enter the tower."])
        self.assertTrue(room["message"]["played"])

    def test_ending_collects_collectables_and_saves_completion(self) -> None:
        data = base_data()
        room = data["regions"]["tower"]["rooms"]["0,0"]
        room.update({"ending": True, "items": ["gem", "statue"]})
        data["entities"].update(
            {
                "gem": {"collectable": True},
                "statue": {"item": False, "collectable": True},
            }
        )
        instance = make_game(data)
        instance.world = type(
            "TestWorld", (), {"get_room_data": lambda _world: room}
        )()
        instance.game_data.save_game_file = Mock(return_value=True)

        instance.enter_room()

        self.assertTrue(data["completed"])
        self.assertEqual(data["player"]["inventory"]["gem"], 1)
        self.assertEqual(room["items"], ["statue"])
        instance.game_data.save_game_file.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
