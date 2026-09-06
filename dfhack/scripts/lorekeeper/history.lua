-- JSONL history persistence for The Lorekeeper.
--@module = true

local json = require('json')
local get_history_path
local STRESS_SIGNATURE_BAND = 500

local function append_signature_value(parts, value)
    table.insert(parts, tostring(value))
end

function signature(snapshot_data)
    local parts = {}
    local identity = snapshot_data.identity
    append_signature_value(parts, identity.id)
    append_signature_value(parts, identity.name)
    append_signature_value(parts, identity.race)
    append_signature_value(parts, identity.caste)
    append_signature_value(parts, identity.profession)
    append_signature_value(parts, identity.citizen)
    append_signature_value(parts, snapshot_data.soul_present)
    append_signature_value(parts, snapshot_data.mental_state.stress // STRESS_SIGNATURE_BAND)

    local thought_counts = {}
    for _, thought in ipairs(snapshot_data.thoughts) do
        local thought_key = table.concat({
            tostring(thought.thought_id),
            tostring(thought.emotion_id),
            tostring(thought.severity),
            tostring(thought.relative_strength),
        }, ':')
        thought_counts[thought_key] = (thought_counts[thought_key] or 0) + 1
    end

    local thought_keys = {}
    for thought_key in pairs(thought_counts) do
        table.insert(thought_keys, thought_key)
    end
    table.sort(thought_keys)
    for _, thought_key in ipairs(thought_keys) do
        append_signature_value(parts, thought_key)
        append_signature_value(parts, thought_counts[thought_key])
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

function load_latest_signatures()
    local path, path_error = get_history_path()
    if not path then
        return nil, path_error
    end

    local signatures = {}
    local file = io.open(path, 'r')
    if not file then
        return signatures, path
    end

    for line in file:lines() do
        local ok, record = pcall(json.decode, line)
        if ok and record and record.record_type == 'dwarf_snapshot' and
                record.snapshot and record.snapshot.identity then
            signatures[record.snapshot.identity.id] = signature(record.snapshot)
        end
    end

    file:close()
    return signatures, path
end

function get_history_path()
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

function should_append(previous_snapshot, current_snapshot)
    return not previous_snapshot or
        signature(previous_snapshot) ~= signature(current_snapshot)
end

function append_snapshots(snapshot_data_list, skip_file_deduplication)
    local path, path_error = get_history_path()
    if not path then
        return nil, false, path_error
    end

    local records = {}
    for _, snapshot_data in ipairs(snapshot_data_list) do
        if not skip_file_deduplication then
            local latest_snapshot = get_latest_snapshot(path, snapshot_data.identity.id)
            if latest_snapshot and not should_append(latest_snapshot, snapshot_data) then
                goto continue
            end
        end

        table.insert(records, {
            schema_version=1,
            record_type='dwarf_snapshot',
            captured_at=os.date('!%Y-%m-%dT%H:%M:%SZ'),
            ingame_time={
                year=df.global.cur_year,
                year_tick=df.global.cur_year_tick,
            },
            snapshot=snapshot_data,
        })

        ::continue::
    end

    if #records == 0 then
        return path, false
    end

    local file, open_error = io.open(path, 'a')
    if not file then
        return nil, false, ('could not open %s: %s'):format(path, tostring(open_error))
    end

    for _, record in ipairs(records) do
        local ok, encoded_or_error = pcall(json.encode, record, {pretty=false})
        if not ok then
            file:close()
            return nil, false, ('could not encode history record: %s'):format(tostring(encoded_or_error))
        end

        local write_ok, write_error = file:write(encoded_or_error, '\n')
        if not write_ok then
            file:close()
            return nil, false, ('could not write %s: %s'):format(path, tostring(write_error))
        end
    end

    file:close()
    return path, true
end

function append_snapshot(snapshot_data, skip_file_deduplication)
    return append_snapshots({snapshot_data}, skip_file_deduplication)
end
