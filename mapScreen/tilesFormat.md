# Formatting `tiles.txt`

Tile entries are double newline separated.

Any given tile entry has three parts, separated by newlines:
1. Tile identifier. One character, is used for the map.
2. Texture File name. Do not include `assets/art/tiles/`, that is automatically included.
3. Boolean describing whether or not the tile is walkable.

Example entry:
```py
F
floor.png
True
```

Example file:
```py
F
floor.png
True

W
wall.png
False

L
locker.png
False
```