import pygame as pg
from textwrap import wrap
import dialog.dialog as dialog
import stats.stats as stats
import math
import copy

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
    def __init__(self, items, options, start):
        """
        General-purpose class that holds a dict of MenuItems
        """
        self.items = items
        self.options = options
        self.current = start
        self.active = False
    def Activate(self):
        self.active = True
        self.options[self.current].Activate
    def Update(self, screen, world, inputs):
        for item in self.items.values():
            if item.visible:
                item.draw(screen, world)
        self.options[self.current].draw(screen)
        result = self.options[self.current].Update(screen, world, inputs)
        self.options[self.current].oldInputs = copy.deepcopy(inputs)
        if result == -1:
            return -1
        elif result == -2:
            self.active = False
        else:
            print(result)
            self.options[self.current].Deactivate()
            self.current = result
            self.options[self.current].Activate()
            return -1

def PauseMenu():
    pauseMenu = Menu(
    {
        "Background Layer 0":BackgroundMenu(True),
        "Portrait 0":PortraitMenu(2,2,True,0),
        "Portrait 1":PortraitMenu(2,144,True,1),
        "Portrait 2":PortraitMenu(2,286,True,2),
        "SharedStatsViewer":SharedStatsMenu(2,426,True),
        "OptionsSidebar":OptionsMenu(452,2,188,474,["View Stats", "Equipment", "Inventory", "Change Spells", "Change Order", "Quit to Title"], True),
        "Background Layer 1":BackgroundMenu(False),
        "Stats 0":StatsMenu(False,0),
        "Stats 1":StatsMenu(False,1),
        "Stats 2":StatsMenu(False,2)
    },
    {
        "OptionsSidebar":MenuOptionsHandler(["Stats","Equipment","Inventory","Spells","Order","Quit"],"OptionsSidebar",
                                                448,22,0,48),
        "Stats":MenuOptionsHandler(["Stats0","Stats1","Stats2"],"OptionsSidebar",
                                       8,72,0,144),
        "Equipment":MenuOptionsHandler(["Equipment0","Equipment1","Equipment2"],"OptionsSidebar",
                                       8,72,0,144),
        "Inventory":MenuOptionsHandler([],"OptionsSidebar",
                                       8,72,0,144),
        "Spells":MenuOptionsHandler(["Spells0","Spells1","Spells2"],"OptionsSidebar",
                                       8,72,0,144),
        "Order":MenuOptionsHandler(["Order0","Order1","Order2"],"OptionsSidebar",
                                       8,72,0,144)
    },
    "OptionsSidebar"
    )

    for i in range(3):
        pauseMenu.options[f"Order{i}"] = MenuOptionsHandler([f"Order{i}|0",f"Order{i}|1",f"Order{i}|2"],"Order",
                                       8,72,0,144)
        for j in range(3):
            pauseMenu.options[f"Order{i}|{j}"] = MenuSwapHandler(i,j,"OptionsSidebar")

    for i in range(3):
        pauseMenu.options[f"Stats{i}"] = MenuChangerHandler({"Background Layer 1":True,f"Stats {i}":True},pauseMenu,f"EV{i}")
        pauseMenu.options[f"EV{i}"] = MenuOptionsHandler([],f"StatsBack{i}",0,0,0,0)
        pauseMenu.options[f"StatsBack{i}"] = MenuChangerHandler({"Background Layer 1":False,f"Stats {i}":False},pauseMenu,"OptionsSidebar")
    
    return pauseMenu

class MenuHandler:
    """
    Base class for active menu elements.
    """
    def __init__(self, next, previous):
        self.next = next
        self.previous = previous
        self.active = False
    def Activate(self):
        self.active = True
    def Deactivate(self):
        self.active = False
    def draw(self, screen):
        pass

class MenuChangerHandler(MenuHandler):
    """
    Shows/hides menu displays, then goes to the next.
    """
    def __init__(self, displayDict, parentMenu, next):
        self.active = False
        self.displayDict = displayDict
        self.parentMenu = parentMenu
        self.next = next
    def Activate(self):
        self.active = True
    def Deactivate(self):
        self.active = False
    def Update(self, screen, world, inputs):
        for key, value in self.displayDict.items():
            self.parentMenu.items[key].visible = value
        return self.next

class MenuSwapHandler(MenuHandler):
    """
    Swaps two party positions, then goes to the next.
    """
    def __init__(self, pos0, pos1, next):
        self.active = False
        self.pos0 = pos0
        self.pos1 = pos1
        self.next = next
    def Activate(self):
        self.active = True
    def Deactivate(self):
        self.active = False
    def Update(self, screen, world, inputs):
        partyList = world.get_component(dialog.PlayerData)[0][1].characters
        temp = partyList[self.pos0]
        partyList[self.pos0] = partyList[self.pos1]
        partyList[self.pos1] = temp
        return self.next

class MenuOptionsHandler(MenuHandler):
    """
    Holds a list of selectable options, and handles input to it including confirm/cancel.
    """
    def __init__(self, optionList, previous, posx, posy, shiftx, shifty, mode="vertical"):
        self.oldInputs = {
            "confirm":True,
            "cancel":True,
            "menu":True,
            "left":True,
            "right":True,
            "up":True,
            "down":True
        }
        self.selected = 0
        self.optionList = optionList
        self.optionCount = len(optionList)
        self.previous = previous
        self.posx = posx
        self.posy = posy
        self.shiftx = shiftx
        self.shifty = shifty
        self.mode = mode
        if self.mode == "vertical":
            self.plusOption = "down"
            self.minusOption = "up"
        else:
            self.plusOption = "right"
            self.minusOption = "left"
        self.active = False
        self.pointer = pg.image.load("assets/art/ui/menus/pointer.png").convert_alpha()
    def Activate(self):
        self.selected = 0
        self.active = True
        self.oldInputs = {
            "confirm":True,
            "cancel":True,
            "menu":True,
            "left":True,
            "right":True,
            "up":True,
            "down":True
        }
    def Deactivate(self):
        self.active = False
    def draw(self, screen):
        """
        Draws a pointer at the location of the current option.
        """
        if self.optionList:
            rect = self.pointer.get_rect()
            rect.center = self.posx + self.selected*self.shiftx, self.posy + self.selected*self.shifty
            screen.blit(self.pointer, rect)
    def Update(self, screen, world, inputs):
        if self.oldInputs["confirm"] == False and inputs["confirm"]:
            # Return chosen MenuOptionsHandler name
            print("Confirm")
            return self.optionList[self.selected]
        if self.oldInputs["cancel"] == False and inputs["cancel"]:
            # Return previous MenuOptionsHandler name
            print("Cancel")
            return self.previous
        if self.oldInputs[self.plusOption] == False and inputs[self.plusOption]:
            print("+")
            self.selected = (self.selected + 1) % self.optionCount
        if self.oldInputs[self.minusOption] == False and inputs[self.minusOption]:
            print("-")
            self.selected = (self.selected - 1) % self.optionCount
        return -1

        
        
        

class MenuItem:
    def __init__(self, posx, posy, visible):
        self.posx = posx
        self.posy = posy
        self.visible = visible
    def draw(self, screen, world):
        pass
    def Update(self, screen, world, inputs):
        pass

class StatsMenu(MenuItem):
    def __init__(self, visible, index):
        self.visible = visible
        self.font = pg.font.SysFont("Courier", 16)
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
        
        character = world.get_component(dialog.PlayerData)[0][1].characters[self.index]
        hp = character.hp
        hpMax = character.baseStats.finalStats["maxHP"]
        className = character.playerClass

        xp = world.get_component(dialog.PlayerData)[0][1].sharedStats.xp
        level = character.baseStats.level
        toNext = xpPerLevelUp[character.baseStats.level] - xp

        name = character.name
        skillPoints = character.skillPoints

        self.posx = 16
        self.posy = 16
        
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

        for i, skillName in enumerate(["maxHP", "physAtk", "magiAtk", "physDef", "magiDef"]):
            printScr(f"{skillName:8}:{character.baseStats.finalStats[skillName]:4} ({character.baseStats.evs[skillName]:1}/8 EVs)", self.posx, self.posy+144+i*24, (255,255,255), self.font, screen)

        shortNames = {"maxHP":"HP","physAtk":"PA","physDef":"PD","magiAtk":"MA","magiDef":"MD"}
        
        # Stat Pentagon
        #  Backing Pentagon and inner tickmarks
        pg.draw.polygon(screen, (255,255,255), [(math.cos(math.pi*i*2/5-math.pi/2)*150+448,math.sin(math.pi*i*2/5-math.pi/2)*150+320) for i in range(5)],4)
        pg.draw.polygon(screen, (255,255,255), [(math.cos(math.pi*i*2/5-math.pi/2)*75+448,math.sin(math.pi*i*2/5-math.pi/2)*75+320) for i in range(5)],2)
        maxValue = stats.baseStatCalc(character.baseStats.level, 2, 8)

        finalPoly = []
        
        for i, skillName in enumerate(["maxHP", "physAtk", "physDef", "magiDef", "magiAtk"]):
            pg.draw.line(screen, (255,255,255), [448, 320], [math.cos(math.pi*i*2/5-math.pi/2)*150+448, math.sin(math.pi*i*2/5-math.pi/2)*150+320], 1)
            finalPoly.append([math.cos(math.pi*i*2/5-math.pi/2)*150*character.baseStats.finalStats[skillName]/maxValue+448, math.sin(math.pi*i*2/5-math.pi/2)*150*character.baseStats.finalStats[skillName]/maxValue+320])
            printScr(shortNames[skillName], math.cos(math.pi*i*2/5-math.pi/2)*165+448, math.sin(math.pi*i*2/5-math.pi/2)*165+320, (255,255,255), self.font, screen)
        pg.draw.polygon(screen, (100,100,255), finalPoly)


class PortraitMenu(MenuItem):
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

class SharedStatsMenu(MenuItem):
    def __init__(self, posx, posy, visible):
        self.posx = posx
        self.posy = posy
        self.visible = visible
        self.font = pg.font.SysFont("Courier", 16)
    def draw(self, screen, world):
        sharedStats = xp = world.get_component(dialog.PlayerData)[0][1].sharedStats
        drawMenuBox(screen, self.posx, self.posy, 500, 50)
        printScr(f"TP:{sharedStats.tp:3}/{sharedStats.tpMax:3}  {sharedStats.gold:6} Gold  {0:6} Crystals", self.posx+24, self.posy+24, (255,255,255), self.font, screen)

class OptionsMenu(MenuItem):
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

class BackgroundMenu(MenuItem):
    def __init__(self, visible):
        self.visible = visible
    def draw(self, screen, world):
        drawMenuBox(screen, 2, 2, 636, 476)