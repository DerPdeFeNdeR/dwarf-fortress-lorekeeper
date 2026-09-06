-- Read cached model translations for The Lorekeeper.
--@module = true

local json = require('json')

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

    local prefix = ('dwarf-history:%d:'):format(unit_id)
    local latest_time
    local latest_result
    for request_id, result in pairs(cache) do
        if type(request_id) == 'string' and request_id:sub(1, #prefix) == prefix and
                type(result) == 'table' then
            local year, year_tick = request_id:match('^dwarf%-history:%d+:(%d+):(%d+)$')
            local time = year and tonumber(year) * 1000000 + tonumber(year_tick)
            if time and (not latest_time or time > latest_time) then
                latest_time = time
                latest_result = result
            end
        end
    end

    return latest_result
end

function get_cache_path_for_display()
    return get_cache_path()
end
