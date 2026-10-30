# Player

The root-level player member is where all player-specific data is stored in the game file.

**Key** `"player"`  
**Value Type**: `dict`  
**Required**: Yes

## Members

### Name

The name of the player as a string. May be omitted if not referenced in the game file.

**Key**: `"name"`  
**Value Type**: `"str"`  
**Required**: No

### Region

The current region the player is in. Value of string should match the key of the region member, not the name.

**Key**: `"region"`  
**Value Type**: `str`  
**Required**: Yes

### Room Position

The room position of the player within its region. Represented as a string with the format `"x,y"`, where `x` and `y` are the cartesian coordinates of the player in the region's room grid.

**Key**: `"room_position"`  
**Value Type**: `str`  
**Value Formatting**: `"x,y"`  
**Required**: Yes

### Inventory

An optional dictionary member containing the currently held items by the player. Each item should be represented as a key matching that item's key in the `entities` member, and an integer value representing the amount of that item held in your inventory. This dictionary may be empty.

**Key**: `"inventory"`  
**Value Type**: `dict`  
**Member Formatting**: `"entity_key": num`  
**Required**: No

### Attributes

An optional dictionary member containing a list of attributes held by the player. Player-level attributes remain distinct from the world-level `attributes` member.

**Key**: `"attributes"`  
**Value Type**: `dict`  
**Required**: No