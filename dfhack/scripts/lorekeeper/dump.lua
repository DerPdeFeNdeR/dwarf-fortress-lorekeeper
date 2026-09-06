-- Read-only selected-unit inspector for The Lorekeeper.
--
-- Install this repository's dfhack/scripts directory as a DFHack script path,
-- then run: lorekeeper/dump

local function get_display_name(unit)
    if not unit.name then
        return '<unnamed>'
    end

    local name = dfhack.units.getVisibleName(unit)
    if name then
        local translated_name = dfhack.translation.translateName(name, true)
        if translated_name and translated_name ~= '' then
            return translated_name
        end
    end

    return '<unnamed>'
end

local function get_race_name(unit)
    local creature_raw = df.global.world.raws.creatures.all[unit.race]
    if creature_raw and creature_raw.creature_id then
        return creature_raw.creature_id
    end

    return '<unknown>'
end

local function get_caste_name(unit)
    local creature_raw = df.global.world.raws.creatures.all[unit.race]
    if not creature_raw or not creature_raw.caste then
        return '<unknown>'
    end

    local caste_raw = creature_raw.caste[unit.caste]
    if caste_raw and caste_raw.caste_id then
        return caste_raw.caste_id
    end

    return '<unknown>'
end

local function get_enum_name(enum, value)
    if type(value) == 'string' then return value end; local direct_name = enum[value]; if type(direct_name) == 'string' then return direct_name end; for enum_value, enum_name in ipairs(enum) do if enum_value == value then return enum_name end end; return ('<unknown:%s>'):format(tostring(value))
end

local function print_thoughts(personality)
    print('  thoughts:')
    if #personality.emotions == 0 then
        print('    <none>')
        return
    end

    for index, thought in ipairs(personality.emotions) do
        print(('    [%d] thought=%s emotion=%s severity=%d relative_strength=%d subthought=%d'):format(
            index,
            get_enum_name(df.unit_thought_type, thought.thought),
            get_enum_name(df.emotion_type, thought.type),
            thought.severity,
            thought.relative_strength,
            thought.subthought))
    end
end

local function print_personality(personality)
    print(('  stress: %d'):format(personality.stress))
    print('  personality_traits:')

    for facet, value in pairs(personality.traits) do
        print(('    %s=%d'):format(
            get_enum_name(df.personality_facet_type, facet),
            value))
    end
end

local unit = dfhack.gui.getSelectedUnit(true)
if not unit then
    print('The Lorekeeper: no unit is currently selected.')
    return
end

print('The Lorekeeper: selected unit')
print(('  df_version: %s'):format(dfhack.getDFVersion()))
print(('  dfhack_version: %s'):format(dfhack.getDFHackVersion()))
print(('  id: %d'):format(unit.id))
print(('  name: %s'):format(get_display_name(unit)))
print(('  race: %s'):format(get_race_name(unit)))
print(('  caste: %s'):format(get_caste_name(unit)))
print(('  profession: %s'):format(dfhack.units.getProfessionName(unit)))
print(('  citizen: %s'):format(dfhack.units.isCitizen(unit) and 'true' or 'false'))

local soul = unit.status and unit.status.current_soul
if not soul then
    print('  soul: <none>')
    return
end

print('  soul: present')
print_thoughts(soul.personality)
print_personality(soul.personality)
