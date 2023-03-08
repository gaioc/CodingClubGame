import pygame as pg
import esper
import dialog.dialog as dialog
import stats.equipment as equip
import stats.stats as stats
import stats.playerStats as pStats
import audio.audio as audio
import battle.battle as battle
import mapScreen.mapScreen as mapScreen
import random


pg.mixer.pre_init(44100, -16, 2, 512) #IMPORTANT: reduces stuttering
pg.mixer.init()


#EVERYTHING BEYOND THIS POINT IS TEMPORARY AND FOR TESTING :))))

clock = pg.time.Clock()

with open("stats/equipment.txt") as equipData:
    equipDict, enchantDict = equip.loadEquipment(equipData.read())
with open("stats/classStats.txt") as classData:
    classDict = stats.readClassStats(classData.read())


lux = pStats.Character("Lux", "English", pStats.PlayerEquip(), pStats.PlayerBaseStats(4, classDict["english"], {"maxHP":0, "physAtk":0, "physDef":0, "magiAtk":0, "magiDef":0}),["Math Skill L13", "Math Skill L16", "Revive", "Math Skill L10"])
lux.equip(equipDict["Notebook"].enchant(enchantDict["Augmented"]))
lux.equip(equipDict["Formal Wear"].enchant(enchantDict["Augmented"]))
lux.equip(equipDict["Six-foot Pencil"].enchant(enchantDict["Sharp"]))
lux.hp = lux.totalStats["maxHP"]

bob = pStats.Character("Bob", "Science", pStats.PlayerEquip(), pStats.PlayerBaseStats(4, classDict["science"], {"maxHP":0, "physAtk":0, "physDef":0, "magiAtk":0, "magiDef":0}),["Math Skill L1", "Science Skill L4", "Science Skill L1", "Revive"])
bob.equip(equipDict["Test Tube"].enchant(enchantDict["Augmented"]))
bob.equip(equipDict["Lab Coat"].enchant(enchantDict["Warded"]))
bob.equip(equipDict["Prism"].enchant(enchantDict["Arcane"]))
bob.hp = bob.totalStats["maxHP"]

test = pStats.Character("Test", "Art", pStats.PlayerEquip(), pStats.PlayerBaseStats(4, classDict["art"], {"maxHP":0, "physAtk":0, "physDef":0, "magiAtk":0, "magiDef":0}),["Math Skill L4", "Math Skill L7", "Math Skill L19", "Revive"])
test.equip(equipDict["Simple Calculator"].enchant(enchantDict["Warded"]))
test.equip(equipDict["Protector's Armour"].enchant(enchantDict["Heavy"]))
test.equip(equipDict["Circle Shield"].enchant(enchantDict["Heavy"]))
test.hp = test.totalStats["maxHP"]

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
#world.component_for_entity(testMap,mapScreen.TileMap).Activate(world)




playerData = world.create_entity(dialog.PlayerData([], dict({"FixHealingPlace":-1}), [], [lux, bob, test], battle.SharedStats(40, 50, 0)))


testBattle = world.create_entity(battle.BattleHandler([battle.BattleEntity(None, None, None, None).fromCharacter(i) for i in world.component_for_entity(playerData, dialog.PlayerData).characters], [battle.BattleEnemy("Skeleton A", {"maxHP":100000,"physAtk":300,"physDef":30,"magiAtk":30,"magiDef":30}, 100000, [battle.enemyAttacks["enemyAttack"],battle.enemyAttacks["boneSpray"]], pg.image.load("assets/art/battle/enemies/skeleton.png"),battle.EnemyAI())], world.component_for_entity(playerData, dialog.PlayerData).sharedStats, pg.image.load("assets/art/battle/backgrounds/background1.png")))
world.component_for_entity(testBattle, battle.BattleHandler).Activate()


player = world.create_entity(mapScreen.Position(32,32), 
                             mapScreen.SpriteRenderer(pg.image.load("assets/art/maps/sprites/player.png")),
                            mapScreen.PlayerMove(8))


world.add_processor(mapScreen.InputProcessor(), priority=15)
world.add_processor(mapScreen.PlayerProcessor(), priority=10)
world.add_processor(mapScreen.GraphicsProcessor(), priority=5)
world.add_processor(battle.BattleProcessor(), priority=1)
world.add_processor(dialog.DialogProcessor(), priority=0)



while 1:
    world.process()
    pg.display.flip()
    clock.tick(30) #technically configurable: can run fine at 60, suffers from frame drops if you go higher
    #print(clock.get_fps()) #see console for performance