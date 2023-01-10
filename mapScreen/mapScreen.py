#MAP SCREEN
#(c) 2022, CHCI PROGRAMMING CLUB



import pygame as pg
import esper
from typing import Tuple, List, Dict
import random
import dialog.dialog as dialog
clock = pg.time.Clock()

def clamp(n, nmin, nmax):
    """Clamp value to constraints"""
    if n<nmin:
        n = nmin
    if n>nmax:
        n = nmax
    return n

class Consts:
    """Constants used throughout this demo"""
    tileSize : int = 32
    screenSize : Tuple[int] = (640,480)
    def __init__(self, tile_size, screen_size):
        self.tileSize = tile_size
        self.screenSize = screen_size
        self.screen = pg.display.set_mode(self.screenSize)

class Camera:
    """Holds camera position and functions"""
    xpos : float = 0
    ypos : float = 0
    def __init__(self, xpos, ypos):
        self.xpos = xpos
        self.ypos = ypos

class Tile:
    """Data for a single tile type"""
    tileSprite : pg.Surface
    walkable : bool = False
    def __init__(self, sprite, walkable, consts):
        self.tileSprite = pg.transform.scale(sprite, (consts.tileSize, consts.tileSize))
        self.walkable = walkable

class Position:
    """Component related to positions"""
    posx : float = 0
    posy : float = 0
    predictedposx : float = 0
    predictedposy : float = 0
    moving = False
    def __init__(self, posx, posy):
        self.posx = posx
        self.posy = posy
        self.predictedposx = posx
        self.predictedposy = posy

class SpriteRenderer:
    """Provides functions to render a sprite given a position"""
    sprite : pg.Surface
    active : bool = True
    def __init__(self, sprite):
        self.sprite = pg.transform.scale(sprite, (32,32))
    def render(self, surf, posx, posy):
        """Render sprite at a given screen position and a surface"""
        rect = self.sprite.get_rect()
        rect.center = posx, posy
        surf.blit(self.sprite, rect)
    

class TileArray:
    """Holds tile data to be indexed by a TileMap, in Dict form"""
    tileData : Dict[str, Tile]
    def __init__(self, data):
        self.tileData = data

class TileMap:
    """2D Array of tiles, as string indexes to a TileArray"""
    mapSize : Tuple[int] = (24,24)
    mapData : List[List[str]] = []
    tileMapping : TileArray
    active : bool = False
    def __init__(self, size, data, mapping, npcs, loadingZones):
        self.mapSize = size
        self.mapData = data
        self.tileMapping = mapping
        self.active = False
        self.npcs = npcs

        #Currently not implemented, but read in by readMapData
        self.loadingZones = loadingZones
    def Activate(self, world):
        self.active = True
        for npc in self.npcs:
            world.create_entity(npc[0], npc[1], SpriteRenderer(pg.image.load(f"assets/art/sprites/{npc[2]}")))
    def Update(self, consts, camera):
        """Draw Tiles. Needs a reference to the game's constants and the camera."""
        for y in range(self.mapSize[1]):
            for x in range(self.mapSize[0]):
                try:
                    value = self.mapData[y][x]
                except IndexError:
                    raise IndexError("map size larger than provided data")
                try:
                    tile = self.tileMapping.tileData[value]
                except IndexError:
                    raise IndexError("tile data index out of bounds")
        
                rect = tile.tileSprite.get_rect()
                rect.center = x*consts.tileSize - camera.xpos, y*consts.tileSize - camera.ypos
                consts.screen.blit(tile.tileSprite, rect)

class Input:
    """Component that internally processes input. Is configurable"""
    buttonMaps : Dict[str, List[int]]
    buttons : Dict[str, bool]
    def __init__(self, maps):
        self.buttonMaps = maps
        self.buttons = dict()
    def pumpInput(self):
        """Internally gathers and processes input. Should be called once per frame."""
        pressed = pg.key.get_pressed()
        for key in self.buttonMaps.keys():
            self.buttons[key] = any([pressed[i] for i in self.buttonMaps[key]])
        #print(self.buttons)
        pg.event.pump()
class PlayerMove:
    """Component that controls the movement of an entity using inputs."""
    speed : float = 32
    def __init__(self, speed):
        self.speed = speed
    def Update(self, inputs, position, tileMap, npcs, world, playerData):
        """Move player based on inputs. 
        Needs a reference to the player's position, and the inputs."""
        buttons = inputs.buttons
        if not(all([btn in buttons for btn in ["up", "down", "left", "right"]])):
            raise RuntimeError("Buttons not fully assigned")
        if not(position.moving):
            try:
                if buttons["up"] and tileMap.tileMapping.tileData[tileMap.mapData[position.predictedposy//32 - 1][position.predictedposx//32]].walkable:
                    position.predictedposy -= 32
                    position.moving = True
                if buttons["down"] and tileMap.tileMapping.tileData[tileMap.mapData[position.predictedposy//32 + 1][position.predictedposx//32]].walkable:
                    position.predictedposy += 32
                    position.moving = True
                if buttons["left"] and tileMap.tileMapping.tileData[tileMap.mapData[position.predictedposy//32][position.predictedposx//32 - 1]].walkable:
                    position.predictedposx -= 32
                    position.moving = True
                if buttons["right"] and tileMap.tileMapping.tileData[tileMap.mapData[position.predictedposy//32][position.predictedposx//32 + 1]].walkable:
                    position.predictedposx += 32
                    position.moving = True
            except IndexError:
                print("OOB Prevented (or, something has gone horribly wrong)")
                """
                To whichever programmer is reading this:
                I know this looks lazy. I know it looks horrible.
                But bear with me. This is better than implementing many, many more checks,
                and if maps are planned right, you should never run into it anyways.
                It prevents a potentially bad crash in the most harmless of ways.
                It only applies to a very specific OOB (out-of bounds) glitch which is already
                covered AND FIXED below.
                In short, this is a necessary evil we must take if we are to continue using
                the heathen language known as Python. (no hate, but there was this one bug
                that took me hours to fix because I mixed up string True and bool True)

                P.S. At least it's the only possible source of IndexErrors in that snippet!
                The rest are KeyErrors that might be raised if a TileMap uses a tile not defined in its TileMapping,
                or KeyErrors if a button is not defined.
                Things would be a lot worse if this obscured actual errors.
                
                Sincerely, 
                Corin Gaiotto
                """

        
        # Aforementioned OOB prevention
        if position.predictedposx < 0:
            position.predictedposx = 0
        if position.predictedposy < 0:
            position.predictedposy = 0
        if position.predictedposx > tileMap.mapSize[0]*32:
            position.predictedposx = tileMap.mapSize[0]*32
        if position.predictedposy > tileMap.mapSize[1]*32:
            position.predictedposy = tileMap.mapSize[1]*32

        # NPC collision detection and interaction
        for npc in npcs:
            if position.predictedposx == npc[0].posx and position.predictedposy == npc[0].posy:
                # Revert planned movement, stopping the player.
                position.predictedposx = position.posx
                position.predictedposy = position.posy
                if buttons["confirm"]:
                    npc[1].interact(world, playerData)
    
        
        if position.posx < position.predictedposx:
            position.posx += self.speed
        if position.posx > position.predictedposx:
            position.posx -= self.speed
        if position.posy < position.predictedposy:
            position.posy += self.speed
        if position.posy > position.predictedposy:
            position.posy -= self.speed
        if position.posx == position.predictedposx and position.posy == position.predictedposy:
            position.moving = False
        #print(f"{tilePosition}")

def readTileData(dataStr, consts):
    """Read in a file containing tile data, as specified in tilesFormat.md.
    Requires a Consts object for tile size.
    Returns a TileArray."""
    tilesRaw = dataStr.split("\n\n")
    outTiles = TileArray(dict())
    for tileData in tilesRaw:
        lines = tileData.split("\n")
        outTiles.tileData[lines[0]] = Tile(pg.image.load(f"assets/art/tiles/{lines[1]}"), (lines[2] == "True"), consts)
    return outTiles

def readMapData(dataStr, tileMapping, npcDict):
    """Read in a file containing map data, as will be specified in mapsFormat.md.
    Requires tile mapping data, as a TileArray.
    Returns a TileMap."""
    size, mapData, npcData, loadingZoneData = dataStr.split("\n\n")

    sizeTuple = tuple(map(int, size.split(" ")))
    mapDataArray = []
    for y in range(sizeTuple[1]):
        mapDataArray.append([])
        for x in range(sizeTuple[0]):
            mapDataArray[y].append(mapData.split("\n")[y][x])
    npcs = []
    for npc in npcData.split("\n"):
        npcX, npcY = npc.split("|")[:2]
        npcBrain = npcDict[npc.split("|")[2]]
        sprite = npc.split("|")[3]
        npcs.append((Position(int(npcX)*32, int(npcY)*32), npcBrain, sprite))
    return TileMap(sizeTuple, mapDataArray, tileMapping, npcs, loadingZoneData)
    
    

class InputProcessor(esper.Processor):
    def process(self):
        """Pump inputs once per frame"""
        inputs = self.world.get_component(Input)[0][1]
        inputs.pumpInput()
class PlayerProcessor(esper.Processor):
    def process(self):
        """Move player and camera, with respect to the current active TileMap."""
        inputs = self.world.get_component(Input)[0][1]
        consts = self.world.get_component(Consts)[0][1]
        camera = self.world.get_component(Camera)[0][1]
        npcs = [npc[1] for npc in self.world.get_components(Position, dialog.NPCBrain)]
        playerData = self.world.get_component(dialog.PlayerData)[0][1]
        currentMap = None
        for tileMapEntity in self.world.get_component(TileMap):
            if tileMapEntity[1].active:
                currentMap = tileMapEntity[1]
                break
        if not(currentMap):
            return 0
        player, position = self.world.get_components(PlayerMove, Position)[0][1]
        player.Update(inputs, position, currentMap, npcs, self.world, playerData)
        if consts.screenSize[0] > currentMap.mapSize[0]*32:
            camera.xpos = currentMap.mapSize[0]*16-consts.screenSize[0]/2
        else:
            camera.xpos = clamp(position.posx, consts.screenSize[0]/2, currentMap.mapSize[0]*32-consts.screenSize[0]/2) - consts.screenSize[0]/2 - 16
        if consts.screenSize[1] > currentMap.mapSize[1]*32:
            camera.ypos = currentMap.mapSize[1]*16-consts.screenSize[1]/2
        else:
            camera.ypos = clamp(position.posy, consts.screenSize[1]/2, currentMap.mapSize[1]*32-consts.screenSize[1]/2) - consts.screenSize[1]/2 - 16
        
        
class GraphicsProcessor(esper.Processor):
    def process(self):
        """Draw graphics, layer by layer. Layers are separated by comments."""
        consts = self.world.get_component(Consts)[0][1]
        camera = self.world.get_component(Camera)[0][1]

        #LAYER 0: BLACK BACKGROUND
        consts.screen.fill((0,0,0))
        
        #LAYER 1: MAP DATA
        for entity, map in self.world.get_component(TileMap):
            if map.active:
                map.Update(consts, camera)

        #LAYER 2: SPRITES
        for entity, (sprite, pos) in self.world.get_components(SpriteRenderer, Position):
            if sprite.active:
                sprite.render(consts.screen, pos.posx-camera.xpos, pos.posy-camera.ypos)
