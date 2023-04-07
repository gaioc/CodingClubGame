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
import save.save as save
import random


pg.mixer.pre_init(44100, -16, 2, 512) #IMPORTANT: reduces stuttering
pg.mixer.init()


#EVERYTHING BEYOND THIS POINT IS TEMPORARY AND FOR TESTING :))))

clock = pg.time.Clock()

world = esper.World()
s = save.SaveData.LoginSetup(world)
screen = pg.display.set_mode((640,480))

i = 0
while 1:
    world.process()
    pg.display.flip()
    clock.tick(30)
    if i > int(clock.get_fps()):
        print(clock.get_fps()) #see console for performance
        i = 0
    i += 1