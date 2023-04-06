import pygame as pg
import dialog.dialog as dialog
import stats.equipment as equip
import stats.stats as stats
import stats.playerStats as pStats
import audio.audio as audio
import mapScreen.mapScreen as mapScreen
import battle.battle as battle
import menu.menu as menu


class SaveData:
    def __init__(self, mapName, posx, posy, playerData):
        self.mapName = mapName
        self.posx = posx
        self.posy = posy
        self.playerData = playerData
    def startWorld(self, world):
        """
        VERY IMPORTANT
        
        Sets up the game world according to own statistics.
        """

                
        inputs = world.create_entity(mapScreen.Input({
            "up":[pg.K_UP, pg.K_w],
            "down":[pg.K_DOWN, pg.K_s],
            "left":[pg.K_LEFT, pg.K_a],
            "right":[pg.K_RIGHT, pg.K_d],
            "confirm":[pg.K_z, pg.K_RETURN],
            "cancel":[pg.K_x, pg.K_LSHIFT, pg.K_RSHIFT],
            "menu":[pg.K_c,pg.K_ESCAPE],
            "z":[pg.K_z],
            "x":[pg.K_x],
            "c":[pg.K_c]
        }))

                
        consts = world.create_entity(mapScreen.Consts(
            32,            #TILE SIZE
            (640,480)      #SCREEN SIZE
        ))
        
        audioDict = world.create_entity(audio.AudioDict("audio/audioFiles.txt"))
        
        
        #CURRENTLY DUMMY VALUES
        camera = world.create_entity(mapScreen.Camera(0,0))
        
        #Testing tile data reading
        with open("mapScreen/tiles.txt") as tileRaw:
            tileMapping = mapScreen.readTileData(tileRaw.read(), world.component_for_entity(consts, mapScreen.Consts))
        world.create_entity(mapScreen.TileArrayComponent(tileMapping))

        with open("stats/classStats.txt") as classData:
            classDict = stats.readClassStats(classData.read())
            world.create_entity(classDict)
        
        #Configure Options
        world.create_entity(dialog.Options(world.component_for_entity(consts,mapScreen.Consts).screen, 1))
        
        #Read Dialog File
        with open("dialog/dialog.txt") as dialogData:
            dialogDict = dialog.readDialogFile(dialogData.read())
        
        #Read NPC File
        with open("dialog/npcs.txt") as npcData:
            npcDict = dialog.readNPCFile(npcData.read(), dialogDict)
        world.create_entity(mapScreen.NPCHolder(npcDict))

                
        with open(f"mapScreen/maps/{self.mapName}.txt") as mapRaw:
            # You can try changing testMap.txt to see the effect on the result!
            mapDict = mapScreen.MapHolder({self.mapName:mapScreen.readMapData(self.mapName, mapRaw.read(), tileMapping, npcDict)})
            world.create_entity(mapDict)
        
        testMap = world.create_entity(mapDict[self.mapName])
        world.component_for_entity(testMap,mapScreen.TileMap).Activate(world)
                
        playerData = world.create_entity(self.playerData)

                
        with open("battle/battles.txt") as battleData:
            battleDict = world.create_entity(battle.readBattleData(battleData.read(), battle.enemies))

                
        # Player on map
        player = world.create_entity(mapScreen.Position(32*self.posx,32*self.posy), 
                                     mapScreen.SpriteRenderer(pg.image.load("assets/art/maps/sprites/player.png").convert_alpha()),
                                    mapScreen.PlayerMove(8, world))
        
        # Processors
        world.add_processor(mapScreen.InputProcessor(), priority=15)
        world.add_processor(mapScreen.PlayerProcessor(), priority=10)
        world.add_processor(mapScreen.GraphicsProcessor(), priority=5)
        world.add_processor(battle.BattleProcessor(), priority=2)
        world.add_processor(menu.MenuProcessor(), priority=1)
        world.add_processor(dialog.DialogProcessor(), priority=0)
        
        


    
    def newGame(world):
        """
        Calls startWorld with the starting conditions of a new game.
        """
        with open("stats/classStats.txt") as classData:
            classDict = stats.readClassStats(classData.read())
            world.create_entity(classDict)
        mainChar = pStats.Character("Lux", "None", pStats.PlayerEquip(), pStats.PlayerBaseStats(0, classDict["none"], {"maxHP":0, "physAtk":0, "physDef":0, "magiAtk":0, "magiDef":0}),[])

        return SaveData("openingArea", 2, 2, dialog.PlayerData([], dict(), [], [mainChar], battle.SharedStats(4, 12, 0, 0), "none")).startWorld(world)

    def fromWorld(world):
        """
        Creates a SaveData object from the game world.
        """
        return SaveData()