-- Read cached model translations for The Lorekeeper.
--@module = true

local json = require('json')

local function decode_queue_line(line)
    local ok, record = pcall(json.decode, line)
    if ok then
        return record
    end
    local converted_ok, converted_record = pcall(json.decode, dfhack.df2utf(line))
    if converted_ok then
        return converted_record
    end
    return nil
end

local function get_cache_path()
    if not dfhack.isWorldLoaded() then
        return nil, 'no world is loaded'
    end

    return dfhack.getSavePath() .. '/lorekeeper-translation-cache.json'
end

local function load_cache()
    local path, path_error = get_cache_path()
    if not path then
        return nil, path_error
    end

    local file = io.open(path, 'r')
    if not file then
        return {}, path
    end

    local contents = file:read('*a')
    file:close()
    if not contents or contents == '' then
        return {}, path
    end

    local ok, cache = pcall(json.decode, contents)
    if not ok or type(cache) ~= 'table' then
        return nil, ('could not decode translation cache: %s'):format(path)
    end

    return cache, path
end

function get_latest_summary(unit_id)
    local cache = load_cache()
    if not cache then
        return nil
    end

    local prefix = ('dwarf-summary:%d:'):format(unit_id)
    local latest_tick
    local latest_result
    for request_id, result in pairs(cache) do
        if type(request_id) == 'string' and request_id:sub(1, #prefix) == prefix and
                type(result) == 'table' then
            local tick = tonumber(request_id:sub(#prefix + 1))
            if tick and (not latest_tick or tick > latest_tick) then
                latest_tick = tick
                latest_result = result
            end
        end
    end

    return latest_result
end

function get_latest_story(unit_id)
    local cache = load_cache()
    if not cache then
        return nil
    end

    local prefix = ('dwarf-history-v2:%d:'):format(unit_id)
    local latest_time
    local latest_result
    for request_id, result in pairs(cache) do
        if type(request_id) == 'string' and request_id:sub(1, #prefix) == prefix and
                type(result) == 'table' then
            local year, year_tick = request_id:match(
                '^dwarf%-history%-v%d+:%d+:(%d+):(%d+)$')
            local time = year and tonumber(year) * 1000000 + tonumber(year_tick)
            if time and (not latest_time or time > latest_time) then
                latest_time = time
                latest_result = result
            end
        end
    end

    return latest_result
end

function get_story_status(unit_id, ingame_time)
    local request_id = ('dwarf-history-v2:%d:%d:%d'):format(
        unit_id, ingame_time.year, ingame_time.year_tick)
    local cache = load_cache()
    if cache and type(cache[request_id]) == 'table' then
        return 'ready', cache[request_id]
    end

    if not dfhack.isWorldLoaded() then
        return 'missing', nil
    end
    local queue_path = dfhack.getSavePath() .. '/lorekeeper-translation-queue.jsonl'
    local file = io.open(queue_path, 'r')
    if file then
        for line in file:lines() do
            local record = decode_queue_line(line)
            if record and record.id == request_id then
                file:close()
                return 'pending', nil
            end
        end
        file:close()
    end

    return 'missing', nil
end

function get_cache_path_for_display()
    return get_cache_path()
end
