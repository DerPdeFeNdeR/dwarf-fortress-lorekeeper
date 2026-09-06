-- JSONL history persistence for The Lorekeeper.
--@module = true

local json = require('json')
local get_history_path
local STRESS_SIGNATURE_BAND = 500

local function append_signature_value(parts, value)
    table.insert(parts, tostring(value))
end

local function decode_record(line)
    local ok, record = pcall(json.decode, line)
    if ok then
        return record
    end

    local converted_line = dfhack.df2utf(line)
    local converted_ok, converted_record = pcall(json.decode, converted_line)
    if converted_ok then
        return converted_record
    end

    return nil
end

local function get_history_index_directory()
    local history_path, path_error = get_history_path()
    if not history_path then
        return nil, path_error
    end

    local index_directory = history_path:gsub('/lorekeeper%-history%.jsonl$',
        '/lorekeeper-history-index')
    if not dfhack.filesystem.mkdir_recursive(index_directory) and
            not dfhack.filesystem.isdir(index_directory) then
        return nil, ('could not create history index directory: %s'):format(index_directory)
    end

    return index_directory
end

local function get_history_index_path(dwarf_id)
    local index_directory, path_error = get_history_index_directory()
    if not index_directory then
        return nil, path_error
    end
    return ('%s/%d.jsonl'):format(index_directory, dwarf_id)
end

local function read_snapshot_records(path, dwarf_id)
    local records = {}
    local file = io.open(path, 'r')
    if not file then
        return records
    end

    for line in file:lines() do
        local record = decode_record(line)
        if record and record.record_type == 'dwarf_snapshot' and
                record.snapshot and record.snapshot.identity and
                record.snapshot.identity.id == dwarf_id then
            table.insert(records, record)
        end
    end

    file:close()
    return records
end

local function build_history_indexes(history_path, index_directory)
    local source = io.open(history_path, 'r')
    if not source then
        local marker = io.open(index_directory .. '/.complete', 'w')
        if marker then marker:close() end
        return true
    end

    local index_files = {}
    for line in source:lines() do
        local record = decode_record(line)
        if record and record.record_type == 'dwarf_snapshot' and
                record.snapshot and record.snapshot.identity and
                record.snapshot.identity.id then
            local dwarf_id = record.snapshot.identity.id
            local index = index_files[dwarf_id]
            if not index then
                local index_path = ('%s/%d.jsonl'):format(index_directory, dwarf_id)
                index = io.open(index_path, 'w')
                if not index then
                    source:close()
                    for _, open_index in pairs(index_files) do
                        open_index:close()
                    end
                    return nil
                end
                index_files[dwarf_id] = index
            end
            index:write(line, '\n')
        end
    end

    source:close()
    for _, index in pairs(index_files) do
        index:close()
    end

    local marker = io.open(index_directory .. '/.complete', 'w')
    if not marker then
        return nil
    end
    marker:close()
    return true
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
    local stress = snapshot_data.mental_state.stress
    append_signature_value(parts, stress and (stress // STRESS_SIGNATURE_BAND) or 'none')

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
        local record = decode_record(line)
        if record and record.record_type == 'dwarf_snapshot' and
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
        local record = decode_record(line)
        if record and record.record_type == 'dwarf_snapshot' and
                record.snapshot and record.snapshot.identity then
            signatures[record.snapshot.identity.id] = signature(record.snapshot)
        end
    end

    file:close()
    return signatures, path
end

function load_snapshots(dwarf_id)
    local path, path_error = get_history_path()
    if not path then
        return nil, path_error
    end

    local index_directory, index_error = get_history_index_directory()
    if not index_directory then
        return nil, index_error
    end

    local index_path = ('%s/%d.jsonl'):format(index_directory, dwarf_id)
    local marker = io.open(index_directory .. '/.complete', 'r')
    if not marker then
        if not build_history_indexes(path, index_directory) then
            return nil, ('could not build history index: %s'):format(index_directory)
        end
    else
        marker:close()
    end

    local existing_index = io.open(index_path, 'r')
    if existing_index then
        existing_index:close()
        local records = read_snapshot_records(index_path, dwarf_id)
        return records, path
    end

    return {}, path
end

local function count_thoughts(snapshot_data)
    local counts = {}
    for _, thought in ipairs(snapshot_data.thoughts) do
        local key = table.concat({tostring(thought.thought_id), tostring(thought.emotion_id)}, ':')
        counts[key] = (counts[key] or 0) + 1
    end
    return counts
end

local function count_differences(previous_counts, current_counts)
    local added = 0
    local removed = 0
    for key, count in pairs(current_counts) do
        added = added + math.max(0, count - (previous_counts[key] or 0))
    end
    for key, count in pairs(previous_counts) do
        removed = removed + math.max(0, count - (current_counts[key] or 0))
    end
    return added, removed
end

function describe_changes(previous_snapshot, current_snapshot)
    local changes = {}
    if previous_snapshot.identity.profession ~= current_snapshot.identity.profession then
        table.insert(changes, ('profession changed from %s to %s'):format(
            previous_snapshot.identity.profession, current_snapshot.identity.profession))
    end

    local previous_stress = previous_snapshot.mental_state.stress
    local current_stress = current_snapshot.mental_state.stress
    if previous_stress and current_stress and previous_stress ~= current_stress then
        table.insert(changes, ('stress changed from %d to %d'):format(
            previous_stress, current_stress))
    end

    local added_thoughts, removed_thoughts = count_differences(
        count_thoughts(previous_snapshot), count_thoughts(current_snapshot))
    if added_thoughts > 0 or removed_thoughts > 0 then
        table.insert(changes, ('thoughts changed: %d added, %d removed'):format(
            added_thoughts, removed_thoughts))
    end

    local previous_facets = {}
    for _, facet in ipairs(previous_snapshot.personality_facets) do
        previous_facets[facet.facet_id] = facet.value
    end
    local changed_facets = 0
    for _, facet in ipairs(current_snapshot.personality_facets) do
        if previous_facets[facet.facet_id] ~= facet.value then
            changed_facets = changed_facets + 1
        end
    end
    if changed_facets > 0 then
        table.insert(changes, ('personality facets changed: %d'):format(changed_facets))
    end

    return changes
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

    local index_files = {}
    local index_directory = get_history_index_directory()
    local index_marker = index_directory and io.open(index_directory .. '/.complete', 'r')
    if index_marker then index_marker:close() end
    for _, record in ipairs(records) do
        local dwarf_id = record.snapshot.identity.id
        local index_path = get_history_index_path(dwarf_id)
        if index_path and not index_files[dwarf_id] then
            local existing_index = io.open(index_path, 'r')
            if existing_index then
                existing_index:close()
                index_files[dwarf_id] = io.open(index_path, 'a')
            elseif index_marker then
                index_files[dwarf_id] = io.open(index_path, 'a')
            end
        end
    end

    for _, record in ipairs(records) do
        local ok, encoded_or_error = pcall(json.encode, record, {pretty=false})
        if not ok then
            file:close()
            for _, index_file in pairs(index_files) do
                if index_file then index_file:close() end
            end
            return nil, false, ('could not encode history record: %s'):format(tostring(encoded_or_error))
        end

        local write_ok, write_error = file:write(encoded_or_error, '\n')
        if not write_ok then
            file:close()
            for _, index_file in pairs(index_files) do
                if index_file then index_file:close() end
            end
            return nil, false, ('could not write %s: %s'):format(path, tostring(write_error))
        end

        local index_file = index_files[record.snapshot.identity.id]
        if index_file then
            index_file:write(encoded_or_error, '\n')
        end
    end

    file:close()
    for _, index_file in pairs(index_files) do
        if index_file then index_file:close() end
    end
    return path, true
end

function append_snapshot(snapshot_data, skip_file_deduplication)
    return append_snapshots({snapshot_data}, skip_file_deduplication)
end

if not dfhack_flags.module then
    local snapshot = reqscript('lorekeeper/snapshot')
    local selected = snapshot.capture_selected_unit()
    if not selected then
        print('The Lorekeeper: no unit is currently selected.')
        return
    end

    local records, path_error = load_snapshots(selected.identity.id)
    if not records then
        print(('The Lorekeeper: could not read history: %s'):format(path_error))
        return
    end

    print(('The Lorekeeper: history for %s'):format(
        dfhack.utf2df(selected.identity.name)))
    print(('  records: %d'):format(#records))
    if #records == 0 then
        print('  No recorded history for this dwarf.')
        return
    end

    for index, record in ipairs(records) do
        local time = record.ingame_time
        local snapshot_data = record.snapshot
        print(('  [%d] year %d, tick %d; stress %s; thoughts %d'):format(
            index, time.year, time.year_tick,
            tostring(snapshot_data.mental_state.stress or '<none>'),
            #snapshot_data.thoughts))
        if index > 1 then
            for _, change in ipairs(describe_changes(records[index - 1].snapshot, snapshot_data)) do
                print('      - ' .. change)
            end
        end
    end
end
