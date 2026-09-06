-- Start Lorekeeper's collector whenever a fortress is loaded.
--
-- Load this script once from dfhack.init:
--   lorekeeper/autostart

local STATE_KEY = 'lorekeeper.autostart'

local function start_collector()
    if dfhack.isMapLoaded() and df.global.gamemode == df.game_mode.DWARF then
        dfhack.run_command('lorekeeper/collect start')
    end
end

dfhack.onStateChange[STATE_KEY] = function(change)
    if change == SC_MAP_LOADED then
        start_collector()
    end
end

-- Support loading the startup script after a world is already active.
start_collector()
