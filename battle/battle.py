import pygame as pg
import esper
import random
from typing import Dict, List
import stats.playerStats as pStats
import battle.actionCommands as act
import mapScreen.mapScreen as mapScreen

pg.font.init()



def printtoscreen(screen, posx, posy, text, font, colour):
    # Print text to screen
    render = font.render(text, True, colour)
    rect = render.get_rect()
    rect.center = posx, posy
    rect.left = posx
    screen.blit(render, rect)

def damageCalc(attack, defense, baseDamage):
    """
    Calculates damage given attack, defense, and base damage.
    """
    return max(1, int((attack**2 * baseDamage) / (attack + defense)))


class BattleEntity:
    def __init__(self, name, stats, hp, spells):
        self.name = name
        self.stats = stats
        self.hp = hp
        self.spells = spells
    def fromCharacter(self, character):
        name = character.name
        stats = character.totalStats
        hp = character.hp
        spells = [spellList[i] for i in character.spellNames]
        self.__init__(name, stats, hp, spells)
        return self
    def updateCharacter(self, character):
        character.hp = self.hp
class BattleEnemy(BattleEntity):
    def __init__(self, name, stats, hp, spells, sprite, enemyAI):
        self.name = name
        self.stats = stats
        self.hp = hp
        self.spells = spells
        self.sprite = sprite
        self.enemyAI = enemyAI

class EnemyAI:
    def __init__(self):
        pass
    def decide(self, options, enemies, players):
        spellInd = random.randint(0,len(options)-1)
        if options[spellInd].targeting in ["1ally", "allallies", "self"]:
            targets = enemies
        elif options[spellInd].targeting in ["1enemy", "allenemies"]:
            targets = players
        return EnemyAction(spellInd, random.randint(0,len(targets)-1), targets)
        

class Spell:
    def __init__(self, name, description, targeting, actionCommand, effects):
        self.name = name
        self.description = description
        self.targeting = targeting
        self.actionCommand = actionCommand
        self.effects = effects
    def Activate(self):
        self.actionCommand.Activate()
    def EnemyAction(self, enemy, enemies, players, targetInd, potentialTargets, user, inputs, screen, world, buttonDrawer):
        if self.targeting in ["self", "allallies", "allenemies"]:
            targets = potentialTargets
        else:
            targets = [potentialTargets[targetInd]]

        # GUARD ACTION COMMAND GOES HERE!
        result = self.actionCommand.Update(inputs, screen, buttonDrawer)

        if result >= 0:
            for effect in self.effects:
                effect.activateEffect(user, enemy, targets, enemies, players, 1-result/2, world)
        else:
            return -1
    def PerformAction(self, player, players, enemies, targetInd, potentialTargets, user, inputs, screen, world, buttonDrawer):
        if self.targeting in ["self", "allallies", "allenemies"]:
            targets = potentialTargets
        else:
            targets = [potentialTargets[targetInd]]

        # ACTION COMMAND GOES HERE!
        result = self.actionCommand.Update(inputs, screen, buttonDrawer)

        if result >= 0:
            for effect in self.effects:
                effect.activateEffect(user, player, targets, players, enemies, (result+1)/2, world)
        else:
            return -1

class SpellEffect:
    """Base class for spell effects."""
    def __init__(self):
        pass
    def activateEffect(self, user, player, targets, actionCommandResult, world):
        print("Unspecified Spell Effect")

class DamageEffect(SpellEffect):
    """Deals damage based on scaling stats and base damage."""
    def __init__(self, amount, offensive, defensive):
        self.amount = amount
        self.offensive = offensive
        self.defensive = defensive
    def activateEffect(self, user, player, targets, players, enemies, actionCommandResult, world):
        attacking = user.stats[self.offensive] * actionCommandResult
        for i, target in enumerate(targets):
            defending = target.stats[self.defensive]
            damage = damageCalc(attacking, defending, self.amount)
            if player:
                ind = enemies.index(target)
                world.create_entity(TemporaryText(str(damage), (255*random.randint(7,10)/10,0,0), 30, 320 - (len(enemies)-1)*0.5*160+random.randint(-32, 32) + ind*160 - 64+random.randint(-32, 32), 200))
            #print(f"{damage} damage to {target.name}!")
            target.hp -= damage
            if target.hp < 0:
                target.hp = 0
class HealEffect(SpellEffect):
    """Heals an amount based on scaling stat."""
    def __init__(self, amount, scaling):
        self.amount = amount
        self.scaling = scaling
    def activateEffect(self, user, player, targets, players, enemies, actionCommandResult, world):
        scale = user.stats[self.scaling] * actionCommandResult
        for i, target in enumerate(targets):
            if target.hp > 0:
                healing = int(scale*self.amount)
                if player:
                    ind = players.index(target)
                    world.create_entity(TemporaryText(str(healing), (0,255,0), 30, 48+ind*200+64, 80))
                target.hp += healing
                if target.hp > target.stats["maxHP"]:
                    target.hp = target.stats["maxHP"]
class StatusSpellEffect(SpellEffect):
    """Grants target a status effect with a chance."""
    def __init__(self, effect, chance):
        self.effect = effect
        self.chance = chance
    def activateEffect(self, user, player, targets, players, enemies, actionCommandResult, world):
        pass

class SharedStats:
    def __init__(self, tp, tpMax, xp):
        self.tp = tp
        self.tpMax = tpMax
        self.xp = xp

class TemporaryText:
    def __init__(self, text, colour, time, posx, posy):
        self.text = text
        self.colour = colour
        self.time = time
        self.timer = 0
        self.posx = posx
        self.posy = posy
        self.font = pg.font.SysFont("Impact", 80)
        self.font.set_bold(True)
        
    def Update(self, screen, world, id):
        """Needs a reference to own entity's id for deletion."""
        #pg.draw.ellipse(screen, (self.colour[0]/2,self.colour[1]/2,self.colour[2]/2), pg.Rect(self.posx-8, self.posy-32, 128, 64))

        offset = (4 - len(self.text))*" "
        
        printtoscreen(screen, self.posx-16, self.posy, offset+self.text, self.font, self.colour)
        self.timer += 1
        if self.timer > self.time:
            world.delete_entity(id)

class BattleHandler:
    def __init__(self, players, enemies, sharedPlayerStats, background):
        self.players = players
        self.enemies = enemies
        self.sharedPlayerStats = sharedPlayerStats
        self.active = False
        self.background = background
        self.font = pg.font.SysFont("Courier", 24)
        self.smallfont = pg.font.SysFont("Courier", 16)
        self.buttonDrawer = act.ButtonDrawer(["arrow_down", "arrow_left", "arrow_right", "arrow_up", "bright_circle", "button_?", "button_c", "button_x", "button_z", "dark_circle", "red_circle"])
    def Activate(self):
        self.turn = "players"
        self.subturn = 0
        self.timing = 0
        self.actionDict = {}
        self.currentIndex = "Start"
        self.active = True
        self.populateActions()
    def populateActions(self):
        current = self.players[self.subturn]

        self.actionDict["Start"] = MenuOptionsAction(["Fight", "Spell", "Run"], ["Fight", "Spell", "Run"], "Start")
        
        self.actionDict["Fight"] = DescriptionConfirmAction(["Fight", "Normal attack.", "Press Z when the circle lights up!"], "FightTarget", "Start")
        self.actionDict["FightTarget"] = MenuOptionsAction([enemy.name for enemy in self.enemies], [f"FightAction{i}" for i in range(len(self.enemies))], "Fight")
        for i in range(len(self.enemies)):
            self.actionDict[f"FightAction{i}"] = PerformAction(Spell("Fight", ["Fight", "Normal attack.", "Press Z when the last circle lights up!"], "1enemy", act.pressButtonCommand(["z"], 48, 3, True, False), [DamageEffect(1, "physAtk", "physDef")]), i, self.enemies, current)

        self.actionDict["Spell"] = MenuOptionsAction([spell.name for spell in current.spells], [f"SpellDescription{i}" for i in range(len(current.spells))], "Start")

        for i in range(len(current.spells)):
            self.actionDict[f"SpellDescription{i}"] = DescriptionConfirmAction(current.spells[i].description, f"SpellTarget{i}", "Spell")
            if current.spells[i].targeting == "1enemy":
                possibleTargets = self.enemies
                self.actionDict[f"SpellTarget{i}"] = MenuOptionsAction([enemy.name for enemy in self.enemies], [f"Spell{i}|{ind}" for ind in range(len(possibleTargets))], f"SpellDescription{i}")
                for ind in range(len(possibleTargets)):
                    self.actionDict[f"Spell{i}|{ind}"] = PerformAction(current.spells[i], ind, possibleTargets, current)
            elif current.spells[i].targeting == "1ally":
                possibleTargets = self.players
                self.actionDict[f"SpellTarget{i}"] = MenuOptionsAction([player.name for player in self.players], [f"Spell{i}|{ind}" for ind in range(len(possibleTargets))], f"SpellDescription{i}")
                for ind in range(len(possibleTargets)):
                    self.actionDict[f"Spell{i}|{ind}"] = PerformAction(current.spells[i], ind, possibleTargets, current)
            elif current.spells[i].targeting == "self":
                possibleTargets = [current]
                self.actionDict[f"SpellTarget{i}"] = MenuOptionsAction([current], [f"Spell{i}|0" for ind in range(len(possibleTargets))], f"SpellDescription{i}")
                self.actionDict[f"Spell{i}|0"] = PerformAction(current.spells[i], 0, possibleTargets, current)
            elif current.spells[i].targeting == "allallies":
                possibleTargets = self.players
                self.actionDict[f"SpellTarget{i}"] = MenuOptionsAction(["All Characters"], [f"Spell{i}|0" for ind in range(len(possibleTargets))], f"SpellDescription{i}")  
                self.actionDict[f"Spell{i}|0"] = PerformAction(current.spells[i], 0, possibleTargets, current)
            elif current.spells[i].targeting == "allenemies":
                possibleTargets = self.enemies
                self.actionDict[f"SpellTarget{i}"] = MenuOptionsAction(["All Enemies"], [f"Spell{i}|0" for ind in range(len(possibleTargets))], f"SpellDescription{i}")
                self.actionDict[f"Spell{i}|0"] = PerformAction(current.spells[i], 0, possibleTargets, current)
            

        self.actionDict["Run"] = RunAwayAction()
        
        self.currentIndex = "Start"

    def draw(self, screen):
        bgrect = self.background.get_rect()
        bgrect.center = 320, 240
        screen.blit(self.background, bgrect)

        for i, enemy in enumerate(self.enemies):
            enemyrect = enemy.sprite.get_rect()
            enemyrect.center = 320 - (len(self.enemies)-1)*0.5*160 + i*160, 200
            screen.blit(enemy.sprite, enemyrect)
        
    def drawUI(self, screen):
        for i, player in enumerate(self.players):
            if self.turn == "players":
                #Highlight current turn
                pg.draw.rect(screen, ((50,150,255) if i == self.subturn else (0,0,200)), pg.Rect(40+i*200, 10, 200, 40))
            elif self.turn == "enemies":
                #Highlight the enemy target
                pg.draw.rect(screen, ((50,150,255) if (self.timing > 0 and ((i == self.currentEnemyAction.targetInd and self.enemies[self.subturn].spells[self.currentEnemyAction.actionInd].targeting == "1enemy") or self.enemies[self.subturn].spells[self.currentEnemyAction.actionInd].targeting == "allenemies")) else (0,0,200)), pg.Rect(40+i*200, 10, 200, 40))
            pg.draw.rect(screen, (255,255,255), pg.Rect(40+i*200, 10, 200, 40), 4)
            name = player.name
            hp = f"{player.hp}/{player.stats['maxHP']}"
            spaces = (13 - (len(name)+len(hp)))*" "
            printtoscreen(screen, 48+i*200, 28, f"{name}{spaces}{hp}", self.font, (255,255,255))
        pg.draw.rect(screen, (0,0,0), pg.Rect(10, 10, 20, 200))
        height = 200 * self.sharedPlayerStats.tp / self.sharedPlayerStats.tpMax
        pg.draw.rect(screen, (0,150,50), pg.Rect(10, 10+200-height, 20, height+1))
        printtoscreen(screen, 10, 220, "TP", self.smallfont, (255,255,255))
        printtoscreen(screen, 10, 240, f"{self.sharedPlayerStats.tp:2}", self.smallfont, (255,255,255))
        printtoscreen(screen, 10, 260, " /", self.smallfont, (255,255,255))
        printtoscreen(screen, 10, 280, f"{self.sharedPlayerStats.tpMax:2}", self.smallfont, (255,255,255))
        
    
    def Update(self, screen, inputs, world):

        self.draw(screen)
        # UPDATE UI
        self.drawUI(screen)

        # Draw temporary text
        for i, entity in world.get_component(TemporaryText):
            entity.Update(screen, world, i)
        
        # if player turn
        if self.turn == "players":

            if self.players[self.subturn].hp < 1:
                result = -2
            else:
                # run current BattleAction
                result = self.actionDict[self.currentIndex].Update(screen, world, inputs)

            
            
            
            if result == -3:
                #Battle's done, everyone can go home now
                return -3
            elif result == -2:
                #Next party member!
                self.subturn += 1
                
                if self.subturn >= len(self.players):
                    self.turn = "enemies"
                    self.subturn = 0
                    self.timing = 0
                    return -1
                else:
                    self.populateActions()
            elif result == -1:
                # carry on as usual
                return -1
            else:
                self.currentIndex = result
                self.actionDict[self.currentIndex].Activate()
                return -1
        elif self.turn == "enemies":
            if self.enemies[self.subturn].hp < 1:
                self.subturn += 1
                self.timing = -1
            else:     
                if self.timing == 0:
                    self.currentEnemyAction = self.enemies[self.subturn].enemyAI.decide(self.enemies[self.subturn].spells, self.enemies, self.players)
                    self.enemies[self.subturn].spells[self.currentEnemyAction.actionInd].Activate()
                elif self.timing < 30:
                    margin = 24
                    pg.draw.rect(screen, (0,0,200), pg.Rect(140, 320, 500, 160))
                    pg.draw.rect(screen, (255,255,255), pg.Rect(140, 320, 500, 160),4)
                    if self.enemies[self.subturn].spells[self.currentEnemyAction.actionInd].name != "Attack":
                        printtoscreen(screen, 140+margin, 320+margin, f"{self.enemies[self.subturn].name} used {self.enemies[self.subturn].spells[self.currentEnemyAction.actionInd].name}!", self.font, (255,255,255))
                    else:
                        printtoscreen(screen, 140+margin, 320+margin, f"{self.enemies[self.subturn].name} attacks!", self.font, (255,255,255))
                elif self.timing >= 30:
                    result = self.enemies[self.subturn].spells[self.currentEnemyAction.actionInd].EnemyAction(True, self.enemies, self.players, self.currentEnemyAction.targetInd, self.currentEnemyAction.potentialTargets, self.enemies[self.subturn], inputs, screen, world, self.buttonDrawer)
                    if result != -1:
                        self.subturn += 1
                        self.timing = -1
            self.timing += 1
            if self.subturn >= len(self.enemies):
                self.turn = "players"
                self.subturn = 0
                self.timing = 0
                self.actionDict = {}
                self.currentIndex = "Start"
                self.populateActions()
                
                

class EnemyAction:
    """Holder for an enemy's action."""
    def __init__(self, actionInd, targetInd, potentialTargets):
        self.actionInd = actionInd
        self.targetInd = targetInd
        self.potentialTargets = potentialTargets

class BattleAction:
    """Base class for UI and Actions."""
    def __init__(self, next, previous):
        self.next = next
        self.previous = previous
    def Update(self, screen, world, inputs):
        return self.next

class MenuOptionsAction:
    def __init__(self, optionList, nextList, previous):
        self.optionList = optionList
        self.nextList = nextList
        self.previous = previous
        self.selected = 0
        self.font = pg.font.SysFont("Courier", 20)
        self.holdingConfirm = True
        self.holdingBack = True
        self.holdingSelect = True
        self.waitingComplete = False
    def Activate(self):
        self.holdingConfirm = True
        self.holdingBack = True
        self.holdingSelect = True
        self.waitingComplete = False
        self.selected = 0
    def Update(self, screen, world, inputs):
        margin = 24
        pg.draw.rect(screen, (0,0,200), pg.Rect(140, 320, 500, 160))
        pg.draw.rect(screen, (255,255,255), pg.Rect(140, 320, 500, 160),4)
        for i, option in enumerate(self.optionList):
            printtoscreen(screen, (i%3)*160+140+margin, (i//3)*20+320+margin, option, self.font, (255,255,255))
        pg.draw.circle(screen, (255,255,255), ((self.selected%3)*160+140+margin-12, (self.selected//3)*20+320+margin), 8)
        if not(self.holdingSelect):
            if inputs["left"]:
                self.selected = (self.selected-1)%len(self.optionList)
                self.holdingSelect = True
            elif inputs["right"]:
                self.selected = (self.selected+1)%len(self.optionList)
                self.holdingSelect = True
                
        else:
            if not(any([inputs["left"], inputs["right"]])):
                self.holdingSelect = False


        if not(inputs["confirm"]) and self.waitingComplete:
            return self.nextList[self.selected]

        if not(self.holdingBack):
            if inputs["cancel"]:
                return self.previous
        else:
            if not(inputs["cancel"]):
                self.holdingBack = False
            
        
        if not(self.holdingConfirm):
            if inputs["confirm"]:
                self.waitingComplete = True
            return -1
            
        else:
            if not(inputs["confirm"]):
                self.holdingConfirm = False
            return -1
class DescriptionConfirmAction:
    def __init__(self, description, next, previous):
        self.description = description
        self.next = next
        self.previous = previous
        self.font = pg.font.SysFont("Courier", 20)
        self.holdingConfirm = True
        self.holdingBack = True
        self.waitingComplete = False
    def Activate(self):
        self.holdingConfirm = True
        self.holdingBack = True
        self.waitingComplete = False
    def Update(self, screen, world, inputs):
        margin = 24
        pg.draw.rect(screen, (0,0,200), pg.Rect(140, 320, 500, 160))
        pg.draw.rect(screen, (255,255,255), pg.Rect(140, 320, 500, 160),4)
        for i, option in enumerate(self.description):
            printtoscreen(screen, 140+margin, i*20+320+margin, option, self.font, (255,255,255))
        if not(inputs["confirm"]) and self.waitingComplete:
            return self.next
        
        if not(self.holdingBack):
            if inputs["cancel"]:
                return self.previous
        else:
            if not(inputs["cancel"]):
                self.holdingBack = False
        
        if not(self.holdingConfirm):
            if inputs["confirm"]:
                self.waitingComplete = True
            return -1
            
        else:
            if not(inputs["confirm"]):
                self.holdingConfirm = False
            return -1
class PerformAction:
    def __init__(self, actionObject, targetInd, potentialTargets, user):
        self.actionObject = actionObject
        self.targetInd = targetInd
        self.potentialTargets = potentialTargets
        self.user = user
        self.buttonDrawer = act.ButtonDrawer(["arrow_down", "arrow_left", "arrow_right", "arrow_up", "bright_circle", "button_?", "button_c", "button_x", "button_z", "dark_circle", "red_circle"])
    def Activate(self):
        self.actionObject.Activate()
    def Update(self, screen, world, inputs):
        # DO STUFF
        players = []
        enemies = []
        for i, battleHandler in world.get_component(BattleHandler):
            if battleHandler.active:
                players = battleHandler.players
                enemies = battleHandler.enemies
        
        result = self.actionObject.PerformAction(True, players, enemies, self.targetInd, self.potentialTargets, self.user, inputs, screen, world, self.buttonDrawer)
        if result == -1:
            return -1
        else:
            return -2
class RunAwayAction:
    def __init__(self):
        pass
    def Activate(self):
        pass
    def Update(self, screen, world, inputs):
        return -3


class BattleProcessor(esper.Processor):
    def process(self):
        inputs = self.world.get_component(mapScreen.Input)[0][1].buttons
        screen = self.world.get_component(mapScreen.Consts)[0][1].screen
        for i, battleHandler in self.world.get_component(BattleHandler):
            if battleHandler.active:
                battleHandler.Update(screen, inputs, self.world)




guardCommands = {
    "normalGuard":act.pressButtonCommand(["z"], 30, 3, True, False),
    "sequenceGuard":act.buttonSequenceCommand(["up", "down", "left", "right"], 3, 60, True)
}
enemyAttacks = {
    "enemyAttack":Spell("Attack", ["Normal Attack"], "1enemy", guardCommands["normalGuard"], [DamageEffect(1, "physAtk", "physDef")]),
    "boneSpray":Spell("Bone Spray", ["Shoots bones"], "allenemies", guardCommands["sequenceGuard"], [DamageEffect(1, "magiAtk", "magiDef")])
}
actionCommandList = {
    "Triple Hit":act.MultipleActionCommands([act.pressButtonCommand(["z", "x", "c"], 30, 3, True, True),act.pressButtonCommand(["z", "x", "c"], 20, 4, True, True),act.pressButtonCommand(["z", "x", "c"], 12, 5, True, True)], 20)
}
spellList = {
    "Triple Hit":Spell("Triple Hit", ["Triple Hit", "Hits three times", "Press the shown buttons in time!"], "1enemy", actionCommandList["Triple Hit"], [DamageEffect(1, "physAtk", "physDef") for i in range(3)])  
}