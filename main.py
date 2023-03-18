import pygame as pg
import esper
import dialog.dialog as dialog
import stats.equipment as equip
import stats.stats as stats
import stats.playerStats as pStats
import audio.audio as audio
import mapScreen.mapScreen as mapScreen
import battle.battle as battle
import menu.menu as menu
import random


pg.mixer.pre_init(44100, -16, 2, 512) #IMPORTANT: reduces stuttering
pg.mixer.init()


#EVERYTHING BEYOND THIS POINT IS TEMPORARY AND FOR TESTING :))))

clock = pg.time.Clock()

with open("stats/equipment.txt") as equipData:
    equipDict, enchantDict = equip.loadEquipment(equipData.read())
with open("stats/classStats.txt") as classData:
    classDict = stats.readClassStats(classData.read())

lux = pStats.Character("Lux", "None", pStats.PlayerEquip(), pStats.PlayerBaseStats(10, classDict["none"], {"maxHP":0, "physAtk":0, "physDef":0, "magiAtk":0, "magiDef":0}),[])
lux2 = pStats.Character("Lux 2", "Psychology", pStats.PlayerEquip(), pStats.PlayerBaseStats(10, classDict["psychology"], {"maxHP":0, "physAtk":0, "physDef":0, "magiAtk":0, "magiDef":0}),[])
lux3 = pStats.Character("Lux 3", "Math", pStats.PlayerEquip(), pStats.PlayerBaseStats(10, classDict["math"], {"maxHP":0, "physAtk":0, "physDef":0, "magiAtk":0, "magiDef":0}),[])


world = esper.World()


inputs = world.create_entity(mapScreen.Input({
    "up":[pg.K_UP, pg.K_w],
    "down":[pg.K_DOWN, pg.K_s],
    "left":[pg.K_LEFT, pg.K_a],
    "right":[pg.K_RIGHT, pg.K_d],
    "confirm":[pg.K_z, pg.K_RETURN],
    "cancel":[pg.K_x, pg.K_LSHIFT, pg.K_RSHIFT],
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

#Configure Options
world.create_entity(dialog.Options(world.component_for_entity(consts,mapScreen.Consts).screen, 1))

#Read Dialog File
with open("dialog/dialog.txt") as dialogData:
    dialogDict = dialog.readDialogFile(dialogData.read())

#Read NPC File
with open("dialog/npcs.txt") as npcData:
    npcDict = dialog.readNPCFile(npcData.read(), dialogDict)
world.create_entity(mapScreen.NPCHolder(npcDict))

with open("mapScreen/maps/openingArea.txt") as mapRaw:
    # You can try changing testMap.txt to see the effect on the result!
    mapDict = mapScreen.MapHolder({"openingArea":mapScreen.readMapData(mapRaw.read(), tileMapping, npcDict)})
    world.create_entity(mapDict)

testMap = world.create_entity(mapDict["openingArea"])
######world.component_for_entity(testMap,mapScreen.TileMap).Activate(world)



playerData = world.create_entity(dialog.PlayerData([], dict({"FixHealingPlace":-1}), [], [lux,lux2,lux3], battle.SharedStats(40, 50, 0, 0)))

with open("battle/battles.txt") as battleData:
    battleDict = world.create_entity(battle.readBattleData(battleData.read(), battle.enemies))

# Player on map
player = world.create_entity(mapScreen.Position(32,32), 
                             mapScreen.SpriteRenderer(pg.image.load("assets/art/maps/sprites/player.png").convert_alpha()),
                            mapScreen.PlayerMove(8))

testMenu = menu.Menu(
    {
        "Background Layer 0":menu.BackgroundMenu(True),
        "Portrait 0":menu.PortraitMenu(2,2,True,0),
        "Portrait 1":menu.PortraitMenu(2,144,True,1),
        "Portrait 2":menu.PortraitMenu(2,286,True,2),
        "SharedStatsViewer":menu.SharedStatsMenu(2,426,True),
        "OptionsSidebar":menu.OptionsMenu(452,2,188,474,["View Stats", "Equipment", "Inventory", "Change Spells", "Change Order"], True)
    }
)

# Processors
world.add_processor(mapScreen.InputProcessor(), priority=15)
world.add_processor(mapScreen.PlayerProcessor(), priority=10)
world.add_processor(mapScreen.GraphicsProcessor(), priority=5)
world.add_processor(battle.BattleProcessor(), priority=1)
world.add_processor(dialog.DialogProcessor(), priority=0)


i = 0
while 1:
    world.process()
    testMenu.Update(world.component_for_entity(consts, mapScreen.Consts).screen, world, world.component_for_entity(inputs, mapScreen.Input))
    pg.display.flip()
    clock.tick(30)
    if i > int(clock.get_fps()):
        print(clock.get_fps()) #see console for performance
        i = 0
    i += 1