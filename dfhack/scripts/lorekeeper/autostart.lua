-- Start Lorekeeper's collector whenever a fortress is loaded.
--
-- Load this script once from dfhack.init:
--   lorekeeper/autostart

local STATE_KEY = 'lorekeeper.autostart'

local function start_collector()
    if dfhack.isWorldLoaded() then
        dfhack.run_command_silent('lorekeeper/collect start')
    end
end

dfhack.onStateChange[STATE_KEY] = function(change)
    if change == SC_WORLD_LOADED then
        start_collector()
    end
end

-- Support loading the startup script after a world is already active.
start_collector()
