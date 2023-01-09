import pygame as pg
import esper
import dialog.dialog as dialog
import stats.equipment as equip
import stats.stats as stats
import stats.playerStats as pStats
import mapScreen.mapScreen as mapScreen
import random


#EVERYTHING BEYOND THIS POINT IS TEMPORARY AND FOR TESTING :))))

clock = pg.time.Clock()

with open("stats/equipment.txt") as equipData:
    equipDict, enchantDict = equip.loadEquipment(equipData.read())
with open("stats/classStats.txt") as classData:
    classDict = stats.readClassStats(classData.read())


bob = pStats.Character("Bob", pStats.PlayerEquip(), pStats.PlayerBaseStats(10, classDict["english"], {"maxHP":0, "physAtk":0, "physDef":0, "magiAtk":0, "magiDef":0}))
#print(equipDict)
bob.equip(equipDict["Simple Calculator"])
bob.equip(equipDict["Protector's Shield"])

#print(bob)

world = esper.World()


inputs = world.create_entity(mapScreen.Input({
    "up":[pg.K_UP],
    "down":[pg.K_DOWN],
    "left":[pg.K_LEFT],
    "right":[pg.K_RIGHT],
    "confirm":[pg.K_z, pg.K_RETURN],
    "cancel":[pg.K_x, pg.K_LSHIFT, pg.K_RSHIFT]
}))


consts = world.create_entity(mapScreen.Consts(
    32,            #TILE SIZE
    (640,480)      #SCREEN SIZE
))



#CURRENTLY DUMMY VALUES
camera = world.create_entity(mapScreen.Camera(0,0))

#Testing tile data reading
with open("mapScreen/tiles.txt") as tileRaw:
    tileMapping = mapScreen.readTileData(tileRaw.read(), world.component_for_entity(consts, mapScreen.Consts))

with open("mapScreen/maps/testMap.txt") as mapRaw:
    # You can try changing testMap.txt to see the effect on the result!
    mapData = mapScreen.readMapData(mapRaw.read(), tileMapping)

testMap = world.create_entity(mapData)



#Configure Options
world.create_entity(dialog.Options(world.component_for_entity(consts,mapScreen.Consts).screen, int(input("Enter text speed: (1-10)"))/4))

#Read Dialog File
with open("dialog/dialog.txt") as dialogData:
    dialogDict = dialog.readDialogFile(dialogData.read())

#Read NPC File
with open("dialog/npcs.txt") as npcData:
    npcDict = dialog.readNPCFile(npcData.read(), dialogDict)

playerData = world.create_entity(dialog.PlayerData([], dict({"FixHealingPlace":-1}), []))


player = world.create_entity(mapScreen.Position(32,32), 
                             mapScreen.SpriteRenderer(pg.image.load("assets/art/sprites/player.png")),
                            mapScreen.PlayerMove(4))

bobbyTheNpc = world.create_entity(mapScreen.Position(64,64),
                               mapScreen.SpriteRenderer(pg.image.load("assets/art/sprites/npc.png")),
                               npcDict["Bobby"])
teacherNPC = world.create_entity(mapScreen.Position(128,192),
                               mapScreen.SpriteRenderer(pg.image.load("assets/art/sprites/npc.png")),
                               npcDict["Teacher"])
locationNPC = world.create_entity(mapScreen.Position(160,320),
                               mapScreen.SpriteRenderer(pg.image.load("assets/art/sprites/placeholder.png")),
                               npcDict["Suspicious <Location>"])


world.add_processor(mapScreen.InputProcessor(), priority=10)
world.add_processor(mapScreen.PlayerProcessor(), priority=5)
world.add_processor(mapScreen.GraphicsProcessor(), priority=1)
world.add_processor(dialog.DialogProcessor(), priority=0)



while 1:
    world.process()
    pg.display.flip()
    clock.tick(30) #technically configurable: can run fine at 60, suffers from frame drops if you go higher
    #print(clock.get_fps()) #see console for performance