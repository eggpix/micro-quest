# Creating a Game File

Micro Quest stores each quest in its own JSON file, containing the entire game, including its story, player choices, rooms, and outcomes. This guide explains how to structure a game file so it can be loaded by the Micro Quest engine.

## Contents

- [Base File Structure](#base-file-structure)
  - [Required Members](#required-members)
  - [Optional Members](#optional-members)
- [Members](#members)
  - [Title](#title)
  - [Description](#description)
  - [Status](#status)

## Base File Structure

Every game file must contain certain required root-level members. Additional members are optional and can be included as needed to support the game's features. Note that dictionary-type values contain their own optional and required members.

### Required Members

- `"title"` — The title of the game, displayed when the game is opened.
- `"description"` — A brief description of the game, displayed below its title.
- `"status"` — The current status of the game. Valid values are `"template"` and `"active"`.
- `"player"` — Contains information about the player.
- `"regions"` — Contains the world's regions and their nested rooms.

### Optional Members

- `"metadata"` — Additional information about the game, such as its author or copyright date.
- `"entities"` — Contains game objects with custom properties and behavior. Entities can represent NPCs, items, and other interactive objects.
- `"definitions"` — Contains reusable configurations that can be applied to multiple entities or rooms.
- `"attributes"` — Contains world-level custom variables that can be accessed by any entity.
- `"conditions"` — Defines reusable conditions that can be evaluated by entities, rooms, events, actions, and other game components to determine whether certain behavior should occur.
- `"actions"` — Defines reusable operations that can be executed by events or other game components.
- `"events"` — Defines events that execute actions when specific game states are reached or when explicitly invoked by an entity or another game component.



