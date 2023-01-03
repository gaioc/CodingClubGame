# Explanation of the usage of the files in this folder

## Equipment and class data
Should be loaded from `equipment.txt` and `classStats.txt` using `equipment.loadEquipment(<file name>)` and `stats.readClassStats(<file name>)` respectively

## Player characters
Player Characters are defined by the `playerStats.Character` object and are initialized in the following way:

```py
testPlayer = playerStats.Character(<name>, playerStats.playerEquip(), playerStats.playerBaseStats(<level>, <class stats>, <effort points>))
```

`<name>` is the name of the character (string), `<level>` is their level (int), `<class stats>` is the stats loaded by `stats.readClassStats()`, indexed by class name, and `<effort points>` is a dict describing the effort points spent on each stat.

Players can equip equipment using the `equip(<equipment>)` and `unEquip()` functions.

### Example usage:
```py
with open("equipment.txt") as equipData:
    equipDict, enchantDict = equip.loadEquipment(equipData.read())
with open("classStats.txt") as classData:
    classDict = stats.readClassStats(classData.read())

bob = pStats.Character("Bob", pStats.PlayerEquip(), pStats.PlayerBaseStats(10, classDict["english"], {"maxHP":0, "physAtk":0, "physDef":0, "magiAtk":0, "magiDef":0}))
print(equipDict)
bob.equip(equipDict["Simple Calculator"])
bob.equip(equipDict["Protector's Shield"])
```
This script reads in the equipment and class data in `equipment.txt` and `classStats.txt`, then creates a player character called Bob, a level ten english student with no equipment or EPs.(effort points)
It then equips the equipment "Simple Calculator" and "Protector's Shield" to Bob.

Once again, if you have any questions, feel free to ask me on discord
