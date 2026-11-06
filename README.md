# Micro Quest

Micro Quest is a text-based adventure game engine. Games are written as JSON
files that describe the story, player, regions, rooms, items, and exits.

## Run the engine

Use Python 3.10 or newer. From the repository directory, start the main menu:

```shell
python src/main.py
```

To load a game directly:

```shell
python src/main.py --file path/to/game.json
```

Template games create a separate active save when loaded. Active game files are
updated in place, so make a copy before testing if you want to preserve the
original.

## Create a game

Follow the step-by-step [game-file quickstart and guide](docs/creating-a-game-file.md#quickstart)
to build a JSON game, add rooms and items, and prepare a shareable template.