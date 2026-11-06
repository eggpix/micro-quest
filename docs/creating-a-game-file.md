# Creating a Game File

Micro Quest is a text-based adventure game engine. Each game is stored in one
JSON file containing its story, regions, rooms, player, and entities. Follow
this guide to create a game, test it, and prepare a template for sharing.

## Before You Start

It is recommended that you follow this guide step-by-step before diving into the reference. The following sections cover a few important details about game files. Please read them carefully.

### Terminology

- **JSON** — The file format used by Micro Quest to store game information. Information about JSON files and how to format them can be found in the [official json.org website](https://www.json.org/json-en.html).
- **Object** — A collection of key/value pairs. Functions similarly to a Python dictionary, with each key associated with a value.
- **Member** — A key/value pair within a JSON object. The key identifies the member, while the value contains its associated data.

### Game Status

Set `"status"` to `"template"` before sharing a new game. When a template is
loaded, Micro Quest asks for a new save-file path and creates an `"active"`
copy, leaving the template unchanged. Active files are played and saved in
place, so make a backup before experimenting with an active game.

### Core JSON Members

A playable game needs a `"player"` with a starting `"region"` and
`"room_position"`, plus a `"regions"` object containing that region and room.
Other members below are recommended; the engine uses fallbacks for the title
and description.

- `"title"` — The game title. Defaults to `"Untitled"` if omitted.
- `"description"` — Introductory text displayed below the title. Defaults to
  an empty string.
- `"status"` — Set to `"template"` before sharing to ensure players get a
  separate save file. Other values are loaded directly as active files.
- `"player"` — Player data, including the starting region and room.
- `"regions"` — Regions and their rooms. Each room key is its coordinate in
  `"x,y"` form.
- `"entities"` — Optional root-level definitions for items used in rooms or
  inventory.

### Naming Conventions

For consistency, it is recommended to name your keys using *snake case*, where words are lowercase and separated by underscores. When possible, give all keys a unique value to avoid confusion. Using a key twice within the same object may result in unpredictable behavior and should always be avoided.

**Example:** `"door_key_0"`

## Quickstart

1. Create a JSON file using the minimal example in Step 1 below.
2. Set the player's starting region and room, and make sure that room exists.
3. Add a room message, items, or exits by following the steps in this guide.
4. From the repository directory, run `python src/main.py` and choose **Load
   Game**, or start a file directly with
   `python src/main.py --file path/to/your_game.json`.
5. To share the game without sharing your save, set `"status": "template"`.
   Micro Quest will create a separate active save when the template is loaded.

See the [README](../README.md) for running the engine.

## 1. Create a Minimal Game

The smallest useful game has one room and an unnamed player starting there:

```json
{
    "title": "Castle Game",
    "description": "A game about castles.",
    "status": "template",
    "player": {
        "region": "fountain",
        "room_position": [0,0]
    },
    "regions": {
        "fountain": {
            "rooms": {
                "0,0": {}
            }
        }
    }
}
```

Copy this into a `.json` file to create a playable starting point. The player
can move only after you add more rooms.

## 2. Customize the Player

Let's try adding some extra information to the player object. We can start by adding a `"name"` member which holds a string.

```json
"player": {
    "name": "Jane",
    "region": "fountain",
    "room_position": [0,0]
},
```

By default, this member won't affect game behavior, but it can be inserted
into dialogue using a placeholder:

```json
"message": {
    "text": "Hello, {player.name}!"
}
```

See [Use values in dialogue](#7-use-values-in-dialogue) for placeholder rules.

Let's add an inventory for the player. The `"inventory"` key will be processed by the game interpreter as a dictionary holding all of the player's items. Each item is formatted as `key: amount`.

```json
"player": {
    "name": "Jane",
    "region": "fountain",
    "room_position": [0,0],
    "inventory": {
        "cake": 1
    }
},
```

By default, `"cake"` doesn't have any meaning. The key must refer back to an *entity*, which is listed in another object. We'll explore entities later. For now, this cake doesn't mean anything and won't be recognized by the game engine.

> **Remember:** JSON objects are unordered. It doesn't matter in what order the player members are, as long as the information stays the same.

## 3. Add a Room

Now that we have a simple player object, let's create more rooms for the player to explore. Right now we have a single `"fountain"` region. Let's start by giving it a name.

```json
"regions": {
    "fountain": {
        "name": "Castle Fountain",
        "rooms": {
            "0,0": {}
        }
    }
}
```

Without a name, the game engine will simply display the player location as the region key. That may be fine for some regions, but it's useful to add proper capitalization and follow standard title conventions.

Next, we can add some extra rooms.

```json
"regions": {
    "fountain": {
        "name": "Castle Fountain",
        "rooms": {
            "0,0": {},
            "0,-1": {},
            "1,0": {},
            "1,-1": {},
            "2,0": {},
            "2,-1": {},
            "2,-2": {}
        }
    }
}
```

Each room is stored as a square in a grid of rooms. It's displayed this way when the player gets their location map. Right now, the player is free to move to any adjacent rooms. We can restrict movement in a certain direction using the `"block"` member:

```json
"regions": {
    "fountain": {
        "name": "Castle Fountain",
        "rooms": {
            "0,0": {},
            "0,-1": {
                "block": ["right"]
            },
            "1,0": {
                "block": ["up"]
            },
            "1,-1": {
                "block": ["down", "left"]
            },
            "2,0": {},
            "2,-1": {},
            "2,-2": {}
        }
    }
}
```

Adding the `"block"` member to a room restricts the player from moving in that direction. Note that blocks do not apply in both directions; to block a player from moving back, you must add a second block in the opposite direction to the adjacent room.

Room coordinates are written as `"x,y"` keys, while the player's
`"room_position"` is a two-number array `[x, y]`. The location view displays a
map centered on the player.

Let's add a message to one of the rooms. This message will play when the player enters the room. To make the message only play once, we can add the `"repeat"` and `"played"` members.

```json
    "0,0": {
        "message": {
            "text": [
                "Welcome to Castle Game, {player.name}! We hope you enjoy your stay.",
                "Explore the castle and see what you find!"
            ],
            "repeat": false,
            "played": false
        }
    }
```

`"repeat": false` means that the message cannot repeat. The engine sets
`"played"` to `true` after displaying it. Set `"played": false` when starting
a new game.

## 4. Add Collectable Items

Rooms can contain items using an `"items"` array. Each item refers to an entity
in the root-level `"entities"` object. Set the entity's `"collectable"` member
to `true` to let the player pick it up from the room's item menu.

```json
{
    "regions": {
        "fountain": {
            "rooms": {
                "1,0": {
                    "items": ["door_key"]
                }
            }
        }
    },
    "entities": {
        "door_key": {
            "name": "Door Key",
            "collectable": true
        }
    }
}
```

Items without `"collectable": true` remain in the room and cannot be picked
up. Collected items are removed from the room and added to the player's
`"inventory"`. An entity may also have a `"description"` member, shown when
the player selects it in their inventory. If no description is available, the
item screen shows a generic message; an entity's `"name"` is used when present,
otherwise the item key is shown. Players can drop one item at a time unless
the entity has `"droppable": false` or the current room has
`"contain_items": false`. Both members default to `true` when omitted.

An entity can define `"interactions"` for actions available while it is in a
room. Each interaction has a display `"name"` and a `"message"` shown when
selected. The interaction key is used as the name if `"name"` is omitted.
Interactions do not pick up or remove the entity. For example:

```json
"harbor_bell": {
    "name": "Harbor Bell",
    "item": false,
    "interactions": {
        "inspect": {
            "name": "Inspect",
            "message": "The bell is old and weathered."
        },
        "ring": {
            "name": "Ring",
            "message": "The bell rings loudly."
        }
    }
}
```

An entity with `"item": false` cannot be picked up, even if it is also marked
`"collectable": true`. Entities with interactions are presented as interactable
in the room-item menu. If an interactable entity is also collectable, its
interaction menu includes a separate **Pick up** choice.

## 5. Connect Rooms

Rooms can define `"connections"` to create exits in a direction that lead
outside the adjacent room grid or to another region. Each connection is keyed
by a direction (`"up"`, `"down"`, `"left"`, or `"right"`). Its optional
`"region"` and `"room_position"` members specify the destination; omitted
members default to the current region and the adjacent room in that direction.
Connections can also include `"conditions"`, `"success"`, `"failure"`, and
`"events"` members. A cross-region exit appears in the movement menu with its
destination region's name (or its key when no name is set). The destination
room must exist for the exit to be offered.

```json
"3,-1": {
    "connections": {
        "up": {
            "region": "courtyard",
            "room_position": [0, 0],
            "conditions": [
                {
                    "type": "has_item",
                    "item": "iron_key"
                }
            ],
            "success": {
                "message": "The gate opens."
            },
            "failure": {
                "message": "The gate is locked."
            },
            "events": {
                "type": "remove_item",
                "item": "iron_key"
            }
        }
    }
}
```

When a player tries to use this exit, every listed `has_item` condition must
pass. The failure message is shown if a required item is missing; otherwise,
the success message is shown and the event removes the key from the player's
inventory. Events can be one object or a list of objects. The currently
supported event is `"remove_item"`, which removes the specified item.

`"success"` can be used without conditions. Set `"repeat_condition": false`
and start `"condition_executed"` as `false` to run the connection's checks,
messages, and events only the first time the checks succeed. The engine saves
`"condition_executed": true` after that successful use.

## 6. End a Game

Set `"ending": true` on a room to complete the game when the player enters it.
The engine sets the root-level `"completed"` member to `true`, automatically
adds collectable items in that room to the player's inventory, saves the game,
and exits play. Set `"completed": false` when creating a fresh save.

## 7. Use Values in Dialogue

Use `{path.to.value}` placeholders to insert values from the game JSON. Each
dot-separated part looks up a member, starting at the root. For example,
`{player.name}` displays the player's name. If a placeholder cannot be
resolved, it is left unchanged, which can help spot a typo while testing.

As shown in Step 3, room messages are stored under `"message"` and their
content is in `"text"`. Text can be one string or a list of strings. For a
list, the **Concatenate dialogue** setting displays all lines together as one
multi-line passage and waits once; when disabled, each line displays
separately and waits after each one. A string message is always one passage.

## 8. Configure and Play

Choose **Options** from the main menu to toggle these settings. Settings are
saved in `config.json` in the current working directory:

- **Clear terminal** clears the screen between menus and passages.
- **Text formatting** enables or removes terminal colors and styling.
- **Concatenate dialogue** controls how list-based dialogue is displayed; see
  [Use Values in Dialogue](#7-use-values-in-dialogue).
- **Wrap text** wraps displayed lines to the terminal width.

To play a specific file without first opening the main menu, run
`python src/main.py --file path/to/your_game.json`. Loading a template prompts
for an active-save path; loading an active file will use and update that file
directly. The engine also remembers the last loaded save for **Load Last Save**.