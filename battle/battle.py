import pygame as pg
import esper
import random
import time
from typing import Dict, List
import stats.playerStats as pStats
import battle.actionCommands as act
import mapScreen.mapScreen as mapScreen
import math
import copy

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
    return max(1, int((attack**2 * baseDamage*random.randint(95,105)/100) / (attack + defense)))


class StatModifier:
    def __init__(self, name, amount):
        self.name = name
        self.amount = amount
class BattleEntity:
    def __init__(self, name, stats, hp, spells):
        self.name = name
        self.baseStats = stats
        self.stats = dict()
        self.hp = hp
        self.spells = spells
        self.statusEffects = []
        self.statModifiers = {"maxHP":[],"physAtk":[],"physDef":[],"magiAtk":[],"magiDef":[]}
    def updateStats(self):
        self.statModifiers = {"maxHP":[],"physAtk":[],"physDef":[],"magiAtk":[],"magiDef":[]}
        for effect in self.statusEffects:
            if effect.type == "StatChange":
                for statModifier, affectedStat in effect.modifiers:
                    self.statModifiers[affectedStat].append(statModifier)
        for stat in self.statModifiers.keys():
            cumulative = 1
            for mod in self.statModifiers[stat]:
                cumulative += mod.amount
            self.stats[stat] = int((self.baseStats[stat] * cumulative))
    def fromCharacter(self, character):
        name = character.name
        stats = character.totalStats
        hp = character.hp
        self.character = character
        spells = [spellList[i] for i in character.spellNames[:4]]
        self.__init__(name, stats, hp, spells)
        self.updateStats()
        return self
    def updateCharacter(self, character):
        character.hp = self.hp
class BattleEnemy(BattleEntity):
    def __init__(self, name, stats, hp, spells, sprite, enemyAI):
        self.name = name
        self.baseStats = stats
        self.stats = stats
        self.statusEffects = []
        self.statModifiers = {"maxHP":[],"physAtk":[],"physDef":[],"magiAtk":[],"magiDef":[]}
        self.hp = hp
        self.spells = spells
        self.sprite = sprite
        self.enemyAI = enemyAI
        self.id = 0

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
            crit = random.randint(0, 99) < 12
            damage = int(damageCalc(attacking, defending, self.amount) * (2 if crit else 1))
            if player:
                ind = enemies.index(target)
                world.create_entity(TemporaryText(str(damage), (255*random.randint(7,10)/10,0,0), 30, 320 - (len(enemies)-1)*0.5*160+random.randint(-32, 32) + ind*160 - 64+random.randint(-32, 32), 200))
                if crit:
                    world.create_entity(TemporaryText("CRIT", (100,0,150), 30, 320 - (len(enemies)-1)*0.5*160+random.randint(-32, 32) + ind*160 - 64+random.randint(-32, 32), 160))
            else:
                ind = enemies.index(target)
                world.create_entity(TemporaryText(str(damage), (255*random.randint(7,10)/10,0,0), 30, 48+ind*200+64, 80))
                if crit:
                    world.create_entity(TemporaryText("CRIT", (100,0,150), 30, 48+ind*200+64, 160))
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
                else:
                    ind = players.index(target)
                    world.create_entity(TemporaryText(str(healing), (0,255,0), 30, 320 - (len(enemies)-1)*0.5*160+random.randint(-32, 32) + ind*160 - 64+random.randint(-32, 32), 200))
                target.hp += healing
                if target.hp > target.stats["maxHP"]:
                    target.hp = target.stats["maxHP"]
class ReviveEffect(SpellEffect):
    """Revive a party member on 20% hp."""
    def __init__(self):
        pass
    def activateEffect(self, user, player, targets, players, enemies, actionCommandResult, world):
        for i, target in enumerate(targets):
            if target.hp < 1:
                target.hp = min(1, target.stats["maxHP"]//5)
class MultiVampireEffect(SpellEffect):
    """Deal damage, then heal all allies based on damage and scale factor."""
    def __init__(self, amount, factor, offensive, defensive):
        self.amount = amount
        self.factor = factor
        self.offensive = offensive
        self.defensive = defensive
    def activateEffect(self, user, player, targets, players, enemies, actionCommandResult, world):
        attacking = user.stats[self.offensive] * actionCommandResult
        for i, target in enumerate(targets):
            defending = target.stats[self.defensive]
            crit = random.randint(0, 99) < 12
            damage = int(damageCalc(attacking, defending, self.amount) * (2 if crit else 1))
            if player:
                ind = enemies.index(target)
                world.create_entity(TemporaryText(str(damage), (255*random.randint(7,10)/10,0,0), 30, 320 - (len(enemies)-1)*0.5*160+random.randint(-32, 32) + ind*160 - 64+random.randint(-32, 32), 200))
                if crit:
                    world.create_entity(TemporaryText("CRIT", (100,0,150), 30, 320 - (len(enemies)-1)*0.5*160+random.randint(-32, 32) + ind*160 - 64+random.randint(-32, 32), 160))
            else:
                ind = enemies.index(target)
                world.create_entity(TemporaryText(str(damage), (255*random.randint(7,10)/10,0,0), 30, 48+ind*200+64, 80))
                if crit:
                    world.create_entity(TemporaryText("CRIT", (100,0,150), 30, 48+ind*200+64, 160))
                #print(f"{damage} damage to {target.name}!")
            target.hp -= damage
            if target.hp < 0:
                target.hp = 0
        for i, target in enumerate(players):
            if target.hp > 0:
                healing = int(self.factor * damage)
                if player:
                    ind = players.index(target)
                    world.create_entity(TemporaryText(str(healing), (0,255,0), 30, 48+ind*200+64, 80))
                else:
                    ind = players.index(target)
                    world.create_entity(TemporaryText(str(healing), (0,255,0), 30, 320 - (len(enemies)-1)*0.5*160+random.randint(-32, 32) + ind*160 - 64+random.randint(-32, 32), 200))
                target.hp += healing
                if target.hp > target.stats["maxHP"]:
                    target.hp = target.stats["maxHP"]
class DoTEffect(SpellEffect):
    """Inflict damage over time effect on entity"""
    def __init__(self, amount, offensive, name, turns, icon):
        self.amount = amount
        self.offensive = offensive
        self.name = name
        self.turns = turns
        self.icon = icon
    def activateEffect(self, user, player, targets, players, enemies, actionCommandResult, world):
        attacking = int(user.stats[self.offensive] * actionCommandResult * self.amount)
        for i, target in enumerate(targets):
            if self.name not in [x.name for x in target.statusEffects]:
                target.statusEffects.append(DoTStatusEffect(self.name, self.turns, attacking, self.icon))
            else:
                for j, statusEffect in enumerate(target.statusEffects):
                    if statusEffect.name == self.name:
                        target.statusEffects[j] = DoTStatusEffect(self.name, self.turns, attacking, self.icon)
class HoTEffect(SpellEffect):
    """Inflict regen over time effect on entity"""
    def __init__(self, amount, offensive, name, turns, icon):
        self.amount = amount
        self.offensive = offensive
        self.name = name
        self.turns = turns
        self.icon = icon
    def activateEffect(self, user, player, targets, players, enemies, actionCommandResult, world):
        attacking = int(user.stats[self.offensive] * actionCommandResult * self.amount)
        for i, target in enumerate(targets):
            if self.name not in [x.name for x in target.statusEffects]:
                target.statusEffects.append(HoTStatusEffect(self.name, self.turns, attacking, self.icon))
            else:
                for j, statusEffect in enumerate(target.statusEffects):
                    if statusEffect.name == self.name:
                        target.statusEffects[j] = HoTStatusEffect(self.name, self.turns, attacking, self.icon)
class ActivateEffects(SpellEffect):
    """Activate persistent effects, and don't reduce their duration."""
    def __init__(self):
        pass
    def activateEffect(self, user, player, targets, players, enemies, actionCommandResult, world):
        for i, target in enumerate(targets):
            for j, statusEffect in enumerate(target.statusEffects):
                statusEffect.activate(not(player), i, (len(enemies) if player else len(players)), target, world)

class StatChangeFixedEffect(SpellEffect):
    """Inflict a stat buff/debuff of fixed strength on entity for a certain amount of turns."""
    def __init__(self, stats, amount, name, turns, icon):
        self.stats = stats
        self.amount = amount
        self.name = name
        self.turns = turns
        self.icon = icon
    def activateEffect(self, user, player, targets, players, enemies, actionCommandResult, world):
        for i, target in enumerate(targets):
            if self.name not in [x.name for x in target.statusEffects]:
                target.statusEffects.append(StatChangeStatusEffect(self.name, self.turns, 
                                                                   [(StatModifier(self.name, self.amount), stat) for stat in self.stats],
                                                                   self.icon))
            else:
                for i, statusEffect in enumerate(target.statusEffects):
                    if statusEffect.name == self.name:
                        target.statusEffects[i] = StatChangeStatusEffect(self.name, self.turns, 
                                                                   [(StatModifier(self.name, self.amount), stat) for stat in self.stats],
                                                                   self.icon)
class StatChangeScalingEffect(SpellEffect):
    """Inflict a stat buff/debuff of scaling strength on entity for a certain amount of turns."""
    def __init__(self, scaling, stats, amount, name, turns, icon):
        self.scaling = scaling
        self.stats = stats
        self.amount = amount
        self.name = name
        self.turns = turns
        self.icon = icon
    def activateEffect(self, user, player, targets, players, enemies, actionCommandResult, world):
        total = math.log(user.stats[self.scaling], 2) * self.amount * actionCommandResult
        print(total)
        for i, target in enumerate(targets):
            if self.name not in [x.name for x in target.statusEffects]:
                target.statusEffects.append(StatChangeStatusEffect(self.name, self.turns, 
                                                                   [(StatModifier(self.name, total), stat) for stat in self.stats],
                                                                   self.icon))
            else:
                for i, statusEffect in enumerate(target.statusEffects):
                    if statusEffect.name == self.name:
                        target.statusEffects[i] = StatChangeStatusEffect(self.name, self.turns, 
                                                                   [(StatModifier(self.name, total), stat) for stat in self.stats],
                                                                   self.icon)
class StatScalingStackingEffect(SpellEffect):
    """Inflict a stat buff/debuff of scaling strength on entity for a certain amount of turns that stacks."""
    def __init__(self, scaling, stats, amount, name, turns, icon):
        self.scaling = scaling
        self.stats = stats
        self.amount = amount
        self.name = name
        self.turns = turns
        self.icon = icon
    def activateEffect(self, user, player, targets, players, enemies, actionCommandResult, world):
        total = math.log(user.stats[self.scaling], 2) * self.amount * actionCommandResult
        print(total)
        for i, target in enumerate(targets):
                target.statusEffects.append(StatChangeStatusEffect(self.name, self.turns, 
                                                                   [(StatModifier(self.name+str(time.time())+str(random.random()), total), stat) for stat in self.stats],
                                                                   self.icon))



class StatusEffectDrawer(Dict):
    def __init__(self, filenames):
        for filename in filenames:
            self[filename] = pg.image.load(f"assets/art/ui/statusIcons/{filename}.png").convert_alpha()
    def draw(self, screen, name, posx, posy):
        rect = self[name].get_rect()
        rect.center = posx, posy
        screen.blit(self[name], rect)


class StatusEffect:
    """Base class"""
    def __init__(self, name, type, turns, endOfTurn, icon):
        self.name = name
        self.type = type
        self.endOfTurn = endOfTurn
        self.turns = turns
        self.icon = icon
    def activate(self, player, posInd, targetAmount, afflicted, world):
        pass
class DoTStatusEffect:
    """Deals damage at the end of afflicted's turn."""
    def __init__(self, name, turns, damage, icon):
        self.name = name
        self.type = "DoT"
        self.endOfTurn = True
        self.damage = damage
        self.turns = turns
        self.icon = icon
    def activate(self, player, posInd, targetAmount, afflicted, world):
        afflicted.hp -= self.damage
        if player:
            world.create_entity(TemporaryText(str(self.damage), (100,0,100), 30, 48+posInd*200+64, 80))
        else:
            world.create_entity(TemporaryText(str(self.damage), (100,0,100), 30, 320 - (targetAmount-1)*0.5*160+random.randint(-32, 32) + posInd*160 - 64+random.randint(-32, 32), 200))
        if afflicted.hp < 0:
            afflicted.hp = 0
class HoTStatusEffect:
    """Heals damage at the end of afflicted's turn."""
    def __init__(self, name, turns, healing, icon):
        self.name = name
        self.type = "HoT"
        self.endOfTurn = True
        self.healing = healing
        self.turns = turns
        self.icon = icon
    def activate(self, player, posInd, targetAmount, afflicted, world):
        afflicted.hp += self.healing
        if player:
            world.create_entity(TemporaryText(str(self.healing), (0,176,100), 30, 48+posInd*200+64, 80))
        else:
            world.create_entity(TemporaryText(str(self.healing), (0,176,100), 30, 320 - (targetAmount-1)*0.5*160+random.randint(-32, 32) + posInd*160 - 64+random.randint(-32, 32), 200))
        if afflicted.hp > afflicted.stats["maxHP"]:
            afflicted.hp = afflicted.stats["maxHP"]
class StatChangeStatusEffect:
    """Changes stats based on modifiers, for as long as it lasts. Stats get recalculated after every action."""
    def __init__(self, name, turns, modifiers, icon):
        self.name = name
        self.type = "StatChange"
        self.turns = turns
        self.modifiers = modifiers
        self.endOfTurn = False
        self.icon = icon

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

class VictoryHandler:
    def __init__(self, allCharacters, sharedStats, xp, gold):
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
        spellsPerClass = {
            "art":["Art Skill L1", "Art Skill L4", "Art Skill L7", "Art Skill L10", "Revive", "Art Skill L16", "Art Skill L19"],
            "science":["Science Skill L1", "Science Skill L4", "Science Skill L7", "Science Skill L10", "Science Skill L13", "Science Skill L16", "Science Skill L19"],
            "math":["Math Skill L1", "Math Skill L4", "Math Skill L7", "Math Skill L10", "Math Skill L13", "Math Skill L16", "Math Skill L19"],
            "psychology":["Psychology Skill L1", "Psychology Skill L4", "Psychology Skill L7", "Psychology Skill L10", "Psychology Skill L13", "Psychology Skill L16", "Psychology Skill L19"],
            "history":["History Skill L1", "History Skill L4", "History Skill L7", "Revive", "History Skill L13", "History Skill L16", "History Skill L19"],
            "english":["English Skill L1", "English Skill L4", "English Skill L7", "Triple Hit", "Revive", "English Skill L16", "English Skill L19"],
            "languages":["Languages Skill L1", "Languages Skill L4", "Languages Skill L7", "Languages Skill L10", "Languages Skill L13", "Languages Skill L16", "Languages Skill L19"],
        }
        
        self.allCharacters = allCharacters
        self.currPlayers = allCharacters[:3]
        self.xp = xp
        self.gold = gold
        self.counter = 0
        
        
        
        
        
        self.menuList = []
        self.menuList.append(DescriptionConfirmAction(["Victory!", f"Gained {xp} experience points", f"and {gold} gold."], 1, -1))

        sharedStats.xp += xp
        while sharedStats.xp > xpPerLevelUp[self.allCharacters[0].character.baseStats.level]:
            sharedStats.xp -= xpPerLevelUp[self.allCharacters[0].character.baseStats.level]
            for battleCharacter in self.allCharacters:
                character = battleCharacter.character
                oldBase = copy.deepcopy(character.baseStats.finalStats)
                character.baseStats.setLevel(character.baseStats.level + 1)
                self.menuList.append(DescriptionConfirmAction([f"{character.name} grew to level {character.baseStats.level}!"] + [f"{statName.upper():8}: {oldBase[statName]:6} + {(character.baseStats.finalStats[statName] - oldBase[statName]):3} = {character.baseStats.finalStats[statName]:5}" for statName in ["maxHP", "physAtk", "physDef", "magiAtk", "magiDef"]],1, -1))
                if character.baseStats.level in [1, 4, 7, 10, 13, 16, 19]:
                    character.spellNames.append(spellsPerClass[character.playerClass.lower()][int((character.baseStats.level - 1)//3)])
                    self.menuList.append(DescriptionConfirmAction([f"{character.name} learned {spellsPerClass[character.playerClass.lower()][int((character.baseStats.level - 1)//3)]}!", ("Equip it in the Menu" if len(character.spellNames) > 4 else "Automatically Equipped")],1, -1))
        
    def Update(self, screen, world, inputs):
        if self.counter >= len(self.menuList):
            return 1
        else:
            result = self.menuList[self.counter].Update(screen, inputs, world)
            if result == 1:
                self.counter += 1
            return -1

        

class BattleHandler:
    def __init__(self, players, enemies, sharedPlayerStats, background, xp, gold):
        self.allCharacters = players
        self.players = players[:3]
        self.enemies = enemies
        self.initialEnemies = enemies
        self.sharedPlayerStats = sharedPlayerStats
        self.active = False
        self.victoryHandler = None
        self.progress = "fighting"
        self.xp = xp
        self.gold = gold
        self.background = background
        self.font = pg.font.SysFont("Courier", 24)
        self.smallfont = pg.font.SysFont("Courier", 16)
        self.buttonDrawer = act.ButtonDrawer(["arrow_down", "arrow_left", "arrow_right", "arrow_up", "bright_circle", "button_?", "button_c", "button_x", "button_z", "dark_circle", "red_circle"])
        self.statusEffectDrawer = StatusEffectDrawer(["absorb", "buffBothDef", "buffCritRate", "buffMagiAtk", "buffMagiDef", "buffPhysAtk", "buffPhysDef", "counterMagic", "counterPhys", "debuffBothDef", "debuffMagiAtk", "debuffMagiDef", "debuffPhysAtk", "debuffPhysDef", "poisonStrong", "poisonWeak", "protectCrit", "regen", "sleep", "taunt"])
    def Activate(self):
        self.turn = "players"
        self.subturn = 0
        self.timing = 0
        self.actionDict = {}
        self.currentIndex = "Start"
        self.active = True
        self.initialEnemyCount = len(self.enemies)
        for i, enemy in enumerate(self.enemies):
            enemy.id = i
        self.populateActions()
    def populateActions(self):
        current = self.players[self.subturn]

        if len(current.spells) > 0:
            self.actionDict["Start"] = MenuOptionsAction(["Fight", "Spell", "Run"], ["Fight", "Spell", "Run"], "Start")
        else:
            self.actionDict["Start"] = MenuOptionsAction(["Fight", "Run"], ["Fight", "Run"], "Start")
        
        self.actionDict["Fight"] = DescriptionConfirmAction(["Fight", "Normal attack.", "Press Z when the circle lights up!"], "FightTarget", "Start")
        self.actionDict["FightTarget"] = MenuOptionsAction([enemy.name for enemy in self.enemies if enemy.hp > 0], [f"FightAction{i}" for i in range(len(self.enemies))], "Fight")
        for i in range(len(self.enemies)):
            self.actionDict[f"FightAction{i}"] = PerformAction(Spell("Fight", ["Fight", "Normal attack.", "Press Z when the last circle lights up!"], "1enemy", act.pressButtonCommand(["z"], 48, 3, True, False), [DamageEffect(1, "physAtk", "physDef")]), i, self.enemies, current)

        if len(current.spells) > 0:
            self.actionDict["Spell"] = MenuOptionsAction([spell.name for spell in current.spells], [f"SpellDescription{i}" for i in range(len(current.spells))], "Start")

        for i in range(len(current.spells)):
            self.actionDict[f"SpellDescription{i}"] = DescriptionConfirmAction(current.spells[i].description, f"SpellTarget{i}", "Spell")
            if current.spells[i].targeting == "1enemy":
                possibleTargets = self.enemies
                self.actionDict[f"SpellTarget{i}"] = MenuOptionsAction([enemy.name for enemy in self.enemies if enemy.hp > 0], [f"Spell{i}|{ind}" for ind in range(len(possibleTargets))], f"SpellDescription{i}")
                for ind in range(len(possibleTargets)):
                    self.actionDict[f"Spell{i}|{ind}"] = PerformAction(current.spells[i], ind, possibleTargets, current)
            elif current.spells[i].targeting == "1ally":
                possibleTargets = self.players
                self.actionDict[f"SpellTarget{i}"] = MenuOptionsAction([player.name for player in self.players], [f"Spell{i}|{ind}" for ind in range(len(possibleTargets))], f"SpellDescription{i}")
                for ind in range(len(possibleTargets)):
                    self.actionDict[f"Spell{i}|{ind}"] = PerformAction(current.spells[i], ind, possibleTargets, current)
            elif current.spells[i].targeting == "self":
                possibleTargets = [current]
                self.actionDict[f"SpellTarget{i}"] = MenuOptionsAction(["Self"], [f"Spell{i}|0" for ind in range(len(possibleTargets))], f"SpellDescription{i}")
                self.actionDict[f"Spell{i}|0"] = PerformAction(current.spells[i], 0, possibleTargets, current)
            elif current.spells[i].targeting == "allallies":
                possibleTargets = self.players
                self.actionDict[f"SpellTarget{i}"] = MenuOptionsAction(["All Characters"], [f"Spell{i}|0" for ind in range(len(possibleTargets))], f"SpellDescription{i}")  
                self.actionDict[f"Spell{i}|0"] = PerformAction(current.spells[i], 0, possibleTargets, current)
            elif current.spells[i].targeting == "allenemies":
                possibleTargets = [enemy for enemy in self.enemies if enemy.hp > 0]
                self.actionDict[f"SpellTarget{i}"] = MenuOptionsAction(["All Enemies"], [f"Spell{i}|0" for ind in range(len(possibleTargets))], f"SpellDescription{i}")
                self.actionDict[f"Spell{i}|0"] = PerformAction(current.spells[i], 0, possibleTargets, current)
            

        self.actionDict["Run"] = RunAwayAction()
        
        self.currentIndex = "Start"

    def draw(self, screen):
        bgrect = self.background.get_rect()
        bgrect.center = 320, 240
        screen.blit(self.background, bgrect)

        for i, enemy in enumerate(self.enemies):
            if enemy.hp > 0:
                enemyrect = enemy.sprite.get_rect()
                enemyrect.center = 320 - (self.initialEnemyCount-1)*0.5*160 + enemy.id*160, 200
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

        # Draw Status Effect Icons
        for i, player in enumerate(self.players):
            for j, statusEffect in enumerate(player.statusEffects):
                self.statusEffectDrawer.draw(screen, statusEffect.icon, 72+i*200+(j%3)*64, 84+(j//3)*64)
                printtoscreen(screen,72+i*200+(j%3)*64,84+(j//3)*64,str(statusEffect.turns),self.smallfont,(255,255,255))
        for i, enemy in enumerate(self.enemies):
            for j, statusEffect in enumerate(enemy.statusEffects):
                self.statusEffectDrawer.draw(screen, statusEffect.icon, 256-(self.initialEnemyCount-1)*0.5*160+enemy.id*160+(j%3)*64, 292+(j//3)*64)
                printtoscreen(screen,256-(self.initialEnemyCount-1)*0.5*160+enemy.id*160+(j%3)*64, 292+(j//3)*64,str(statusEffect.turns),self.smallfont,(255,255,255))
        
    
    def Update(self, screen, inputs, world):
        self.draw(screen)
        # Check if battle has finished
        if self.progress == "fighting":
            if len(self.enemies) < 1:
                self.progress = "victory"
                self.victoryHandler = VictoryHandler(self.allCharacters, self.sharedPlayerStats, self.xp, self.gold)
            elif not(any([p for p in self.players if p.hp > 0])):
                self.progress = "defeat"
        
        # If battle has finished, run either the game over or the victory handler with the given statistics.
        if self.progress == "victory":
            result = self.victoryHandler.Update(screen, inputs, world)
            if result == 1:
                return -3
            else:
                return -1
        
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
                self.enemies = [enemy for enemy in self.enemies if enemy.hp > 0]
            
            
            
            if result == -3:
                # Run away
                return -3
            elif result == -2:
                # Activate end-of-my-turn status effects
                for effect in self.players[self.subturn].statusEffects:
                    if effect.endOfTurn:
                        effect.activate(True, self.subturn, len(self.players), self.players[self.subturn], world)
                    effect.turns -= 1
                self.players[self.subturn].statusEffects = [i for i in self.players[self.subturn].statusEffects if i.turns > 0]

                
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
                    result = self.enemies[self.subturn].spells[self.currentEnemyAction.actionInd].EnemyAction(False, self.enemies, self.players, self.currentEnemyAction.targetInd, self.currentEnemyAction.potentialTargets, self.enemies[self.subturn], inputs, screen, world, self.buttonDrawer)
                    if result != -1:
                        # Activate end-of-my-turn status effects
                        for effect in self.enemies[self.subturn].statusEffects:
                            if effect.endOfTurn:
                                effect.activate(False, self.subturn, len(self.enemies), self.enemies[self.subturn], world)
                            effect.turns -= 1
                        self.enemies[self.subturn].statusEffects = [i for i in self.enemies[self.subturn].statusEffects if i.turns > 0]
                        oldenemies = self.enemies
                        self.enemies = [enemy for enemy in self.enemies if enemy.hp > 0]
                        # Next
                        # IF the current entity is still alive, bump index, otherwise keep it the same
                        if oldenemies[self.subturn] in self.enemies:
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
    "None":act.ActionCommand(),
    "Press Z Fast":act.pressButtonCommand(["z"], 48, 7, True, True),
    "Hidden Button Press":act.pressButtonCommand(["z", "x", "c"], 60, 3, False, True),
    "Hidden X/C Fast":act.pressButtonCommand(["x", "c"], 48, 7, False, True),
    "Hidden Direction Press":act.pressButtonCommand(["up", "down", "left", "right"], 60, 3, False, True),
    "Lenient 5 Directions":act.buttonSequenceCommand(["up", "down", "left", "right"], 5, 60, True),
    "Hidden 5 Directions":act.buttonSequenceCommand(["up", "down", "left", "right"], 5, 120, False),
    "Hidden 3 Fast Directions":act.buttonSequenceCommand(["up", "down", "left", "right"], 3, 52, False),
    "4 Directions in a Row":act.MultipleActionCommands([act.pressButtonCommand(["up", "down", "left", "right"], 32, 3, True, True),act.pressButtonCommand(["up", "down", "left", "right"], 32, 3, True, True),act.pressButtonCommand(["up", "down", "left", "right"], 32, 3, True, True),act.pressButtonCommand(["up", "down", "left", "right"], 32, 3, True, True)],8),
    "Hidden Button + Arrow Sequence":act.MultipleActionCommands([act.pressButtonCommand(["z", "x", "c"], 52, 3, False, True),act.buttonSequenceCommand(["z", "x", "c"], 5, 60, False)],20),
    "Difficult 12 Buttons/Directions":act.buttonSequenceCommand(["up", "down", "left", "right", "z", "x", "c"], 12, 105, True),
    "Hidden 5, Hidden 3, Mash Z":act.MultipleActionCommands([act.buttonSequenceCommand(["up", "down", "left", "right"], 5, 120, False),act.buttonSequenceCommand(["up", "down", "left", "right"], 3, 52, False),act.buttonSequenceCommand(["z"], 16, 48, True)],30),
    "X or Down":act.buttonSequenceCommand(["x","down"],6,120,False),
    "Hold X, then Up/Down":act.MultipleActionCommands([act.holdButtonCommand("x", 60, 3), act.buttonSequenceCommand(["up", "down"],8,60,True)],30),
    "Hold Z":act.holdButtonCommand("z", 60, 3), 
    "Hold X":act.holdButtonCommand("x", 60, 3),
    "Hold X Slow":act.holdButtonCommand("x", 120, 7),
    "Hold C Fast":act.holdButtonCommand("c", 48, 7),
    "Hold C Slow":act.holdButtonCommand("c", 120, 7),
    "Mash Z":act.buttonSequenceCommand(["z"], 16, 48, True),
    "Mash X":act.buttonSequenceCommand(["x"], 16, 48, True),
    "Mash Up":act.buttonSequenceCommand(["up"], 16, 48, True),
    "Mash Down":act.buttonSequenceCommand(["down"], 16, 48, True),
    "Mash Up/Down/X":act.MultipleActionCommands([act.buttonSequenceCommand(["up"], 16, 48, True),act.buttonSequenceCommand(["down"], 16, 48, True),act.buttonSequenceCommand(["x"], 16, 48, True)],48),
    "Triple Hit":act.MultipleActionCommands([act.pressButtonCommand(["z", "x", "c"], 30, 3, True, True),act.pressButtonCommand(["z", "x", "c"], 20, 4, True, True),act.pressButtonCommand(["z", "x", "c"], 12, 5, True, True)], 20),
    "Konami Code":act.MultipleActionCommands([
        act.pressButtonCommand(["up"],20,1,True,True),
        act.pressButtonCommand(["up"],20,1,True,True),
        act.pressButtonCommand(["down"],20,1,True,True),
        act.pressButtonCommand(["down"],20,1,True,True),
        act.pressButtonCommand(["left"],20,1,True,True),
        act.pressButtonCommand(["right"],20,1,True,True),
        act.pressButtonCommand(["left"],20,1,True,True),
        act.pressButtonCommand(["right"],20,1,True,True),
        act.pressButtonCommand(["x"],20,1,True,True),
        act.pressButtonCommand(["c"],20,1,True,True),
        act.pressButtonCommand(["z"],20,1,True,True),
    ],10)
}
spellList = {
    # ART SPELLS
    "Art Skill L1":Spell("Art Skill L1", ["Art Skill L1", "Magic attack, hits 1 enemy", "Hold Z!"], "1enemy", actionCommandList["Hold Z"],[DamageEffect(2.5, "magiAtk", "magiDef")]),
    "Art Skill L4":Spell("Art Skill L4", ["Art Skill L4", "Conjure a Creature to fight for you", "No Action Command"], "self", actionCommandList["None"],[]), # UNFINISHED
    "Art Skill L7":Spell("Art Skill L7", ["Art Skill L7", "Creature explodes, damaging all enemies", "Mash Z!"], "allenemies", actionCommandList["Mash Z"],[DamageEffect(7.5, "magiAtk", "magiDef")]), # UNFINISHED
    "Art Skill L10":Spell("Art Skill L10", ["Art Skill L10", "Heal the Creature. [Note: creature has no maximum health]", "No Action Command"], "self", actionCommandList["None"],[]), # UNFINISHED
    "Revive":Spell("Revive", ["Revive", "Revive a fallen party member and heal them", "No Action Command"], "1ally", actionCommandList["None"],[ReviveEffect(),HealEffect(0.2, "magiAtk")]),
    "Art Skill L16":Spell("Art Skill L16", ["Art Skill L16", "Shift the Creature to an ally.", "No Action Command"], "1ally", actionCommandList["None"],[]), # UNFINISHED
    "Art Skill L19":Spell("Art Skill L19", ["Art Skill L19", "Creature attacks 5 times.", "No Action Command"], "1enemy", actionCommandList["None"],[]), # UNFINISHED
    
    # SCIENCE SKILLS
    "Science Skill L1":Spell("Science Skill L1", ["Science Skill L1", "Magic attack, hits 1 enemy", "Press the shown button!"], "1enemy", actionCommandList["Hidden Button Press"],[DamageEffect(2.5, "magiAtk", "magiDef")]),
    "Science Skill L4":Spell("Science Skill L4", ["Science Skill L4", "Magic attack, hits all enemies", "Press the shown directions in order!"], "allenemies", actionCommandList["Lenient 5 Directions"],[DamageEffect(1.5, "magiAtk", "magiDef")]),
    "Science Skill L7":Spell("Science Skill L7", ["Science Skill L7", "Poison one enemy", "No Action Command"], "1enemy", actionCommandList["None"],[DoTEffect(0.25, "magiAtk", "Science DoT", 10, "poisonWeak")]),
    "Science Skill L10":Spell("Science Skill L10", ["Science Skill L10", "Put one enemy to sleep", "No Action Command"], "1enemy", actionCommandList["None"],[]), # UNFINISHED
    "Science Skill L13":Spell("Science Skill L13", ["Science Skill L13", "Powerful magic attack, hits 1 enemy", "Press the shown button, then the shown sequence!"], "1enemy", actionCommandList["Hidden Button + Arrow Sequence"],[DamageEffect(10, "magiAtk", "magiDef")]),
    "Science Skill L16":Spell("Science Skill L16", ["Science Skill L16", "Powerful magic attack, hits all enemies", "Press the shown buttons in sequence!"], "allenemies", actionCommandList["Difficult 12 Buttons/Directions"],[DamageEffect(5, "magiAtk", "magiDef")]),
    "Science Skill L19":Spell("Science Skill L7", ["Science Skill L19", "Reflect guarded magic attacks this turn, taking no damage.", "No Action Command"], "self", actionCommandList["None"],[]), # UNFINISHED
    
    # MATH SKILLS
    "Math Skill L1":Spell("Math Skill L1", ["Math Skill L1", "Draws in enemy attacks", "No Action Command"], "self", actionCommandList["None"],[]), # UNFINISHED
    "Math Skill L4":Spell("Math Skill L4", ["Math Skill L4", "Pulls damage away from allies,", "taking damage in the process for 5 turns", "No Action Command"], "allallies", actionCommandList["None"],[]), # UNFINISHED
    "Math Skill L7":Spell("Math Skill L7", ["Math Skill L7", "Shields party from CRITs", "for 5 turns", "No Action Command"], "allallies", actionCommandList["None"],[]), # UNFINISHED
    "Math Skill L10":Spell("Math Skill L10", ["Math Skill L10", "Creates a ward over the party", "that absorbs damage until destroyed", "Hold C, then release!"], "allallies", actionCommandList["Hold C Fast"],[]), # UNFINISHED
    "Math Skill L13":Spell("Math Skill L13", ["Math Skill L13", "Increases Defensive Stats", "for 5 turns", "No Action Command"], "self", actionCommandList["None"],[StatChangeFixedEffect(["physDef", "magiDef"], 0.8, "Math L13", 4, "buffBothDef")]),
    "Math Skill L16":Spell("Math Skill L16", ["Math Skill L16", "Braces self for a physical attack,", "dealing damage back when guarded", "No Action Command"], "self", actionCommandList["None"],[]), # UNFINISHED
    "Math Skill L19":Spell("Math Skill L19", ["Math Skill L19", "Deals heavy damage with user's physical defense", "Hold C, then release!"], "1enemy", actionCommandList["Hold C Slow"],[DamageEffect(5, "physDef", "physDef")]),
    
    # PSYCHOLOGY SKILLS
    "Psychology Skill L1":Spell("Psychology Skill L1", ["Psychology Skill L1", "Lowers an enemy's attack and magic attack", "Press the shown directions in order!"], "1enemy", actionCommandList["Lenient 5 Directions"],[StatChangeScalingEffect("magiAtk", ["physAtk"], -0.1, "Psych L1 PhysAtk", 4, "debuffPhysAtk"), StatChangeScalingEffect("magiAtk", ["magiAtk"], -0.1, "Psych L1 MagiAtk", 4, "debuffMagiAtk")]),
    "Psychology Skill L4":Spell("Psychology Skill L4", ["Psychology Skill L4", "Magic attack, hits 1 enemy", "Hold X!"], "1enemy", actionCommandList["Hold X"],[DamageEffect(2.5, "magiAtk", "magiDef")]),
    "Psychology Skill L7":Spell("Psychology Skill L7", ["Psychology Skill L7", "Raises the party's defenses", "Press the shown directions as they appear!"], "allallies", actionCommandList["Hidden 5 Directions"],[StatChangeScalingEffect("magiAtk", ["physDef"], 0.1, "Psych L7 PhysDef", 4, "buffPhysDef"), StatChangeScalingEffect("magiAtk", ["magiDef"], 0.1, "Psych L7 MagiDef", 4, "buffMagiDef")]),
    "Psychology Skill L10":Spell("Psychology Skill L10", ["Psychology Skill L10", "Increases an ally's crit chance", "Press the shown directions in time!"], "1ally", actionCommandList["4 Directions in a Row"],[]), # UNFINISHED
    "Psychology Skill L13":Spell("Psychology Skill L13", ["Psychology Skill L13", "Increases an ally's physical attack", "Press the shown directions as they appear!"], "1ally", actionCommandList["Hidden 3 Fast Directions"],[StatChangeScalingEffect("magiAtk", ["physAtk"], 0.1, "Psych L13 PhysAtk", 4, "buffPhysAtk")]), 
    "Psychology Skill L16":Spell("Psychology Skill L16", ["Psychology Skill L16", "Increases an ally's magical attack", "Press the shown directions as they appear!"], "1ally", actionCommandList["Hidden 3 Fast Directions"],[StatChangeScalingEffect("magiAtk", ["magiAtk"], 0.1, "Psych L13 MagiAtk", 4, "buffMagiAtk")]), 
    "Psychology Skill L19":Spell("Psychology Skill L19", ["Psychology Skill L19", "Increases all of the party's stats!", "Press the shown directions as they appear", "twice, then mash Z!"], "allallies", actionCommandList["Hidden 5, Hidden 3, Mash Z"],[StatChangeScalingEffect("magiAtk", ["physAtk"], 0.2, "Psych L19 PhysAtk", 4, "buffPhysAtk"),StatChangeScalingEffect("magiAtk", ["magiAtk"], 0.2, "Psych L19 MagiAtk", 4, "buffMagiAtk"),StatChangeScalingEffect("magiAtk", ["physDef"], 0.2, "Psych L19 PhysDef", 4, "buffPhysDef"),StatChangeScalingEffect("magiAtk", ["magiDef"], 0.2, "Psych L19 MagiDef", 4, "buffMagiDef")]),
    
    # HISTORY SKILLS
    "History Skill L1":Spell("History Skill L1", ["History Skill L1", "Heal an ally", "Hold X!"], "1ally", actionCommandList["Hold X"],[HealEffect(0.7, "magiAtk")]),
    "History Skill L4":Spell("History Skill L4", ["History Skill L4", "Cures all conditions", "on an ally", "No Action Command"], "1ally", actionCommandList["None"],[]), # UNFINISHED
    "History Skill L7":Spell("History Skill L7", ["History Skill L7", "Gives passive regeneration", "to an ally", "Press X or DOWN as it appears!"], "1ally", actionCommandList["X or Down"],[HoTEffect(0.3, "magiAtk", "History Regen", 5, "regen")]),
    # Revive
    "History Skill L13":Spell("History Skill L13", ["History Skill L13", "Heal party", "Hold X, then press UP and DOWN!"], "allallies", actionCommandList["Hold X, then Up/Down"],[HealEffect(0.5, "magiAtk")]),
    "History Skill L16":Spell("History Skill L16", ["History Skill L16", "Drain an enemy's life", "to heal the party", "Hold X!"], "1enemy", actionCommandList["Hold X Slow"],[MultiVampireEffect(4, 0.25, "magiAtk", "magiDef")]),
    "History Skill L19":Spell("History Skill L19", ["History Skill L19", "Revive all fallen party member and heals them greatly", "Mash UP, then DOWN, then X!"], "allallies", actionCommandList["Mash Up/Down/X"],[ReviveEffect(),HealEffect(2, "magiAtk")]), 

    "Languages Skill L1":Spell("Languages Skill L1", ["Languages Skill L1", "Lowers an enemy's defense and magic defense", "Can Stack", "Press the right direction when it appears!"], "1enemy", actionCommandList["Hidden Direction Press"],[StatScalingStackingEffect("magiAtk", ["physDef","magiDef"], -0.05, "Languages L1 BothDef", 3, "debuffBothDef")]),
    "Languages Skill L4":Spell("Languages Skill L4", ["Languages Skill L4", "Copies the last skill used", "by an ally.", "Previous Action Command"], "self", actionCommandList["None"],[]), # UNFINISHED
    "Triple Hit":Spell("Triple Hit", ["Triple Hit", "Hits three times", "Press the shown buttons in time!"], "1enemy", actionCommandList["Triple Hit"], [DamageEffect(1, "physAtk", "physDef") for i in range(3)]),
    "Languages Skill L10":Spell("Languages Skill L10", ["Languages Skill L10", "Deals heavy damage over 3 turns", "Press X or C!"], "1enemy", actionCommandList["Hidden X/C Fast"],[DoTEffect(1, "magiAtk", "Languages DoT", 3, "poisonStrong")]),
    "Languages Skill L13":Spell("Languages Skill L13", ["Languages Skill L13", "Attacks, with a chance to find an item", "Press Z!"], "1enemy", actionCommandList["Press Z Fast"],[]), # UNFINISHED
    "Languages Skill L16":Spell("Languages Skill L16", ["Languages Skill L16", "Activates damage over time effects", "on one enemy 3 times", "No Action Command"], "1enemy", actionCommandList["None"],[ActivateEffects() for x in range(3)]), # UNFINISHED
    "Languages Skill L19":Spell("Languages Skill L19", ["Languages Skill L19", "Removes status effects,", "dealing damage relative to amount", "Up-Up-Down-Down-","-Left-Right-Left-Right-","-X-C-Z!"], "1enemy", actionCommandList["Konami Code"],[]), # UNFINISHED
}