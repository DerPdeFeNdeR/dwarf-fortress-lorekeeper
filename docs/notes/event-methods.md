# Event causes and methods — 2026-09-06

The user requested that deaths, killings and similar events say how they happened
when supported. `event_index.enrich` now calls `event_method.capture` only for
requested death/wound records. One exact event lookup, no global scan; at most
two item-definition/material resolutions for recorded impact item and launcher.
Names use recorded type/subtype/material rather than a possibly changed current
item description. Unresolved definitions retain IDs/status without guessed names.

Verified against installed `hack/scripts/deathcause.lua` and
[DFHack event definitions](https://github.com/DFHack/df-structures/blob/master/df.history_event.xml):
death weapon fields distinguish `item` and `shooter_item`; wounds expose
`injury_type`, `body_part`, `woundee_race`, `woundee_caste`, and `part_lost`.
Wound body names are `vector<string*>`; unwrap `.value` before UTF-8 conversion.
The installed injury enum provides BLUDGEON, SLASH, PIERCE, GORE and BURN.

Python's explicit cause/injury glossary excludes generic/unknown meanings.
Selected method details become required adjacent coverage. Drowning is a cause,
not automatically proof the named killer deliberately drowned the victim.
Weapon type does not establish a particular swing, intent, exact attack sequence,
or body part. No combat-log reconstruction is attempted. Methods of rescue,
abduction and other events remain unknown unless already explicit in their data.
Memoires retain methods only for admitted personal events, not unseen incidents
or the lives of family/friends. Raw profile diagnostics remain unchanged.

View schema 25 invalidates prepared views on explicit refresh/preparation.
New method fields participate in monthly evidence comparisons. Finished annual
chapters remain immutable. U in a Memoire requests fresh input; D in Chronicles
requests an updated current-year draft. No DF restart required; watcher restart
loads the Python changes.

Verification: 149 Python tests (144 passed, 5 opt-in skipped); 110 actual DFHack
tests passed. A separate live generation/cache check passed in 6.20 seconds and
retained blood loss plus the recorded iron axe. Temporary, uninserted DF event
objects verified real weapon naming and wound body-part conversion, and were
deleted afterward. Live indexed deaths 76829/76841/77070 resolved STRUCK_DOWN,
BLEED and THIRST respectively; none recorded weapon fields. These are not
evidence of a particular weapon for the struck-down death. No private save data
was copied into the repository. Player review remains pending; no commit/push.
