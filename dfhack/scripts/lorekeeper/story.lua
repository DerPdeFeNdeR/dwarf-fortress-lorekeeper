-- Queue a small history request for the external watcher.
local unit = dfhack.gui.getSelectedUnit(true)
if not unit then print('The Lorekeeper: no unit is selected.'); return end
local ok, err = reqscript('lorekeeper/view_request').request(unit.id)
if not ok then
    print('The Lorekeeper: request failed: ' .. tostring(err))
else
    print('The Lorekeeper: history requested. Open lorekeeper/history/show to read it.')
end
