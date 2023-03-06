# How to format npcFormat.txt (when it gets implemented)

## Basics

Separate NPCs are separated by 2 newlines.

## Formatting an NPC
The first line will cotain the name of the NPC. Name things well and consistently!
Every line after that will contain a condition, and a dialog. (ordered in order of priority)

### Line
The line is formatted as follows:
`TestCondition: TestDialog`, where TestCondition is a Condition (will be explained), and TestDialog is the name of a Dialog as described in `dialog.txt`.

### Conditions
Conditions have a name, and (sometimes) arguments. A full list of conditions will be detailed here.
___
#### `FirstInteraction()`
Returns True if this is the first time meeting the NPC.
___
#### `PlayerClass(class)`
Returns True if Lux's chosen class matches `class`.
___
#### `QuestStatus(status)`
This one returns True if `status` matches the current status of the quest. (-1 means not taken, everything else represents different completion stages in increasing order.)
___
#### `HasItem(item)`
Returns True if `item` is in the player's inventory.
___
#### `Auto()`
Returns True, all the time.
___
#### `Any(conds...)` and `All(conds...)`
Return True if any(`Any`) or all(`All`) of the above conditions (`conds`) are met.
___
#### `Not(cond)`
Return True if condition is not met.

## Example NPC

```py
Bobby
FirstInteraction(): Fix Healing Place - First
QuestStatus(FixHealingPlace, -1): Fix Healing Place
All(QuestStatus(FixHealingPlace, 0), HasItem(<Item>)): Fix Healing Place - Conditions met
QuestStatus(FixHealingPlace, 0): Fix Healing Place - Reminder
QuestStatus(FixHealingPlace, 1): Healing Place Interaction
```

Reading through this in pseudocode, we get:

```
Bobby
If this is the first time meeting Bobby, then A
Otherwise, if the player does not have this quest, then B
Otherwise, if the player has the quest and the necessary item, then C
Otherwise, if the player has the quest, then D
Finally, if the player has completed the quest, then E
```

## This one might be a bit harder to use :sweat_smile:
## As usual, if you have any questions, ask!