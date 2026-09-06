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

function request(unit_id)
    local path = directory()
    if not dfhack.filesystem.mkdir_recursive(path) and not dfhack.filesystem.isdir(path) then
        return nil, 'could not create history request directory'
    end
    local nonce = os.time()
    local target = ('%s/%d.%d.%d.%d.request.json'):format(path, unit_id,
        df.global.cur_year, df.global.cur_year_tick, nonce)
    local existing = io.open(target, 'r')
    if existing then existing:close(); return true end
    local file, err = io.open(target .. '.tmp', 'w')
    if not file then return nil, err end
    local ok, write_error = file:write(json.encode({unit_id=unit_id,
        year=df.global.cur_year, tick=df.global.cur_year_tick, nonce=nonce}, {pretty=false}))
    file:close()
    if not ok then return nil, write_error end
    local renamed, rename_error = os.rename(target .. '.tmp', target)
    return renamed, rename_error
end
