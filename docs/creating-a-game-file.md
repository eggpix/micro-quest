# Creating a Game File

Micro Quest is a minimal but flexible text-based adventure game engine. Every game in Micro Quest is stored as a single JSON file containing all rooms, characters, player information, and more. This guide gives game creators a starting point and reference for making game templates that can be distributed and played.

## Before You Start

It is recommended that you follow this guide step-by-step before diving into the reference. The following sections cover a few important details about game files. Please read them carefully.

### Terminology

Before creating a game, it's important to know some basic terminology. Below are a few basic important terms that will be used throughout this guide.

- **JSON** — The file format used by Micro Quest to store game information. Information about JSON files and how to format them can be found in the [official json.org website](https://www.json.org/json-en.html).
- **Object** — A collection of key/value pairs. Functions similarly to a Python dictionary, with each key associated with a value.
- **Member** — A key/value pair within a JSON object. The key identifies the member, while the value contains its associated data.

### Game Status

A Micro Quest game can be labeled as either "template" or "active". Template games are the files distributed to players. These files must be copied or converted to active files first before playing. This prevents players from accidentally overwriting template data, allowing them to restart from an empty save. An active file can be played normally and functions like an existing save file. Status information is stored as a string in the `"status"` member of every JSON file, and is required for the game to run. Game creators should set this member to `"template"` before distribution.

### Required JSON Members

Every game file must contain certain required root-level members. Additional members are optional and can be included as needed to support the game's features. Note that dictionary-type values contain their own optional and required members. Listed below is the comprehensive list of strictly required JSON members for the game to run.

- `"title"` — The title of the game, displayed when the game is opened.
- `"description"` — A brief description of the game, displayed below its title.
- `"status"` — The current status of the game. Valid values are `"template"` and `"active"`.
- `"player"` — Contains information about the player.
- `"regions"` — Contains the world's regions and their nested rooms.

Detailed information about each member can be found in the game file member reference.

### Naming Conventions

For consistency, it is recommended to name your keys using *snake case*, where words are lowercase and separated by underscores. When possible, give all keys a unique value to avoid confusion. Using a key twice within the same object may result in unpredictable behavior and should always be avoided.

**Example:** `"door_key_0"`


## 1. Create a Minimal Game
The smallest valid JSON file that can be loaded by the Micro Quest engine consists of a single room and an unnamed player occupying that room. It looks like this:

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

As you can see, this game file contains only the required members outlined above. Copying this code into a .json file creates a valid game that can be loaded by the Micro Quest engine. However, the player cannot interact with the game yet.

## 2. Customize the Player

Let's try adding some extra information to the player object. We can start by adding a `"name"` member which holds a string.

```json
"player": {
    "name": "Jane",
    "region": "fountain",
    "room_position": [0,0]
},
```

By default, this member won't affect any game behavior, however this name can be accessed and placed in dialogue using curly braces:

```json
"message": "Hello, {player.name}!"
```

More information on accessing variables within dialogue can be found in `...`.

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