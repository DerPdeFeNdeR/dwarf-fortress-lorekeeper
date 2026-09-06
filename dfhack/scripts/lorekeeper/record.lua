-- Append one selected-dwarf snapshot to the fortress history JSONL file.
--
-- Run with a unit selected: lorekeeper/record

local snapshot = reqscript('lorekeeper/snapshot')
local history = reqscript('lorekeeper/history')

local snapshot_data = snapshot.capture_selected_unit()
if not snapshot_data then
    print('The Lorekeeper: no unit is currently selected.')
    return
end

local path, appended, error_message = history.append_snapshot(snapshot_data)
if not path then
    print(('The Lorekeeper: could not record snapshot: %s'):format(error_message))
    return
end

if appended then
    print(('The Lorekeeper: recorded %s to %s'):format(
        snapshot_data.identity.name,
        path))
else
    print(('The Lorekeeper: no changes for %s; history record skipped.'):format(
        snapshot_data.identity.name))
end
