# Formatting maps in the `/maps/` folder

Maps should be TXT files.

On the first line, the map size should be given, in the format `X Y`.

After a double newline, the map data should be given, exactly how it appears.

After another double newline, NPC locations should be listed. These will go 

`X Y NpcIdentifier`.

After that, the locations of loading zones and their destinations should be listed. These will be formatted as so:

`X1 Y1 NextMapName X2 Y2`, where X1/Y1 are the coords of the loading zone and X2/Y2 are the coords of the destination on the map `NextMapName`.

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

4 4 npc1

2 0 loadingzone1
2 19 loadingzone2
```