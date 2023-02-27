# Formatting maps in the `/maps/` folder

Maps should be TXT files.

On the first line, the map size should be given, in the format `X Y`.

After a double newline, the map data should be given, exactly how it appears.

After another double newline, NPC locations should be listed. These will go 

`X|Y|NpcIdentifier|NPCSpriteFileName`.
(NPCSpriteFileName should not be an absolute path: for example, use `npc.png` instead of `assets/art/sprites/npc.png`)

After that, the locations of cutscene triggers should be listed. These will go
`X|Y|Cutscene`.

After that, the locations of loading zones and their destinations should be listed. These will be formatted as so:

`X1|Y1|NextMapName|X2|Y2`, where X1/Y1 are the coords of the loading zone and X2/Y2 are the coords of the destination on the map `NextMapName`.

All locations and measurements are tile-based, starting at the top left corner (0, 0).

Example map (simple hallway, placeholder NPC/loading zones):

```py
8 20

WWFWWWWW
WFFFFFFW
WFFFFFFW
WFFFFFFW
WFFFFFFW
WFFFFFFW
WFFFFFFW
WFFFFFFW
WFFFFFFW
WFFFFFFW
WFFFFFFW
WFFFFFFW
WFFFFFFW
WFFFFFFW
WFFFFFFW
WFFFFFFW
WFFFFFFW
WFFFFFFW
WFFFFFFW
WWFWWWWW

2|2|Bobby|npc.png
4|6|Teacher|npc.png
5|10|Suspicious <Location>|moss.png

5|15|Example Cutscene

2|19|mainHall|9|1
2|0|smallRoomTest|4|6
```