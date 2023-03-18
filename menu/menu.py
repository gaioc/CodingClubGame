import pygame as pg
from textwrap import wrap
import dialog.dialog as dialog

def printScr(text: str, posx: float, posy: float, colour: pg.Color, font: pg.font.Font, screen: pg.Surface):
    """
    Render text at (posx,posy) of screen, using font in provided colour.
    """
    render = font.render(text, True, colour)
    rect = render.get_rect()
    rect.center = posx, posy
    rect.left = posx
    screen.blit(render, rect)

def drawPortrait(posx, posy, screen):
    """
    Draw the given character portrait centered at *posx*,*posy*. Currently draws a 128x128 white square for testing purposes.
    """
    pg.draw.rect(screen, (255,255,255), pg.Rect(posx-64,posy-64,128,128))

def printWrapped(text: str, width: int, lineSpacing: int, posx: float, posy: float, colour: pg.Color, font: pg.font.Font, screen: pg.Surface):
    """
    Render text wrapped at width at (posx,posy) of screen, using font in provided colour.
    """
    wrapped = wrap(text, width=width)
        
    for i in range(0, len(wrapped)):
        printScr("".join(wrapped[i]), posx, posy+lineSpacing*i, (255,255,255), font, screen)

def drawMenuBox(screen, left, top, length, height):
    pg.draw.rect(screen, (0,0,160), pg.Rect(left, top, length, height))
    pg.draw.rect(screen, (255,255,255), pg.Rect(left, top, length, height),4)

def drawHorizontalBar(screen, left, top, length, height, color, value, max):
    pg.draw.rect(screen, (0,0,0), pg.Rect(left, top, length, height))
    pg.draw.rect(screen, color, pg.Rect(left, top, length*value/max, height))

def drawVerticalBar(screen, left, top, length, height, color, value, max):
    pg.draw.rect(screen, (0,0,0), pg.Rect(left, top, length, height))
    pg.draw.rect(screen, color, pg.Rect(left, top, length, height*value/max))

class Menu:
    def __init__(self, items):
        """
        General-purpose class that holds a dict of MenuItems
        """
        self.items = items
    def Update(self, screen, world, inputs):
        for item in self.items.values():
            if item.visible:
                item.draw(screen, world)
        
        
class MenuOptionsHandler:
    """
    Holds a list of selectable options, and handles input to it including confirm/cancel.
    """
    def __init__(self, optionCount, posx, posy, shiftx, shifty, mode="vertical"):
        self.selected = 0
        self.optionCount = optionCount
        self.posx = posx
        self.posy = posy
        self.shiftx = shiftx
        self.shifty = shifty
        self.mode = mode
        self.active = False
    def Activate(self):
        self.active = True
        self.oldInputs = {
            "confirm":True,
            "cancel":True,
            "left":True,
            "right":True,
            "up":True,
            "down":True
        }
    def draw(self, screen):
        """
        Draws a pointer at the location of the current option.
        """
        

class MenuItem:
    def __init__(self, posx, posy, visible):
        self.posx = posx
        self.posy = posy
        self.visible = visible
    def draw(self, screen, world):
        pass
    def Update(self, screen, world, inputs):
        pass

class PortraitMenu:
    def __init__(self, posx, posy, visible, index):
        self.posx = posx
        self.posy = posy
        self.visible = visible
        self.font = pg.font.SysFont("Courier", 16)
        # Character party index this menu is tied to
        self.index = index
    def draw(self, screen, world):
        
        xpPerLevelUp = [
                   1,
                   5,
                  10,
                  30,
                 100,
                 150,
                 300,
                 900,
                1200,
                6000,
                9000,
               18000,
               54000,
              180000,
              270000,
              540000,
             1620000,
             5400000,
            24300000,
            48600000,
            10**100
        ]
        
        # Backing
        drawMenuBox(screen, self.posx, self.posy, 550, 144)
        if len(world.get_component(dialog.PlayerData)[0][1].characters) <= self.index:
            return 1

        # Character portrait
        drawPortrait(self.posx+72, self.posy+72, screen)

        # Values
        character = world.get_component(dialog.PlayerData)[0][1].characters[self.index]
        hp = character.hp
        hpMax = character.baseStats.finalStats["maxHP"]
        className = character.playerClass

        xp = world.get_component(dialog.PlayerData)[0][1].sharedStats.xp
        level = character.baseStats.level
        toNext = xpPerLevelUp[character.baseStats.level] - xp

        name = character.name
        skillPoints = character.skillPoints

        # Draw values
        #  Name
        printScr(name, self.posx+148, self.posy+16, (255,255,255), self.font, screen)
        #  HP
        printScr(f"HP:{hp:4}/{hpMax:4}", self.posx+148, self.posy+36, (255,255,255), self.font, screen)
        drawHorizontalBar(screen, self.posx+280, self.posy+28, 160, 16, (0,255,0), hp, hpMax)
        #  Level
        printScr(f"Level {level:2}", self.posx+148, self.posy+56, (255,255,255), self.font, screen)
        #  XP to next
        if level < 20:
            drawHorizontalBar(screen, self.posx+280, self.posy+48, 160, 16, (0,255,255), xp, xpPerLevelUp[level])
            printScr(f"To next level: {toNext:8}", self.posx+148, self.posy+76, (255,255,255), self.font, screen)
        else:
            drawHorizontalBar(screen, self.posx+280, self.posy+48, 160, 16, (0,255,255), 1, 1)
            printScr(f"MAX LEVEL", self.posx+148, self.posy+76, (255,255,255), self.font, screen)
        #  Class
        printScr(f"Class: {className:10}", self.posx+148, self.posy+96, (255,255,255), self.font, screen)
        printScr(f"Unspent Skill Points: {skillPoints:2}", self.posx+148, self.posy+116, (255,255,255), self.font, screen)

class SharedStatsMenu:
    def __init__(self, posx, posy, visible):
        self.posx = posx
        self.posy = posy
        self.visible = visible
        self.font = pg.font.SysFont("Courier", 16)
    def draw(self, screen, world):
        sharedStats = xp = world.get_component(dialog.PlayerData)[0][1].sharedStats
        drawMenuBox(screen, self.posx, self.posy, 500, 50)
        printScr(f"TP:{sharedStats.tp:3}/{sharedStats.tpMax:3}  {sharedStats.gold:6} Gold  {0:6} Crystals", self.posx+24, self.posy+24, (255,255,255), self.font, screen)

class OptionsMenu:
    def __init__(self, left, top, length, height, optionList, visible):
        self.left = left
        self.top = top
        self.length = length
        self.height = height
        self.optionList = optionList
        self.visible = visible
        self.font = pg.font.SysFont("Courier", 20)
    def draw(self, screen, world):
        drawMenuBox(screen, self.left, self.top, self.length, self.height)
        for i, option in enumerate(self.optionList):
            printScr(option, self.left+16, self.top+24+i*48, (255,255,255), self.font, screen)

class BackgroundMenu:
    def __init__(self, visible):
        self.visible = visible
    def draw(self, screen, world):
        drawMenuBox(screen, 2, 2, 636, 476)