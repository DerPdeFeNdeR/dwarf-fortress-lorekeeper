# The Lorekeeper — DFHack development scripts

This directory contains repository-local DFHack scripts. It is intentionally
not copied into the user's DFHack installation automatically.

## Install for development

The recommended development setup is to add this repository directory as a
DFHack script path. Open this file in a text editor (create it if it does not
exist):

```text
C:\Program Files (x86)\Steam\steamapps\common\Dwarf Fortress\dfhack-config\script-paths.txt
```

Add this line, using the Windows path format:

```text
+C:\Users\contr\projects\dwarf-fortress-lorekeeper\dfhack\scripts
```

The leading `+` tells DFHack to search this development directory before its
default script directories. DFHack reads the file at startup, so fully exit
and restart Dwarf Fortress after changing it. This keeps edits in the project
available without copying files into the DFHack installation.

The equivalent WSL path is:

```text
/mnt/c/Users/contr/projects/dwarf-fortress-lorekeeper/dfhack/scripts
```

The local DFHack installation discovered during Milestone 0 is:

```text
/mnt/c/Program Files (x86)/Steam/steamapps/common/DFHack
```

## First command

1. Start Dwarf Fortress through Steam.
2. Load a fortress save.
3. Select a dwarf with the normal `v` unit view or the unit list.
4. Open the DFHack console. On Windows, use the DFHack console window or the
   in-game DFHack console if enabled.
5. Run:

```text
lorekeeper/dump
```

The command is read-only and currently reports selected-unit identity data.
If no unit is selected, it will print a harmless message instead.

To open the first in-game summary window, select a dwarf and run:

```text
lorekeeper/show
```

Use `Ctrl-R` to refresh the selected dwarf, `Ctrl-C` to copy the visible
summary to the system clipboard, and `Esc` to close the window.

Useful troubleshooting commands:

```text
help lorekeeper/dump
ls lorekeeper
```

To export the active runtime token catalog, run:

```text
lorekeeper/tokens
```

To copy the catalog to the system clipboard:

```text
lorekeeper/tokens copy
```

If DFHack cannot find the command, confirm the path has no quotes, restart the
game completely, and check that the repository file exists at
`dfhack/scripts/lorekeeper/dump.lua`.
