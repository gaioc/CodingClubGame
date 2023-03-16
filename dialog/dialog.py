import pygame as pg
from os import system
from os.path import abspath
import esper
from dataclass import dataclass
from typing import List, Dict, Tuple
import pathlib
import battle.battle as battle
from mapScreen.mapScreen import Input, PlayerMove, loadMap, NPCHolder, MapHolder, TileArrayComponent, Position
import audio.audio as audio

#PYGAME DEPENDENCIES
pg.font.init()

def cls():
    """Clear console."""
    system("clear")
def printScr(text: str, posx: float, posy: float, colour: pg.Color, font: pg.font.Font, screen: pg.Surface):
    """
    Render text at (posx,posy) of screen, using font in provided colour.
    """
    render = font.render(text, True, colour)
    rect = render.get_rect()
    rect.center = posx, posy
    rect.left = posx
    screen.blit(render, rect)

class Options:
    """
    Component that holds all ingame options and constants, as well as references to important objects
    """
    textSpeed : int = 1
    Screen : pg.Surface
    def __init__(self, screen: pg.Surface, textSpeed: int):
        self.textSpeed = textSpeed
        self.Screen = screen



class DialogInstance:
    """
    Base class for dialog actions to inherit from
    """
    active : bool = False
    def __init__(self):
        pass
    def Update(self, screen, inputs, textSpeed, playerData, world):
        return -2

class DialogWait(DialogInstance):
    active : bool = False
    next : int = -2
    def __init__(self, amount, next):
        self.next = next
        self.amount = amount # In Frames (30fps)
        self.counter = 0
    def Activate(self):
        self.active = True
        self.counter = 0
    def Update(self, screen, inputs, textSpeed, playerData, world):
        self.counter += 1
        if self.counter > self.amount:
            return self.next
        else:
            return -1

class DialogHealPlayer(DialogInstance):
    active : bool = False
    next : int = -2
    def __init__(self, next):
        self.next = next
    def Activate(self):
        self.active = True
    def Update(self, screen, inputs, textSpeed, playerData, world):
        """
        Heal the player's party to full and restore TP.
        """
        print("NOTIMPLEMENTED: HEAL PARTY")
        return self.next

class DialogGiveQuest(DialogInstance):
    active : bool = False
    questID : str
    next : int = -2
    def __init__(self, questID, next):
        self.questID = questID
        self.next = next
    def Activate(self):
        self.active = True
    def Update(self, screen, inputs, textSpeed, playerData, world):
        """
        Give the player a quest.
        """
        if self.questID not in playerData.questList or playerData.questList[self.questID] == -1:
            playerData.questList[self.questID] = 0
        return self.next

class DialogBumpQuest(DialogInstance):
    active : bool = False
    questID : str
    next : int = -2
    def __init__(self, questID, next):
        self.questID = questID
        self.next = next
    def Activate(self):
        self.active = True
    def Update(self, screen, inputs, textSpeed, playerData, world):
        """
        Bump a quest's level of completion up by one.
        """
        playerData.questList[self.questID] += 1
        return self.next

class DialogTakeItem(DialogInstance):
    active : bool = False
    item : str
    next : int = -2
    def __init__(self, item, next):
        self.item = item
        self.next = next
    def Activate(self):
        self.active = True
    def Update(self, screen, inputs, textSpeed, playerData, world):
        """
        Take an item from player inventory
        """
        playerData.inventory.pop(playerData.inventory.index(self.item))
        return self.next
class DialogGiveItem(DialogInstance):
    active : bool = False
    item : str
    next : int = -2
    def __init__(self, item, next):
        self.item = item
        self.next = next
    def Activate(self):
        self.active = True
    def Update(self, screen, inputs, textSpeed, playerData, world):
        """
        Give an item to player inventory
        """
        playerData.inventory.append(self.item)
        return self.next
class DialogMovePlayer(DialogInstance):
    active : bool = False
    posx : int
    posy : int
    speed : int
    next : int = -2
    def __init__(self, posx, posy, speed, next):
        self.posx = posx
        self.posy = posy
        self.speed = speed
        self.next = next
    def Activate(self):
        self.active = True
    def Update(self, screen, inputs, textSpeed, playerData, world):
        """
        Move player to location with speed.
        """
        player = world.get_components(PlayerMove, Position)[0][1][1]

        if player.posx != self.posx:
            player.posx -= (player.posx-self.posx)/abs(player.posx-self.posx) * self.speed
        if player.posy != self.posy:
            player.posy -= (player.posy-self.posy)/abs(player.posy-self.posy) * self.speed

        if player.posx == self.posx and player.posy == self.posy:
            print("Done")
            player.predictedposx = int(player.posx)
            player.predictedposy = int(player.posy)
            player.posx = int(player.posx)
            player.posy = int(player.posy)
            return self.next
        else:
            return -1
        


class DialogLoadMap(DialogInstance):
    """
    Loads map and places player at the given position.
    """
    active : bool = False
    mapName : str
    playerX : int
    playerY : int
    next : int = -2

    def __init__(self, mapName, playerX, playerY, next):
        self.mapName = mapName
        self.playerX = playerX
        self.playerY = playerY
        self.next = next
    def Activate(self):
        self.active = True
    def Update(self, screen, inputs, textSpeed, playerData, world):
        """
        Load the given map and place the player at playerX, playerY. (tile position)
        """
        mapsDict = world.get_component(MapHolder)[0][1]
        npcDict = world.get_component(NPCHolder)[0][1]
        tileMapping = world.get_component(TileArrayComponent)[0][1].data

        playerPos = world.get_components(Position, PlayerMove)[0][1][0]
        
        loadMap(world, mapsDict, self.mapName, npcDict, tileMapping)

        playerPos.posx = self.playerX*32
        playerPos.posy = self.playerY*32
        playerPos.predictedposx = self.playerX*32
        playerPos.predictedposy = self.playerY*32

        return self.next

class DialogBattle(DialogInstance):
    """
    Start a battle defined in battles.txt by name. BattleDict must be initialized.
    Waits until all battles are done to continue.
    """
    def __init__(self, battle, next):
        self.battle = battle
        self.next = next
    def Activate(self):
        self.active = True
        self.state = 0
    def Update(self, screen, inputs, textSpeed, playerData, world):
        if self.state == 0:
            print(world.get_component(PlayerData)[0][1].characters)
            battleHolder = world.get_component(battle.BattleDict)[0][1][self.battle]
            battle.StartBattle(battleHolder, world.get_component(PlayerData)[0][1].characters, world.get_component(PlayerData)[0][1].sharedStats, world)
            self.state = 1
        else:
            done = True
            for i, battleHandler in world.get_component(battle.BattleHandler):
                if battleHandler.active:
                    done = False
            if done:
                return self.next
        return -1
        

class DialogText(DialogInstance):
    """                                                                                    
    One "segment" of dialogue. Used internally by the Dialog component.
    """
    text : str = ""
    textInd : float = 0
    playerOptions : List[str] = []
    nextDialog : List[int] = []
    active : bool = False
    chosenOption : int = 0
    btnHeld : bool = False

    def __init__(self, text: str, playerOptions: List[str], nextDialog: List[int]):
        self.text = text
        self.playerOptions = playerOptions
        self.nextDialog = nextDialog
        self.font = pg.font.SysFont("OpenSans Mono", 28)
    
    def Activate(self):
        self.active = True
        self.textInd = 0
        self.chosenOption = 0
        self.btnHeld = True #used to make sure player does not accidentally skip dialogue
    def Update(self, screen: pg.Surface, inputs, textSpeed: int, playerData, world) -> int:
        audioDict = world.get_component(audio.AudioDict)[0][1]

        #Draw dialog box
        pg.draw.rect(screen, (30,30,30), pg.Rect(8, 379, 624, 96))
        #cls()
        #Draw text
        
        toDisplay = list(self.text[0:int(self.textInd+textSpeed)])
        
        wrapping = 64
        
        for i in range(0, len(toDisplay), wrapping):
            printScr("".join(toDisplay[i:i+wrapping]), 16, 394+20*i//wrapping, (255,255,255), self.font, screen)
            finalPos = i

        if int(self.textInd / textSpeed) % 3 == 0 and self.textInd <= len(self.text):
            # play text noise
            print("Text Noise")
            audioDict.play("textNoise")
        
        #Check for skipping text scrolling
        if inputs.buttons["cancel"]:
            #print("SKIP")
            self.textInd = len(self.text)

        self.textInd += textSpeed

        
        
            
        #End of text reached?
        if self.textInd > len(self.text):
            if len(self.playerOptions) > 0:
                for i in range(len(self.playerOptions)):
                    printScr(f"{self.playerOptions[i]}", 16, 416+20*i+finalPos, (255,255,255), self.font, screen)
                #Find where to jump to from this point
                pg.draw.circle(screen, (255,255,255), (12, 416+20*self.chosenOption+finalPos), 4)
                if self.btnHeld:
                    if not(any(inputs.buttons.values())):
                        self.btnHeld = False
                    else:
                        return -1
                if inputs.buttons["confirm"]:
                    # Reset dialog to original state
                    self.textInd = 0
                    self.btnHeld = True
                    temp = self.chosenOption
                    self.chosenOption = 0
                    return self.nextDialog[temp]
                    self.btnHeld = True
                elif inputs.buttons["up"]:
                    audioDict.play("menuMove")
                    self.chosenOption = (self.chosenOption - 1) % len(self.playerOptions)
                    self.btnHeld = True
                elif inputs.buttons["down"]:
                    audioDict.play("menuMove")
                    self.chosenOption = (self.chosenOption + 1) % len(self.playerOptions)
                    self.btnHeld = True
                return -1
            else:
                if self.nextDialog[0] == -2:
                    #print("RECT")
                    pg.draw.rect(screen, (0,255,0), pg.Rect(308, 464, 16, 16))
                else:
                    #print("CIRCLE")
                    pg.draw.circle(screen, (0,255,0), (316, 472), 8)
                pg.display.flip()
                if self.btnHeld:
                    if not(any(inputs.buttons.values())):
                        self.btnHeld = False
                    return -1
                if inputs.buttons["confirm"]:
                    # Reset dialog to original state
                    self.textInd = 0
                    self.btnHeld = True
                    self.chosenOption = 0
                    return self.nextDialog[0]
                else:
                    return -1
        
        return -1


class Dialog:
    """
    Implementation of a simple dialog system using ECS.
    Consists of a list of "DialogueInstance"s.
    Update is run every frame if activated.
    """
    dialogIndex : int = 0
    texts = List[DialogInstance]
    #textOptions : list[list[str]]
    active : bool = False
    def __init__(self, texts: List[DialogInstance]):
        self.texts = texts
    def Activate(self, npcName):
        self.active = True
        self.npcName = npcName
        self.dialogIndex = 0
    def Update(self, screen, inputs, textSpeed, playerData, world) -> int:
        #Update current DialogInstance
        try:
            result = self.texts[self.dialogIndex].Update(screen, inputs, textSpeed, playerData, world)
        except IndexError:
            raise IndexError("Invalid dialogue jump. Make sure dialogue jumps to a valid index.")
        if result == -2:
            #Code -2 means end of dialog
            self.active = False
            self.dialogIndex = 0
            if not(self.npcName in playerData.npcsInteractedWith):
                playerData.npcsInteractedWith.append(self.npcName)
            
            world.get_component(PlayerMove)[0][1].Activate()
            
            return -2
        if result == -1:
            #Code -1 means continue
            return -1
        else:
            #All other codes mean to jump to indexed dialogue
            self.texts[self.dialogIndex].active = False
            self.dialogIndex = result
            try:
                self.texts[self.dialogIndex].Activate()
            except IndexError:
                raise IndexError("Invalid dialogue jump. Make sure dialogue jumps to a valid index.")

class Quest:
    """
    Container class that contains a quest name, and its completion status. 
    (-1 is not taken, 0 is not completed, and everything above that refers to individual stages of completion.)
    If a quest has multiple parts, track each part with an individual Quest object.
    """
    def __init__(self, name, status):
        self.name = name
        self.status = status

class PlayerData:
    """
    Contains all information that conditions could need, 
    and all data that needs to be saved.
    (progression, interacted NPCs, inventory, and all the characters)
    """
    def __init__(self, inventory, questList, npcsInteractedWith, characters, sharedStats):
        self.inventory = inventory
        self.questList = questList
        self.npcsInteractedWith = npcsInteractedWith
        self.characters = characters # First 1 is Lux, next 2 are on party, rest are off
        self.sharedStats = sharedStats

class Condition:
    """
    Base class for conditions to inherit from.
    """
    def __init__(self):
        pass
    def verify(self, name, playerData):
        """
        Always returns true. Useful for bottom priority dialogue.
        """
        return True
class MultipleAllConditions(Condition):
    def __init__(self, conditions):
        """
        Takes a list of Conditions. Can be recursive in nature.
        """
        self.conditions = conditions
    def verify(self, name, playerData):
        """
        Returns true if ALL conditions are met
        """
        return all([cond.verify(name, playerData) for cond in self.conditions])
class MultipleAnyConditions(Condition):
    def __init__(self, conditions):
        """
        Takes a list of Conditions. Can be recursive in nature.
        """
        self.conditions = conditions
    def verify(self, name, playerData):
        """
        Returns true if ANY conditions are met
        """
        return any([cond.verify(name, playerData) for cond in self.conditions])
class NotCondition(Condition):
    def __init__(self, condition):
        """
        Takes a Condition. Can be recursive in nature.
        """
        self.condition = condition
    def verify(self, name, playerData):
        """
        Returns true if condition is NOT met.
        """
        return not(self.condition.verify(name, playerData))
class QuestStatusCondition(Condition):
    def __init__(self, questName, questStatus):
        self.questName = questName
        self.questStatus = questStatus
    def verify(self, name, playerData):
        """
        Returns true if relevant quest is at relevant level of completion
        """
        if self.questName in playerData.questList.keys():
            return playerData.questList[self.questName] == self.questStatus
        else:
            return self.questStatus == -1
class InventoryCondition(Condition):
    def __init__(self, itemName):
        self.itemName = itemName
    def verify(self, name, playerData):
        """
        Returns true if player has relevant item
        """
        return self.itemName in playerData.inventory
class PlayerClassCondition(Condition):
    def __init__(self, className):
        self.className = className
    def verify(self, name, playerData):
        return self.className == playerData.characters[0].playerClass
class FirstInteractionCondition(Condition):
    def __init__(self):
        pass
    def verify(self, name, playerData):
        """
        Returns true if name is not in the list of interacted NPCs.
        """
        return not(name in playerData.npcsInteractedWith)


class BrainInstance:
    """
    Class that contains a condition and a dialogue
    """
    def __init__(self, condition, dialogue):
        self.condition = condition
        self.dialogue = dialogue

class NPCBrain:
    """
    Component that determines the dialogue used by an NPC, as well as that NPC's identifier.
    """
    name : str #MUST BE UNIQUE!!!
    brainOptions : List[BrainInstance] #ORDER MATTERS: Lower index means higher priority
    def __init__(self, name, brainOptions):
        """
        Basic constructor. Will be used internally and in readNPCFile only.
        """
        self.name = name
        self.brainOptions = brainOptions
    def fetchCurrent(self, playerData):
        """
        Returns the highest priority eligible dialogue. playerData is still a WIP
        """
        for instance in self.brainOptions:
            if instance.condition.verify(self.name, playerData):
                return instance.dialogue
        return None
    def interact(self, world, playerData):
        """
        Wrapper function that grabs the highest priority eligible dialogue and displays it.
        Needs a reference to the game world to interact with it and create an entity. Returns said entity.
        """
        currentDialog = self.fetchCurrent(playerData)
        

        

        dialogEntity = world.create_entity(currentDialog)
        
        currentDialog.Activate(self.name)
        
        return dialogEntity
        


class DialogProcessor(esper.Processor):
    """
    ECS System that updates active dialog boxes automatically.
    """
    def process(self):
        optionobj, options = self.world.get_component(Options)[0]
        inputs = self.world.get_component(Input)[0][1]
        playerData = self.world.get_component(PlayerData)[0][1]
        for ent, dial in self.world.get_component(Dialog):
            if dial.active:
                dial.Update(options.Screen, inputs, options.textSpeed, playerData, self.world)
        pg.display.flip()

def parseCondition(conditionStr):
    funcName = conditionStr.split("(")[0]
    args = "(".join(conditionStr.split("(")[1:])[:-1]

    if funcName == "FirstInteraction":
        return FirstInteractionCondition()
    elif funcName == "QuestStatus":
        argList = args.split(", ")
        return QuestStatusCondition(argList[0], int(argList[1]))
    elif funcName == "HasItem":
        return InventoryCondition(args)
    elif funcName == "PlayerClass":
        return PlayerClassCondition(argList[0])
    elif funcName == "Auto":
        return Condition()
    elif funcName == "Not":
        return NotCondition(parseCondition(args))
    elif funcName == "Any":
        layer = 0
        argList = []
        end = 0
        for i in range(len(args)):
            if args[i] == "(":
                layer += 1
            elif args[i] == ")":
                layer -= 1
            elif args[i] == "," and layer == 0:
                argList.append(args[end:i])
                end = i+2
            if i == len(args) - 1:
                argList.append(args[end:])
        return MultipleAnyConditions([parseCondition(arg) for arg in argList])
    elif funcName == "All":
        layer = 0
        argList = []
        end = 0
        for i in range(len(args)):
            if args[i] == "(":
                layer += 1
            elif args[i] == ")":
                layer -= 1
            elif args[i] == "," and layer == 0:
                argList.append(args[end:i])
                end = i+2
            if i == len(args) - 1:
                argList.append(args[end:])
        return MultipleAllConditions([parseCondition(arg) for arg in argList])

def readNPCFile(npcFileContents, dialogDict):
    """
    Reads a string containing multiple formatted NPCBrains,
    and returns a Dict object with their names and parsed content.
    Needs an already parsed dict with dialog.
    """
    npcDict = dict()
    # SPLIT FILE INTO INDIVIDUAL NPCBRAINS
    rawNPCs = npcFileContents.split("\n\n")
    for rawNPC in rawNPCs:
        name = rawNPC.split("\n")[0]
        lines = rawNPC.split("\n")[1:]
        instances = []
        for line in lines:
            condition, dialog = line.split(": ")
            instances.append(BrainInstance(parseCondition(condition), dialogDict[dialog]))
        npcDict[name] = NPCBrain(name, instances)
    return npcDict
def readDialogFile(dialogFileContents):
    """
    Reads a string containing multiple formatted dialogs, 
    and returns a Dict object with their names and parsed content.
    """
    dialogDict = dict()
    # SPLIT FILE INTO INDIVIDUAL DIALOGS
    rawDialogs = dialogFileContents.split("\n\n")
    for rawDialog in rawDialogs:
        # GET ID USED IN DICT
        name = rawDialog.split("\n")[0]
        # GET LINES OF DIALOG/OTHER FUNCTIONS
        contents = rawDialog.split("\n")[1:]
        finalContents = []
        for line in contents:
            parts = line.split("|")
            data = parts[0]
            #print("|".join(parts))
            options = [i for i in parts[1].split(",") if i] # Remove redundant/empty entries
            next = [i for i in list(map(int, parts[2].split(","))) if i] # Remove redundant/empty entries
            if line[0] == "\\":
                #PROCESS DIALOG FUNCTIONS
                parts = line.split("|")
                functionWithArgs = data.split(" ")
                function = functionWithArgs[0]
                if function == "\HealPlayer":
                    finalContents.append(DialogHealPlayer(int(parts[2])))
                elif function == "\GiveQuest":
                    finalContents.append(DialogGiveQuest(functionWithArgs[1], int(parts[2])))
                elif function == "\TakeItem":
                    finalContents.append(DialogTakeItem(functionWithArgs[1],int(parts[2])))
                elif function == "\GiveItem":
                    finalContents.append(DialogGiveItem(functionWithArgs[1],int(parts[2])))
                elif function == "\BumpQuest":
                    finalContents.append(DialogBumpQuest(functionWithArgs[1],int(parts[2])))
                elif function == "\LoadMap":
                    finalContents.append(DialogLoadMap(functionWithArgs[1], int(functionWithArgs[2]), int(functionWithArgs[3]), int(parts[2])))
                elif function == "\MovePlayer":
                    finalContents.append(DialogMovePlayer(int(functionWithArgs[1])*32, int(functionWithArgs[2])*32, int(functionWithArgs[3]), int(parts[2])))
                elif function == "\Wait":
                    finalContents.append(DialogWait(functionWithArgs[1],int(parts[2])))
                elif function == "\Battle":
                    finalContents.append(DialogBattle(functionWithArgs[1],int(parts[2])))
                elif function == "\Empty":
                    finalContents.append(DialogInstance())
                else:
                    finalContents.append(DialogInstance())
            else:
                finalContents.append(DialogText(data, options, next))
        dialogDict[name] = Dialog(finalContents)
    return dialogDict
