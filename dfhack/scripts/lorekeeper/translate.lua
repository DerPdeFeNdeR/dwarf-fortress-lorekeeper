-- Queue a selected dwarf for asynchronous Codex explanation.
--
-- Run: lorekeeper/translate

local json = require('json')
local snapshot = reqscript('lorekeeper/snapshot')

local function get_queue_path()
    if not dfhack.isWorldLoaded() then
        return nil, 'no world is loaded'
    end

    local save_path = dfhack.getSavePath()
    if not dfhack.filesystem.mkdir_recursive(save_path) and
            not dfhack.filesystem.isdir(save_path) then
        return nil, ('could not create save directory: %s'):format(save_path)
    end

    return save_path .. '/lorekeeper-translation-queue.jsonl'
end

local snapshot_data = snapshot.capture_selected_unit()
if not snapshot_data then
    print('The Lorekeeper: no unit is currently selected.')
    return
end

local queue_path, path_error = get_queue_path()
if not queue_path then
    print(('The Lorekeeper: could not queue translation: %s'):format(path_error))
    return
end

local ok, encoded_snapshot = pcall(json.encode, snapshot_data, {pretty=false})
if not ok then
    print(('The Lorekeeper: could not encode translation request: %s'):format(
        tostring(encoded_snapshot)))
    return
end

local request_id = ('dwarf-summary:%d:%d'):format(
    snapshot_data.identity.id,
    df.global.cur_year_tick)
local request_record = {
    id=request_id,
    kind='dwarf_summary',
    raw=encoded_snapshot,
    context='Explain this Dwarf Fortress dwarf summary using only the supplied structured data.',
    language='en',
}

local file, open_error = io.open(queue_path, 'a')
if not file then
    print(('The Lorekeeper: could not open translation queue: %s'):format(
        tostring(open_error)))
    return
end

local encoded_request = json.encode(request_record, {pretty=false})
local write_ok, write_error = file:write(encoded_request, '\n')
file:close()
if not write_ok then
    print(('The Lorekeeper: could not write translation queue: %s'):format(
        tostring(write_error)))
    return
end

print(('The Lorekeeper: queued %s for Codex translation.'):format(
    snapshot_data.identity.name))
print(('  queue: %s'):format(queue_path))
print('  run helper/process_queue.py, then refresh lorekeeper/show')
