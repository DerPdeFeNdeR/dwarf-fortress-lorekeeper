-- Queue a selected dwarf's grouped history for asynchronous Codex storytelling.
--
-- Run: lorekeeper/story

local json = require('json')
local snapshot = reqscript('lorekeeper/snapshot')
local history = reqscript('lorekeeper/history')

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

local records, history_error = history.load_snapshots(snapshot_data.identity.id)
if not records then
    print(('The Lorekeeper: could not load history: %s'):format(history_error))
    return
end
if #records == 0 then
    print(('The Lorekeeper: no recorded history for %s.'):format(
        snapshot_data.identity.name))
    return
end

local story_input = history.build_story_input(records)
local queue_path, path_error = get_queue_path()
if not queue_path then
    print(('The Lorekeeper: could not queue story: %s'):format(path_error))
    return
end

local ok, encoded_input = pcall(json.encode, story_input, {pretty=false})
if not ok then
    print(('The Lorekeeper: could not encode story request: %s'):format(
        tostring(encoded_input)))
    return
end

local latest_time = records[#records].ingame_time
local request_id = ('dwarf-history-v2:%d:%d:%d'):format(
    snapshot_data.identity.id, latest_time.year, latest_time.year_tick)
local request_record = {
    id=request_id,
    kind='dwarf_history',
    raw=encoded_input,
    context='Write a concise, factual Dwarf Fortress history for this dwarf from the supplied timeline. Use only supplied events. Do not invent names, causes, relationships, or events. Mention uncertainty when the timeline is sparse. Return a readable story, not a data summary.',
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

print(('The Lorekeeper: queued history story for %s.'):format(
    dfhack.utf2df(snapshot_data.identity.name)))
print(('  events: %d'):format(#story_input.events))
print(('  queue: %s'):format(queue_path))
print('  run helper/process_queue.py, then use the cached result for display')
