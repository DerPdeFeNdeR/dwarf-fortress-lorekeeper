-- JSONL history persistence for The Lorekeeper.
--@module = true

local json = require('json')

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

    return path
end
