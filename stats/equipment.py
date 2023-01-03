class EquipStatModifier:
    def __init__(self, name, value):
        self.name = name
        self.value = value

class EquipStat:
    def __init__(self, value):
        self.baseValue = value
        self.value = value
        self.modifiers = dict()
    def add(self, modifier):
        if not(modifier.name in self.modifiers.keys()):
            self.value += modifier.value
            self.modifiers[modifier.name] = modifier.value
    def remove(self, modName):
        if modName in self.modifiers.keys():
            self.value -= self.modifiers.pop(modName)
    def __repr__(self):
        return f"{self.value:2}({self.baseValue:2}\t{self.value - self.baseValue:3})"
            


class EquipStats(dict):
    def __init__(self, maxHP, physAtk, physDef, magiAtk, magiDef):
        super().__init__()
        self["maxHP"] = EquipStat(maxHP)
        self["physAtk"] = EquipStat(physAtk)
        self["physDef"] = EquipStat(physDef)
        self["magiAtk"] = EquipStat(magiAtk)
        self["magiDef"] = EquipStat(magiDef)
    def __repr__(self):
        out = ""
        for k, v in self.items():
            out += f"{k.upper():16}: {v}\n"
        return out
    def add(self, other, name):
        """Self is a dict of Stats, other is a dict of StatModifiers"""
        for k, v in other.items():
            self[k].add(EquipStatModifier(name, other[k]))
        return self
    def remove(self, other):
        for k, v in other.items():
            self[k].remove(other[k].name)
        return self

class Equipment:
    def __init__(self, name, modifiers, slot):
        self.name = name
        self.modifiers = modifiers
        self.slot = slot
    def __repr__(self):
        out = ""
        out += self.name + "\n"
        out += self.slot.title() + "\n"
        for k, v in self.modifiers.items():
            out += f"{k.upper():16}: {v:3}\n"
        return out
    def enchant(self, enchantment):
        """Non-destructive. Returns newly enchanted item."""
        if enchantment.applicable[self.slot]:
            enchanted = Equipment(
                (f"{self.name} {enchantment.name}" if enchantment.postfix else f"{enchantment.name} {self.name}"), 
                dict(), self.slot)
            allModsList = list(self.modifiers.items()) + list(enchantment.modifiers.items())
            for k,v in allModsList:
                if k in enchanted.modifiers.keys():
                    enchanted.modifiers[k] += v
                else:
                    enchanted.modifiers[k] = v
            return enchanted
        else:
            raise RuntimeError(f"Enchantment {enchantment.name} cannot be applied to slot {self.slot}")
        


class Enchantment:
    def __init__(self, name, modifiers, applicable, postfix):
        self.name = name
        self.modifiers = modifiers
        self.applicable = applicable
        self.postfix = postfix
    def __repr__(self):
        out = ""
        out += self.name + "\n"
        out += "\n".join([k if v else "" for k, v in self.applicable.items()]) + "\n"
        for k, v in self.modifiers.items():
            out += f"{k.upper():16}: {v:3}\n"
        return out

def loadEquipment(equipString):
    equipmentStrList = equipString.split("\n\n")
    finalEquipment = dict()
    finalEnchantments = dict()
    for equipStr in equipmentStrList:
        params = equipStr.split("\n")
        try:
            name = params[0]
        except:
            raise SyntaxError("Invalid or Missing item name")
        if params[1] == "enchantment":
            postfix = (params[2]=="postfix")
            applicable = dict(zip(["weapon", "armour", "accessory"],[i.title()=="True" for i in params[3:6]]))
            modifiers = {
                    i.split(":")[0]:int(i.split(":")[1]) for i in params[6:]
            }
            finalEnchantments[name] = Enchantment(name, modifiers, applicable, postfix)
        else:
            try:
                slot = params[1]
            except:
                raise SyntaxError(f"Invalid or Missing item slot for {name}")
            try:
                modifiers = {
                    i.split(":")[0]:int(i.split(":")[1]) for i in params[2:]
                }
            except:
                raise SyntaxError(f"Invalid or Missing item modifiers for {name}")
            finalEquipment[name] = Equipment(name, modifiers, slot)
    return finalEquipment, finalEnchantments
