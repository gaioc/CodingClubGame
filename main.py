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
print(equipDict)
bob.equip(equipDict["Simple Calculator"])
bob.equip(equipDict["Protector's Shield"])

print(bob)

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

testMap = world.create_entity(mapScreen.TileMap(
    (50, 50), #50 by 50 should be much larger than we would ever need in a (relatively) indoor setting
    [
        [(1 if random.randint(0,5) == 5 else 0) for x in range(50)] 
        for y in range(50)
    ],
    [
        mapScreen.Tile(pg.image.load("assets/art/tiles/grass.png"), False, world.component_for_entity(consts, mapScreen.Consts)),
        mapScreen.Tile(pg.image.load("assets/art/tiles/shallow.png"), False, world.component_for_entity(consts, mapScreen.Consts))
    ]
))

player = world.create_entity(mapScreen.Position(0,0), 
                             mapScreen.SpriteRenderer(pg.image.load("assets/art/sprites/player.png")),
                            mapScreen.PlayerMove(1))

bobTheNpc = world.create_entity(mapScreen.Position(64,64),
                               mapScreen.SpriteRenderer(pg.image.load("assets/art/sprites/npc.png")))

#Configure Options
world.create_entity(dialog.Options(world.component_for_entity(consts,mapScreen.Consts).screen, int(input("Enter text speed: (1-10)"))/4))

#Read Dialog File
with open("dialog/dialog.txt") as dialogData:
    dialogDict = dialog.readDialogFile(dialogData.read())

playerData = dialog.PlayerData(["<Item>"], dict({"FixHealingPlace":1}), ["Bobby"])


testNPC = dialog.NPCBrain(
    "Bobby",
    [
        dialog.BrainInstance(dialog.FirstInteractionCondition(), dialogDict["Fix Healing Place - First"]),
        dialog.BrainInstance(dialog.QuestStatusCondition("FixHealingPlace", -1), dialogDict["Fix Healing Place"]),
        dialog.BrainInstance(dialog.MultipleAllConditions([dialog.QuestStatusCondition("FixHealingPlace", 0), dialog.InventoryCondition("<Item>")]), dialogDict["Fix Healing Place - Conditions met"]),
        dialog.BrainInstance(dialog.QuestStatusCondition("FixHealingPlace", 0), dialogDict["Fix Healing Place - Reminder"]),
        dialog.BrainInstance(dialog.QuestStatusCondition("FixHealingPlace", 1), dialogDict["Healing Place Interaction"])
    ]
)




world.add_processor(mapScreen.InputProcessor(), priority=10)
world.add_processor(mapScreen.PlayerProcessor(), priority=5)
world.add_processor(mapScreen.GraphicsProcessor(), priority=1)
world.add_processor(dialog.DialogProcessor(), priority=0)


for x in range(300):
    world.process()
    pg.display.flip()
    clock.tick(30) #technically configurable: can run fine at 60, suffers from frame drops if you go higher
    print(clock.get_fps()) #see console for performance
testNPC.interact(world, playerData)
while 1:
    world.process()
    pg.display.flip()
    clock.tick(30) #technically configurable: can run fine at 60, suffers from frame drops if you go higher
    print(clock.get_fps()) #see console for performance