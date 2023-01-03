from stats.equipment import *
from stats.stats import *
class PlayerEquip:
    """
    Container that holds the player's out of battle static stats (not current hp, tp, etc).
    Only use equip() and unequip() to modify values, or, call calculate() after any modifications.
    Ideally, though, don't.
    """
    def __init__(self):
        self.equipStats = EquipStats(0,0,0,0,0)
        self.equipment = {
            "weapon":None,
            "armour":None,
            "accessory":None
        }
    def __repr__(self):
        out = f"{str(self.stats)}\n"
        for k, v in self.equipment.items():
            out += f"\n{k.upper():16}: {v.name if v else 'NONE'}"
        return out
    def equip(self, equipment):
        if not(self.equipment[equipment.slot]):
            self.equipStats.add(equipment.modifiers, equipment.slot)
            self.equipment[equipment.slot] = equipment
    def unEquip(self, slot):
        equipment = self.equipment[slot]
        for k, v in self.stats.items():
            self.equipStats[k].remove(slot)
        self.equipment[slot] = None
        return equipment
class PlayerBaseStats:
    def __init__(self, level, ivs, evs):
        """
        Initialize object with a level, ivs, and evs. 
        Automatically calls calculate() to determine base stats.
        """
        self.level = level
        self.ivs = ivs
        self.evs = evs
        self.calculate()
    def __repr__(self):
        """
        Prints all of the stats, and their IVs and EVs.
        """
        out = ""
        for k in self.ivs:
            out += f"{k:20}: {self.finalStats[k]:3} ({self.ivs[k]:2.1f} IVs) ({self.evs[k]:1} EVs)\n"
        return out
    def calculate(self):
        """
        Calculates and sets the final stats of this PlayerStats object.
        Assumes the existence of a MaxHP stat, which **should** exist, otherwise something is
        deeply wrong.
        """
        self.finalStats = dict()
        for k in self.ivs:
            if k == "maxHP":
                self.finalStats["maxHP"] = baseHPCalc(self.level, self.ivs["maxHP"], self.evs["maxHP"])
            else:
                self.finalStats[k] = baseStatCalc(self.level, self.ivs[k], self.evs[k])
    def setLevel(self, value):
        """
        Sets level and then recalculates stats.
        """
        self.level = value
        self.calculate()
    def setEv(self, stat, value):
        """
        Sets an EV and then recalculates stats.
        """
        self.evs[stat] = value
        self.calculate()


class Character:
    def __init__(self, name, equipment, baseStats):
        self.name = name
        self.equipment = equipment
        self.baseStats = baseStats

        self.totalStats = dict()
        self.calculate()
    def __repr__(self):
        out = ""
        out += self.name + "\n"
        for k in self.totalStats.keys():
            out += f"{k:20}: {self.totalStats[k]:4} (Base: {self.baseStats.finalStats[k]:4} Equipment: {self.equipment.equipStats[k].value:4})\n"
        out += "Equipment:\n"
        out += f"Weapon   : {self.equipment.equipment['weapon'].name if self.equipment.equipment['weapon'] else None}\n"
        out += f"Armour   : {self.equipment.equipment['armour'].name if self.equipment.equipment['armour'] else None}\n"
        out += f"Accessory: {self.equipment.equipment['accessory'].name if self.equipment.equipment['accessory'] else None}\n"
        return out
    def calculate(self):
        for k in self.equipment.equipStats.keys():
            self.totalStats[k] = self.equipment.equipStats[k].value + self.baseStats.finalStats[k]
    def equip(self, equipment):
        self.equipment.equip(equipment)
        self.calculate()
    def unEquip(self, slot):
        self.equipment.unEquip(slot)
        self.calculate()
        
