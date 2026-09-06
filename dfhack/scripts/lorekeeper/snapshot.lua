-- Structured selected-dwarf data for The Lorekeeper.
--
-- This module is the boundary between DFHack objects and Lorekeeper's
-- presentation, translation, and history layers.
--@module = true

local function get_enum_name(enum, value)
    if type(value) == 'string' then
        return value
    end

    local direct_name = enum[value]
    if type(direct_name) == 'string' then
        return direct_name
    end

    for enum_value, enum_name in ipairs(enum) do
        if enum_value == value then
            return enum_name
        end
    end

    return ('<unknown:%s>'):format(tostring(value))
end

local function get_display_name(unit)
    local name = dfhack.units.getReadableName(unit, true)
    if name and name ~= '' then
        return dfhack.df2console(name)
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

local function get_context()
    local context = {
        site_id=df.global.plotinfo and df.global.plotinfo.site_id or nil,
    }

    local savegame = df.global.world.cur_savegame
    if savegame and savegame.save_dir then
        context.save_id = savegame.save_dir
    end

    return context
end

local function capture_thoughts(personality)
    local thoughts = {}
    for _, thought in ipairs(personality.emotions) do
        table.insert(thoughts, {
            thought_id=thought.thought,
            thought_name=get_enum_name(df.unit_thought_type, thought.thought),
            emotion_id=thought.type,
            emotion_name=get_enum_name(df.emotion_type, thought.type),
            severity=thought.severity,
            relative_strength=thought.relative_strength,
            subthought=thought.subthought,
        })
    end

    return thoughts
end

local function capture_personality_facets(personality)
    local facets = {}
    for facet, value in pairs(personality.traits) do
        table.insert(facets, {
            facet_id=facet,
            facet_name=get_enum_name(df.personality_facet_type, facet),
            value=value,
        })
    end

    table.sort(facets, function(a, b)
        return a.facet_name < b.facet_name
    end)

    return facets
end

function capture(unit)
    if not unit then
        return nil
    end

    local captured = {
        schema_version=1,
        source={
            df_version=dfhack.getDFVersion(),
            dfhack_version=dfhack.getDFHackVersion(),
        },
        context=get_context(),
        identity={
            id=unit.id,
            name=get_display_name(unit),
            race=get_race_name(unit),
            caste=get_caste_name(unit),
            profession=dfhack.units.getProfessionName(unit),
            citizen=dfhack.units.isCitizen(unit),
        },
        thoughts={},
        mental_state={
            stress=nil,
        },
        personality_facets={},
        soul_present=false,
    }

    local soul = unit.status and unit.status.current_soul
    if soul then
        captured.soul_present = true
        captured.thoughts = capture_thoughts(soul.personality)
        captured.mental_state.stress = soul.personality.stress
        captured.personality_facets = capture_personality_facets(soul.personality)
    end

    return captured
end

function capture_selected_unit()
    return capture(dfhack.gui.getSelectedUnit(true))
end
