import pygame as pg
from typing import Dict, List
import esper
import random

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
        ##print(self.buttons)
        pg.event.pump()
class InputProcessor(esper.Processor):
    def process(self):
        """Pump inputs once per frame"""
        inputs = self.world.get_component(Input)[0][1]
        inputs.pumpInput()
class ActionCommandProcessor(esper.Processor):
    def process(self):
        """Check action commands"""
        inputs = self.world.get_component(Input)[0][1]
        screen = self.world.get_component(pg.Surface)[0][1]
        buttonDrawer = self.world.get_component(ButtonDrawer)[0][1]
        for id, comm in self.world.get_component(MultipleActionCommands):
            if comm.code < 0:
                comm.Update(inputs.buttons, screen, buttonDrawer)
            

class ButtonDrawer(Dict):
    def __init__(self, filenames):
        for filename in filenames:
            self[filename] = pg.image.load(f"assets/art/ui/{filename}.png")
    def drawShort(self, screen, short, posx, posy):
        self.draw(screen, {
            "down":"arrow_down",
            "left":"arrow_left",
            "right":"arrow_right",
            "up":"arrow_up",
            "z":"button_z",
            "x":"button_x",
            "c":"button_c"
        }[short], posx, posy)
    def draw(self, screen, name, posx, posy):
        rect = self[name].get_rect()
        rect.center = posx, posy
        screen.blit(self[name], rect)


class ActionCommand:
    """Base class for action commands to inherit from."""
    def __init__(self):
        self.window = 0
    def Update(self, inputs, screen, buttonDrawer):
        """Return code depends on result. Negative numbers mean still in progress, 0 is fail, and 1 is success."""
        return 1
    def Activate(self):
        pass

class MultipleActionCommands(ActionCommand):
    """Multiple action commands in sequence."""
    def __init__(self, commands, timeBetween):
        self.commands = commands
        self.commandCounter = 0
        self.code = -2
        self.timeBetween = timeBetween
        self.timer = 0
    def Activate(self):
        self.code = -2
        self.timer = 0
        self.commandCounter = 0
        for command in self.commands:
            command.Activate()
    def Update(self, inputs, screen, buttonDrawer):
        if self.code == -1:
            result = self.commands[self.commandCounter].Update(inputs, screen, buttonDrawer)
            if result == -1:
                return -1
            elif result == 1:
                self.commandCounter += 1
                self.code = -2
                return -2
            elif result == 0:
                self.code = 0
                return 0
        elif self.code == -2:
            self.timer += 1
            if self.timer >= self.timeBetween:
                self.timer = 0
                self.code = -1
                return -1
        if self.commandCounter >= len(self.commands):
            self.code = 1
            return 1
        return self.code

class buttonSequenceCommand(ActionCommand):
    """Shows a sequence of buttons that have to be pressed in time."""
    def __init__(self, buttons, amount, maxTime, visible):
        self.timer = 0
        self.maxTime = maxTime
        self.buttonAmount = amount
        self.buttonCounter = 0
        self.code = -3
        self.buttons = buttons
        self.currentHeld = ""
        self.visible = visible
    def Activate(self):
        self.timer = 0
        self.buttonCounter = 0
        self.code = -3
        self.currentHeld = ""
    def Update(self, inputs, screen, buttonDrawer):
        """Code -3 means start, -2 means started, -1 means button currently held, 0 or 1 means fail or succeed."""
        if self.code == -3:
            self.sequence = [random.choice(self.buttons) for x in range(self.buttonAmount)]
            if self.visible:
                pass
                #print(" ".join(self.sequence))
            else:
                pass
                #print(self.sequence[self.buttonCounter], end=" ", flush=True)
            self.code = -2
        else:
            if self.visible:
                offset = 32
            else:
                offset = 0
            pg.draw.rect(screen, (0,0,0), pg.Rect(40+16, 64+64+offset, 32*self.buttonAmount, 16))
            pg.draw.rect(screen, (255,0,0), pg.Rect(40+16, 64+64+offset, 32*self.buttonAmount*(self.timer)/self.maxTime, 16))
            for i in range(self.buttonAmount):
                if self.visible or self.buttonCounter >= i:
                    buttonDrawer.drawShort(screen, self.sequence[i], 40+i*32+32, 64+32)
                else:
                    buttonDrawer.draw(screen, "button_?", 40+i*32+32, 64+32)
            if self.visible:
                for i in range(self.buttonAmount):
                    if self.buttonCounter > i:
                        buttonDrawer.draw(screen, "bright_circle", 40+i*32+32, 64+64)
                    elif self.buttonCounter == i:
                        buttonDrawer.draw(screen, "red_circle", 40+i*32+32, 64+64)
                    else:
                        buttonDrawer.draw(screen, "dark_circle", 40+i*32+32, 64+64)
            if self.code == -2:
                self.timer += 1
                if inputs[self.sequence[self.buttonCounter]]:
                    self.currentHeld = self.sequence[self.buttonCounter]
                    self.buttonCounter += 1
                    self.code = -1
                    if self.buttonCounter < self.buttonAmount:
                        #print("*" if self.visible else self.sequence[self.buttonCounter], end=" ", flush=True)
                        pass
                    return -1
                if any(inputs[x] for x in set(self.buttons) - set([self.sequence[self.buttonCounter]])):
                    #print("Misinput!")
                    self.code = 0
                    return 0
            elif self.code == -1:
                ##print(f"Holding {self.currentHeld}")
                if not(inputs[self.currentHeld]):
                    self.code = -2
        if self.timer > self.maxTime:
            #print("Time out!")
            self.code = 0
            return 0
        if self.buttonCounter >= self.buttonAmount:
            #print("Success!")
            self.code = 1
            return 1
        return self.code



class pressButtonCommand(ActionCommand):
    """Press a specific button on cue."""
    def __init__(self, buttonNames, targetTime, starFrequency, visible, randomize):
        self.timer = 0
        self.targetTime = targetTime
        self.starFrequency = starFrequency
        self.delay = targetTime//starFrequency
        self.window = 10 * (1 if visible else 2)

        self.buttonNames = buttonNames
        
        self.code = -2
        self.visible = visible
        self.randomize = randomize

        if self.randomize:
            self.buttonName = random.choice(self.buttonNames)
        else:
            self.buttonName = self.buttonNames[0]
    def Activate(self):
        self.timer = 0
        self.code = -2
        if self.randomize:
            self.buttonName = random.choice(self.buttonNames)
        else:
            self.buttonName = self.buttonNames[0]
    def Update(self, inputs, screen, buttonDrawer):
        """Code -2 means button not yet held, -1 means started holding, then 0 or 1 mean success or fail."""
        i = 0
        for i in range(self.starFrequency+1):
            if self.timer < i*self.delay:
                if i >= self.starFrequency and not(self.visible):
                    buttonDrawer.draw(screen, "button_?", 40+i*32+32, 64+32)
                else:
                    buttonDrawer.draw(screen, "dark_circle", 40+i*32+32, 64+32)
            else:
                if i >= self.starFrequency:
                    if self.visible:
                        buttonDrawer.draw(screen, "red_circle", 40+i*32+32, 64+32)
                    else:
                        buttonDrawer.drawShort(screen, self.buttonName, 40+i*32+32, 64+32)
                else:
                    buttonDrawer.draw(screen, "bright_circle", 40+i*32+32, 64+32)
        if self.visible:
            buttonDrawer.drawShort(screen, self.buttonName, 40+i*32+32, 64+64)
        if self.code == -2:
            #print(f"Press {self.buttonName} when you see the exclamation marks" if self.visible else "Press the shown button in time!")
            self.code = -1
        elif self.code == -1:
            self.timer += 1
            if self.timer % self.delay == 0:
                if self.timer < self.targetTime:
                    pass
                    #print("*")
                else:
                    pass
                    #print("!!!" if self.visible else self.buttonName)
            if any(inputs.values()) and not(inputs[self.buttonName]):
                self.code = 0
                #print("Wrong Button!")
            elif inputs[self.buttonName]:
                finalEval = abs(self.targetTime - self.timer)
                #print(finalEval)
                self.code = (1 if finalEval <= self.window else 0)
                #print("Success!" if self.code == 1 else "Failure!")
        return self.code
                
class holdButtonCommand(ActionCommand):
    """Hold a specific button, then release on cue."""
    def __init__(self, buttonName, targetTime, starFrequency):
        self.timer = -1
        self.targetTime = targetTime
        self.starFrequency = starFrequency
        self.delay = targetTime//starFrequency
        self.window = 10
        self.buttonName = buttonName
        self.code = -2
    def Activate(self):
        self.timer = -1
        self.code = -2
    def Update(self, inputs, screen, buttonDrawer):
        """Code -2 means button not yet held, -1 means started holding, then 0 or 1 mean success or fail."""
        i = 0
        for i in range(self.starFrequency+1):
            if self.timer < i*self.delay:
                buttonDrawer.draw(screen, "dark_circle", 40+i*32+32, 64+32)
            else:
                if i >= self.starFrequency:
                    buttonDrawer.draw(screen, "red_circle", 40+i*32+32, 64+32)
                else:
                    buttonDrawer.draw(screen, "bright_circle", 40+i*32+32, 64+32)
        buttonDrawer.drawShort(screen, self.buttonName, 40+32, 64+64)
        if self.code == -2 and inputs[self.buttonName]:
            #print("Start!")
            self.code = -1
        elif self.code == -1:
            self.timer += 1
            if self.timer % self.delay == 0:
                if self.timer < self.targetTime:
                    pass
                    #print("*")
                else:
                    pass
                    #print("!!!")
            if not(inputs[self.buttonName]):
                finalEval = abs(self.targetTime - self.timer)
                #print(finalEval)
                self.code = (1 if finalEval <= self.window else 0)
                #print("Success!" if self.code == 1 else "Failure!")
        return self.code
