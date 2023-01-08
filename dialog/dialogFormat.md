# How to format dialog.txt

## Basics

Separate instances of dialog are separated by 2 newlines.

## Formatting a dialog
The first line will cotain the name of the dialog. Name things well and consistently!
Every line after that will contain a line of dialog, or a function.

### Line of dialog
The format for a line of dialog is as follows: 

`[text]|[options]|[next]`

`text` is what will be displayed in the dialog box.

`options` can be left blank(no spaces!), or can be a list of comma-separated options.

`next` refers to the line or lines to jump to next. 
There should either be one line number or an amount equal 
to the number of options (separated with commas).

The line number begins counting at 0, starting with the first line after the title.

Example line of dialog (no options):

`Test NPC: Hello, World!||3`

Example line of dialog (with options):

`Test NPC: Pineapple on Pizza?|Yes,No|3,6`

### Dialog Function
The format for a dialog function is as follows:

`\[function] [args]||[next]`

`function` is one of a couple predefined functions that do something in the game world.

The function might have arguments (`args`), in which case you would describe them separated by spaces.

`next` is, as always, an integer representing a line number.

#### A list of dialog functions and their implementation status
- [Usable, No function] `HealPlayer`: heals party fully and replenishes TP
- [Usable] `GiveQuest [quest]`: gives player the quest with id `quest`.
- [Usable] `BumpQuest [quest]`: "bumps" the quest with id `quest`'s completion status up by one.
- [Usable] `GiveItem [item]`: gives player an item with name `item`.
- [Usable] `TakeItem [item]`: takes away an item with name `item` from player.

### Examples

Putting all these together, here is an example dialog:
```julia
Test Dialog
Test NPC:Hello!||1
Test NPC:Welcome to the healing place!||2
Test NPC:Would you like to heal?|Yes,No|4,3
Test NPC:Goodbye!||-2
\HealPlayer||5
Healed fully!||3
```

Here it is again with the different parts highlighted, and line numbers superimposed:
```julia
[TITLE]Test Dialog
[0]Test NPC:Hello!||1 #line of dialog
[1]Test NPC:Welcome to the healing place!||2
[2]Test NPC:Would you like to heal?|Yes,No|4,3 #options
[3]Test NPC:Goodbye!||-2
[4]\HealPlayer||5 #healing function
[5]Healed fully!||3
```

## Message me if you have any questions!
