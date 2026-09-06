# Environment discovery — 2026-09-06

- Target game: Steam version of Dwarf Fortress.
- DFHack installation found at:
  `C:\Program Files (x86)\Steam\steamapps\common\DFHack`
- DFHack configuration used for development script paths:
  `C:\Program Files (x86)\Steam\steamapps\common\Dwarf Fortress\dfhack-config\script-paths.txt`
- Repository script path configured:
  `+C:\Users\contr\projects\dwarf-fortress-lorekeeper\dfhack\scripts`
- First repository command:
  `lorekeeper/dump`
- In-game validation completed successfully: after restarting Dwarf Fortress,
  `lorekeeper/dump` displayed selected-dwarf information.
- The dump was then extended to inspect `unit.status.current_soul.personality`
  for raw emotions/thoughts, personality traits, and stress. In-game
  verification completed successfully for dwarf Mistêm Woundcolored under DF 0.53.16 / DFHack 53.16-r1.1. Thought and personality fields are readable.
- Dwarf Fortress must be restarted after changing `script-paths.txt`.
