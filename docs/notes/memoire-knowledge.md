# Memoire knowledge boundary — 2026-09-06

The user requested personal first-person accounts without omniscient knowledge,
and the product spelling **Memoire**, including the in-game window and button.

`helper/memoire_knowledge.py` sanitizes a copy of the on-demand profile before
`build_story_input` derives compact references, life events, historical episodes,
and heard-story anchors. Personal event participation requires the exact subject
HF ID and supported role. Own death and social-link changes alone are not personal
knowledge. Battle participation does not disclose every other combatant.

Family/friend references preserve names but do not import world-recorded births
and deaths. Witnessed incidents preserve victim identity but omit hidden causes,
killers, dates and locations. Explicit heard tales retain their resolved topic
and teller, always framed as listening rather than participation. Unsupported
knowledge stays absent: never invent a rumor to supply it. This is a conservative
boundary; richer facts need explicit personal evidence before they can be added.

The raw profile and technical timeline remain unchanged; fortress chronicles
retain broader event coverage. Filtering is bounded by existing profile caps,
runs in Python, and adds no periodic collection or render-loop model work.

View schema 24 and monthly-book version 2 invalidate prior narrative context.
An old book is archived on the next explicit preparation, not deleted or used to
seed new passages. Dormant books are not regenerated in bulk. Saved old revisions
may remain visible while preparation starts; new prose must use filtered evidence.

`lorekeeper/memoire` opens the reader; `lorekeeper/read` remains compatible.
Historical filenames, JSON keys and `lorekeeper/overlay.biography` are retained
to preserve existing storage and saved overlay configuration. They are not the
player-facing product name.

Regression tests cover family/world fact exclusion, victim-only incident details,
exact personal roles, battle participants, heard-topic framing, source immutability,
stable reference order and old-book migration without prior prose.
