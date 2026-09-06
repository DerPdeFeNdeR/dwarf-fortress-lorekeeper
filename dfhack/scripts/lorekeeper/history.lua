-- JSONL history persistence for The Lorekeeper.
--@module = true

local json = require('json')

local function append_signature_value(parts, value)
    table.insert(parts, tostring(value))
end

local function snapshot_signature(snapshot_data)
    local parts = {}
    local identity = snapshot_data.identity
    append_signature_value(parts, identity.id)
    append_signature_value(parts, identity.name)
    append_signature_value(parts, identity.race)
    append_signature_value(parts, identity.caste)
    append_signature_value(parts, identity.profession)
    append_signature_value(parts, identity.citizen)
    append_signature_value(parts, snapshot_data.soul_present)
    append_signature_value(parts, snapshot_data.mental_state.stress)

    for _, thought in ipairs(snapshot_data.thoughts) do
        append_signature_value(parts, thought.thought_id)
        append_signature_value(parts, thought.emotion_id)
        append_signature_value(parts, thought.severity)
        append_signature_value(parts, thought.relative_strength)
        append_signature_value(parts, thought.subthought)
    end

    for _, facet in ipairs(snapshot_data.personality_facets) do
        append_signature_value(parts, facet.facet_id)
        append_signature_value(parts, facet.value)
    end

    return table.concat(parts, '\31')
end

local function get_latest_snapshot(path, dwarf_id)
    local file = io.open(path, 'r')
    if not file then
        return nil
    end

    local latest_snapshot
    for line in file:lines() do
        local ok, record = pcall(json.decode, line)
        if ok and record and record.record_type == 'dwarf_snapshot' and
                record.snapshot and record.snapshot.identity and
                record.snapshot.identity.id == dwarf_id then
            latest_snapshot = record.snapshot
        end
    end

    file:close()
    return latest_snapshot
end

local function get_history_path()
    if not dfhack.isWorldLoaded() then
        return nil, 'no world is loaded'
    end

    local save_path = dfhack.getSavePath()
    if not dfhack.filesystem.mkdir_recursive(save_path) and
            not dfhack.filesystem.isdir(save_path) then
        return nil, ('could not create save directory: %s'):format(save_path)
    end

    return save_path .. '/lorekeeper-history.jsonl'
end

function get_path()
    return get_history_path()
end

function append_snapshot(snapshot_data)
    local path, path_error = get_history_path()
    if not path then
        return nil, path_error
    end

    local latest_snapshot = get_latest_snapshot(path, snapshot_data.identity.id)
    if latest_snapshot and
            snapshot_signature(latest_snapshot) == snapshot_signature(snapshot_data) then
        return path, false
    end

    local record = {
        schema_version=1,
        record_type='dwarf_snapshot',
        captured_at=os.date('!%Y-%m-%dT%H:%M:%SZ'),
        ingame_time={
            year=df.global.cur_year,
            year_tick=df.global.cur_year_tick,
        },
        snapshot=snapshot_data,
    }

    local file, open_error = io.open(path, 'a')
    if not file then
        return nil, ('could not open %s: %s'):format(path, tostring(open_error))
    end

    local ok, encoded_or_error = pcall(json.encode, record, {pretty=false})
    if not ok then
        file:close()
        return nil, ('could not encode history record: %s'):format(tostring(encoded_or_error))
    end

    local write_ok, write_error = file:write(encoded_or_error, '\n')
    file:close()
    if not write_ok then
        return nil, ('could not write %s: %s'):format(path, tostring(write_error))
    end

    return path, true
end
