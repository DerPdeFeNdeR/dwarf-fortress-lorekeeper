-- Small file protocol for external history preparation.
--@module = true
local json = require('json')

local function directory()
    return dfhack.getSavePath() .. '/lorekeeper-views'
end

function worker_available()
    local file = io.open(dfhack.getSavePath() .. '/../lorekeeper-worker.json', 'r')
    if not file then return false end
    local contents = file:read(4096)
    file:close()
    local ok, value = pcall(json.decode, contents)
    return ok and type(value.updated_at) == 'number' and os.time() - value.updated_at < 30
end

function read(unit_id, page, revision)
    local suffix = page and ('.' .. revision .. '.' .. page) or ''
    local file = io.open(directory() .. '/' .. unit_id .. suffix .. '.json', 'r')
    if not file then return nil end
    local contents = file:read(65537)
    file:close()
    if not contents or #contents > 65536 then return nil end
    local ok, value = pcall(json.decode, contents)
    if ok then return value end
end

function read_chapter(unit_id, filename)
    if type(filename) ~= 'string' or not filename:match('^' .. unit_id .. '%.monthly%.[a-f0-9]+%.json$') then
        return nil
    end
    local file = io.open(directory() .. '/' .. filename, 'r')
    if not file then return nil end
    local contents = file:read(65537)
    file:close()
    if not contents or #contents > 65536 then return nil end
    local ok, value = pcall(json.decode, contents)
    if ok then return value end
end

function read_profile(unit_id, filename)
    if type(filename) ~= 'string' or not filename:match('^' .. unit_id .. '%.%d+%.%d+%.%d+%.profile%.json$') then
        return nil
    end
    local file = io.open(directory() .. '/' .. filename, 'r')
    if not file then return nil end
    local contents = file:read(131073)
    file:close()
    if not contents or #contents > 131072 then return nil end
    local ok, value = pcall(json.decode, contents)
    if ok and type(value) == 'table' and value.unit_id == unit_id then return value end
end

function request(unit_id)
    local path = directory()
    if not dfhack.filesystem.mkdir_recursive(path) and not dfhack.filesystem.isdir(path) then
        return nil, 'could not create history request directory'
    end
    local nonce = os.time()
    local request_data = {unit_id=unit_id, year=df.global.cur_year,
        tick=df.global.cur_year_tick, nonce=nonce, monthly_version=1}
    local session=reqscript('lorekeeper/chronicle').runtime
    if session then
        request_data.environment=reqscript('lorekeeper/environment').reference(session,df.global.cur_year)
    end
    local target = ('%s/%d.%d.%d.%d.request.json'):format(path, unit_id,
        df.global.cur_year, df.global.cur_year_tick, nonce)
    local existing = io.open(target, 'r')
    if existing then existing:close(); return true, nil, request_data end
    -- Separate bounded profile from the tiny request/status protocol.
    local unit = df.unit.find(unit_id)
    local profile_name
    if unit then
        local captured, profile = pcall(function() return reqscript('lorekeeper/profile').capture(unit) end)
        if not captured then return nil, 'memoire capture failed: ' .. tostring(profile) end
        local encoded = json.encode(profile, {pretty=false})
        if #encoded > 131072 then return nil, 'memoire profile exceeds 128 KiB' end
        profile_name = ('%d.%d.%d.%d.profile.json'):format(unit_id,
            df.global.cur_year, df.global.cur_year_tick, nonce)
        local output, profile_error = io.open(path .. '/' .. profile_name, 'w')
        if not output then return nil, profile_error end
        local wrote, write_error = output:write(encoded)
        local closed, close_error = output:close()
        if not wrote or not closed then return nil, write_error or close_error end
    end
    local file, err = io.open(target .. '.tmp', 'w')
    if not file then return nil, err end
    request_data.profile_file = profile_name
    local ok, write_error = file:write(json.encode(request_data, {pretty=false}))
    file:close()
    if not ok then return nil, write_error end
    local renamed, rename_error = os.rename(target .. '.tmp', target)
    return renamed, rename_error, request_data
end
