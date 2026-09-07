-- Bounded on-demand biography context. Never called by the background collector.
--@module = true
local references = reqscript('lorekeeper/references')

local function field(object, key)
    local ok, value = pcall(function() return object[key] end)
    if ok then return value end
end

local function label(enum, value)
    return field(enum, value) or tostring(value)
end

function reference_kind(thought)
    return references.thought_kind(thought)
end

function quick_overview(unit)
    local lines = {'Character overview (not a generated biography)'}
    local soul = unit.status.current_soul
    if not soul then table.insert(lines, 'No personality information is available.'); return lines end
    local mind = soul.personality
    table.insert(lines, 'Current stress: ' .. tostring(mind.stress))
    table.insert(lines, 'Emotional entries, which may include recalled experiences:')
    local glossary = reqscript('lorekeeper/glossary')
    for i=math.max(0, #mind.emotions-3),#mind.emotions-1 do
        local entry = mind.emotions[i]
        local thought = glossary.describe_thought(label(df.unit_thought_type, entry.thought))
        local emotion = glossary.describe_emotion(label(df.emotion_type, entry.type))
        table.insert(lines, '- ' .. (thought.label or thought.text or label(df.unit_thought_type, entry.thought)) ..
            ' / ' .. (emotion.label or emotion.text or label(df.emotion_type, entry.type)))
    end
    return lines
end

local function scalar_fields(object, names)
    local result = {}
    for _, name in ipairs(names) do
        local value = field(object, name)
        if type(value) == 'number' or type(value) == 'boolean' or type(value) == 'string' then
            result[name] = value
        end
    end
    return result
end

function capture(unit)
    local resolver = references.new(references.game_providers())
    local result = {schema_version=7, unit_id=unit.id,
        histfig_id=unit.hist_figure_id, captured_at={year=df.global.cur_year,
        tick=df.global.cur_year_tick}, source={df_version=dfhack.getDFVersion(),
        dfhack_version=dfhack.getDFHackVersion()}, limitations={}, figures={},
        references=resolver.records}
    local function section(name, vector, convert, limit)
        local rows = {}
        result[name] = rows
        if not vector then
            table.insert(result.limitations, name .. ': unavailable')
            return
        end
        for _, value in ipairs(vector) do
            -- DF vectors are zero-indexed; count actual visits, not indices.
            if #rows >= (limit or 64) then
                table.insert(result.limitations, name .. ': truncated')
                break
            end
            local ok, row = pcall(convert, value)
            if ok then table.insert(rows, row or {unavailable=true})
            else table.insert(rows, {unavailable=true}); table.insert(result.limitations, name .. ': unsupported entry') end
        end
    end
    local figure = df.historical_figure.find(unit.hist_figure_id)
    result.historical_events=reqscript('lorekeeper/event_index').capture(unit.hist_figure_id,resolver)
    section('relationships', figure and figure.histfig_links, function(link)
        local target = resolver:resolve('historical_figure', link.target_hf)
        return {target_hf=link.target_hf, kind=tostring(link._type),
            target_name=target.details and target.details.name,
            reference_key=target.key, reference_status=target.status,
            strength=field(link, 'link_strength'), observed_now=true}
    end)
    local soul = unit.status.current_soul
    local personality = soul and soul.personality
    local function emotion(value)
        local row = scalar_fields(value, {'thought','type','subthought','severity',
            'strength','relative_strength','year','year_tick','created_year','created_tick'})
        row.thought_name = label(df.unit_thought_type, row.thought)
        row.emotion_name = label(df.emotion_type, row.type)
        row.flags = scalar_fields(field(value, 'flags'), {'memory','remembered',
            'remembered_shortterm','remembered_reflected_on','facet_change','value_change'})
        row.reference_kind = reference_kind(row.thought_name)
        local kind = row.reference_kind == 'unresolved' and ('thought:' .. row.thought_name) or row.reference_kind
        local target = resolver:resolve(kind, row.subthought)
        row.reference_key = target.key
        row.reference_status = target.status
        return row
    end
    section('emotions', personality and personality.emotions, emotion, 128)
    local memories = field(personality, 'memories')
    section('shortterm_memories', field(memories, 'shortterm'), emotion)
    section('longterm_memories', field(memories, 'longterm'), emotion)
    section('core_memories', field(memories, 'core_memories'), function(value)
        local row = scalar_fields(value, {'changed_facet','facet_old','facet_new',
            'changed_value','value_old','value_new'})
        row.memory = emotion(value.memory)
        return row
    end)
    section('values', field(personality, 'values'), function(value)
        local row = scalar_fields(value, {'type','strength'})
        row.name = label(df.value_type, row.type)
        return row
    end)
    section('needs', field(personality, 'needs'), function(value)
        local row = scalar_fields(value, {'id','deity_id','focus_level','need_level'})
        row.name = label(df.need_type, row.id)
        if row.deity_id and row.deity_id >= 0 then
            local target = resolver:resolve('historical_figure', row.deity_id)
            row.reference_key, row.reference_status = target.key, target.status
        end
        return row
    end)
    section('preferences', field(soul, 'preferences'), function(value)
        local row = scalar_fields(value, {'type','item_type','item_subtype','creature_id',
            'color_id','shape_id','plant_id','poetic_form_id','musical_form_id',
            'dance_form_id','mattype','matindex','active'})
        row.type_name = label(df.unitpref_type, row.type)
        row.references = {}
        for _, target in ipairs(references.preference_targets(row, row.type_name)) do
            local resolved = resolver:resolve(target.kind, target.id, target.extra)
            table.insert(row.references, {key=resolved.key, status=resolved.status})
        end
        return row
    end)
    local social = field(field(figure,'info'),'relationships')
    local friend_limits
    result.friends, friend_limits = reqscript('lorekeeper/friends').capture(field(social,'hf_visual'),resolver)
    for _,note in ipairs(friend_limits) do table.insert(result.limitations,note) end
    table.insert(result.limitations,'Friends are directional current observations, not mutual bonds or dated formation events.')
    result.personality_facets = scalar_fields(field(personality, 'traits'),
        {'ANXIETY_PROPENSITY','ORDERLINESS','ALTRUISM','BRAVERY','CRUELTY',
         'DUTIFULNESS','FRIENDLINESS','STRESS_VULNERABILITY'})
    table.insert(result.limitations, 'Values are explicit personal entries; cultural defaults are not resolved.')
    for _, reference in ipairs(result.references) do
        if reference.kind == 'historical_figure' and reference.status == 'resolved' then
            table.insert(result.figures, {id=reference.id, name=reference.details.name})
        end
    end
    table.insert(result.limitations, 'Only resolved typed references may supply names; unsupported types remain unresolved.')
    table.insert(result.limitations, 'Reference lookups are capped at 160 per profile with depth 2; no world scans.')
    table.insert(result.limitations, 'Storytelling enrichment is capped at 8 incidents and 4 performers per incident; office definition lookup visits at most 128 entries. Historical election sites are not inferred from current assignments.')
    table.insert(result.limitations, 'Memory year/tick can indicate last use, not the original event date.')
    table.insert(result.limitations, 'Relationship links describe the current state, not necessarily the state at an event.')
    return result
end

if dfhack_flags.module then return end
local unit = dfhack.gui.getSelectedUnit(true)
if not unit then print('The Lorekeeper: no unit is selected.'); return end
local profile = capture(unit)
print('The Lorekeeper: on-demand profile for ' .. dfhack.units.getReadableName(unit, true))
print(('  indexed historical events: %d (%s)'):format(#profile.historical_events.events,
    profile.historical_events.coverage.status))
for _, name in ipairs({'emotions','shortterm_memories','longterm_memories',
        'core_memories','values','needs','preferences','relationships','friends'}) do
    print(('  %s: %d entries (memory sections may include empty slots)'):format(name, #profile[name]))
end
local names = {}
for _, figure in ipairs(profile.figures) do names[figure.id] = figure.name end
for _, link in ipairs(profile.relationships) do
    if link.target_hf then
        print(('  relationship: %s -> %s [HF %d]'):format(link.kind,
            dfhack.utf2df(names[link.target_hf] or 'unresolved'), link.target_hf))
    end
end
for _, friend in ipairs(profile.friends) do
    print(('  %s: %s [HF %s; current, directional]'):format(friend.kind,
        dfhack.utf2df(friend.target_name or 'unresolved'),tostring(friend.target_hf)))
end
for _, reference in ipairs(profile.references) do
    local details = reference.details or {}
    print(('  reference: %s [%s] %s'):format(reference.key, reference.status,
        dfhack.utf2df(details.name or details.victim_name or '')))
end
for _, limitation in ipairs(profile.limitations) do print('  Note: ' .. limitation) end
