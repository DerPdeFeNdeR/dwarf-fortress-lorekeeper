# Dwarf age and voice metadata — 2026-09-07

Dwarf Fortress life stages are derived from the creature raw definitions:

- ages 0 through less than 1 year are babies;
- ages 1 through less than 12 are children;
- age 12 and above is adult.

The game does not define an `elder` life stage. Dwarves may die of old age within
their species lifespan range (roughly 150–170 years), but age alone does not
reduce their skills or mental ability. Lorekeeper therefore stores `life_stage`
using the game terms and may also store `narrative_band: older_adult` as an
editorial delivery cue for a patient, long-view voice. That cue is never exposed
to the model as game metadata or used to infer frailty, forgetfulness, or reduced
intelligence. Baby and child guidance remains readable and must not invent adult
reasoning or independent actions. Child prose should make age noticeable through
concrete attention, curiosity, shorter thought movements, and simpler literal
phrasing while preserving intelligence and avoiding unsupported sensory detail.

The profile and annual narrator captures include `age` when birth data is
available. Missing birth data remains explicitly unknown. The current-year
calculation follows the integer age exposed by DF; exact birthday timing is not
claimed when the available capture cannot establish it.

When a live unit is explicitly labeled `Dwarven Baby` or `Dwarven Child`, that
life-stage label takes precedence over a conflicting birth-year estimate. The
estimate is retained in `age.years` with `age.source: birth_year_estimate` or
`unit_life_stage` for diagnosis; it is not used to make the prose adult when DF
identifies the unit as a child.
