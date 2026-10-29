# How to Create a Game File
Micro Quest stores each quest as its own JSON file containing the entire game story, player choices, rooms, and outcomes. This guide explains how to create a game file that can be loaded by the Micro Quest engine.
## Game File Structure
Every game file must contain certain required members. Other members may be optional, depending on the features used by the game.
### Required Members
- `"title"` — The title of the game, displayed when game is opened.
- `"description"` — A brief game description, displayed below the title.
- `"status"` — The current status of the game, either `"template"` or `"active"`.
- `"player"` — Game entity member containing player information.
- `"regions"` — Member containing world regions and the rooms nested within them.
### Optional Members
- `"characters"` — Contains relevant information for game NPCs.
- `"items"` — Contains relevant information for game items.
- `"challenges"` — Contains information for game challenges. These are used to require certain conditions or inputs before performing an action.
- `"attributes"` — Custom values that can be held by any game entity. Used to add custom behavior or store miscellaneous information for later. Can be used to store game-specific settings.
- `"events"` — Events that trigger based on game state. Can be used to modify custom attributes or base attributes like player position.