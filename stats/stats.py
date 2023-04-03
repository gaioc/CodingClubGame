from math import floor

#ANY PRINT STATEMENTS ARE TEMPORARY. ONCE UI IS FINALIZED, THINGS WILL CHANGE




class Stats(dict):
    """
    For now, is just a dict. 
    Additional functions may come later, 
    and if they do, this is where they go.
    """
    pass

class StatModifier:
    """
    Base class. Only use inherits AdditiveModifier and MultiplicativeModifier
    """
    def __init__(self, amount):
        self.amount = amount

class AdditiveModifier(StatModifier):
    """
    Modifier that adds to a stat directly. Combines additively.
    Example: +20 attack
    Example combination: +20 attack and +10 attack = +30 attack
    """
class MultiplicativeModifier(StatModifier):
    """
    Modifier that multiplies a stat. Combines additively.
    Example: +20% attack (x (1 + 0.2))
    Example combination: +20% attack and +50% attack = +70% attack (x (1 + 0.2 + 0.5))
    """

def calculateBattleStat(baseStat, additiveModifiers, multiplicativeModifiers):
    """
    Combines additive and multiplicative modifiers properly to get the final in-battle stat.
    """
    return (baseStat + sum([a.amount for a in additiveModifiers])) * (1 + sum([m.amount for m in multiplicativeModifiers]))






def baseHPCalc(level, ivs, evs):
    """
    Calculates the MaxHP stat of a character given level, IVs, and EVs.
    """
    statMultiplier = ivs * (1 + evs/16)
    return int(floor(1.18537581656**level * 10 * statMultiplier))# + 4.99*level)
def baseStatCalc(level, ivs, evs):
    """
    Calculates any stat other than MaxHP given level, IVs, and EVs.
    """
    statMultiplier = ivs * (1 + evs/16)
    return int(1.18537581656**level * 10 * statMultiplier)

def damageCalc(attack, defense, baseDamage):
    """
    Calculates damage given attack, defense, and base damage.
    """
    return max(1, int((attack**2 * baseDamage) / (attack + defense)))

class ClassStats(dict):
    pass

def readClassStats(statsString):
    finalStats = ClassStats()
    classes = statsString.split("\n\n")
    for classData in classes:
        lines = classData.split("\n")
        name = lines[0]
        stats = dict()
        for statLine in lines[1:]:
            parts = statLine.split(":")
            stats[parts[0]] = float(parts[1])
        finalStats[name] = stats
    return finalStats
