# Micro Quest

Micro Quest is a text-based adventure game engine. Games are written as JSON
files that describe the story, player, regions, rooms, items, and exits.

**Inspired by:** [QuestForge](https://github.com/Code2College-Content/elite-101-mw-b)

## Run the engine

Use Python 3.10 or newer. From the repository directory, start the main menu:

```shell
python src/main.py
```

To load a game directly:

```shell
python src/main.py --file path/to/game.json
```

To resume the last saved game without opening the menu:

```shell
python src/main.py --last
```

## Run tests

The test suite uses Python's standard library and requires no additional
packages:

```shell
python -m unittest discover -v
```

Template games create a separate active save when loaded. Active game files are
updated in place, so make a copy before testing if you want to preserve the
original.

## Features

Micro Quest supports the following gameplay and authoring features:

- JSON game files with a title, description, player state, regions, rooms, and
  root-level entities.
- Room and exit definitions, including directional connections, custom map
  markers, and destination regions.
- Conditions and events for movement checks, item removal, attribute updates,
  player input prompts, and one-time connection triggers.
- Collectable items, inventory management, drops, and room-item interactions.
- NPC conversations and branching dialogue trees with conditional choices.
- On-start prompts, room messages, endings, and room completion status.
- Template saves that copy into a new active file and remember the last loaded
  save for quick resume.
- A settings menu for clearing the terminal, toggling text formatting, dialogue
  concatenation, and wrapping long lines.

## Create a game

Follow the step-by-step [game-file quickstart and guide](docs/creating-a-game-file.md#quickstart)
to build a JSON game, add rooms and items, and prepare a shareable template.