## Status

Status stores whether the game is an active game file or a template. If the game is a template, a new copy of the game file must be created before playing (this avoids overwriting game data in case the player wants to restart a game). The new file will have active status. If you are creating a game for other players to play, set this value to `"template"` before distribution.

**Key**: `"status"`  
**Value Type**: `str`  
**Valid Entries**: `"template"` or `"active"`  
**Required**: Yes