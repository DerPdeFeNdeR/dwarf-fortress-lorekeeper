-- Efficient background collector for fortress citizen snapshots.
--
-- Run: lorekeeper/collect start|stop|status
--@module = true

local snapshot = reqscript('lorekeeper/snapshot')
local history = reqscript('lorekeeper/history')
local policy = reqscript('lorekeeper/policy')

local CHECK_INTERVAL_TICKS = 100
local UNITS_PER_BATCH = 12
local MIN_RECORD_INTERVAL_TICKS = 1200
local STATE_KEY = 'lorekeeper.collect'

active = active or false
initializing = initializing or false
timer_id = timer_id or nil
state = state or {
    signatures={},
    units={},
    next_unit_index=1,
    scan_in_progress=false,
    scanned=0,
    recorded=0,
    last_recorded_ticks={},
    last_scan_tick=nil,
}
state.last_recorded_ticks = state.last_recorded_ticks or {}

local function current_time_key()
    return df.global.cur_year * 403200 + df.global.cur_year_tick
end

local function citizen_ids()
    local ids = {}
    for _, unit in ipairs(dfhack.units.getCitizens()) do table.insert(ids, unit.id) end
    return ids
end

local function clear_scan()
    state.units = {}
    state.next_unit_index = 1
    state.scan_in_progress = false
end

local function count_entries(entries)
    local count = 0
    for _ in pairs(entries) do
        count = count + 1
    end
    return count
end

local function stop_timer()
    if timer_id and dfhack.timeout_active(timer_id) then
        dfhack.timeout_active(timer_id, nil)
    end
    timer_id = nil
end

local function stop_collection()
    active = false
    initializing = false
    stop_timer()
    clear_scan()
end

local scan_batch
local function run_scan_batch()
    if not active or not dfhack.isWorldLoaded() then
        return
    end

    local processed = 0
    local changed_snapshots = {}
    local changed_signatures = {}
    while processed < UNITS_PER_BATCH and state.next_unit_index <= #state.units do
        local candidate = state.units[state.next_unit_index]
        local unit = candidate and df.unit.find(candidate)
        state.next_unit_index = state.next_unit_index + 1
        processed = processed + 1
        state.scanned = state.scanned + 1

        local snapshot_data = snapshot.capture(unit)
        if snapshot_data then
            local dwarf_id = snapshot_data.identity.id
            local current_signature = history.signature(snapshot_data)
            local last_recorded_tick = state.last_recorded_ticks[dwarf_id]
            if policy.should_record(
                    state.signatures[dwarf_id],
                    current_signature,
                    last_recorded_tick,
                    current_time_key(),
                    MIN_RECORD_INTERVAL_TICKS) then
                table.insert(changed_snapshots, snapshot_data)
                changed_signatures[dwarf_id] = current_signature
            end
        end
    end

    if #changed_snapshots > 0 then
        local _, appended, error_message = history.append_snapshots(changed_snapshots, true)
        if appended then
            for dwarf_id, current_signature in pairs(changed_signatures) do
                state.signatures[dwarf_id] = current_signature
                state.last_recorded_ticks[dwarf_id] = current_time_key()
            end
            state.recorded = state.recorded + #changed_snapshots
        elseif error_message then
            print(('The Lorekeeper: collector write failed: %s'):format(error_message))
        end
    end

    if state.next_unit_index <= #state.units then
        timer_id = dfhack.timeout(1, 'ticks', scan_batch)
        return
    end

    state.last_scan_tick = {
        year=df.global.cur_year,
        year_tick=df.global.cur_year_tick,
    }
    clear_scan()
    timer_id = dfhack.timeout(CHECK_INTERVAL_TICKS, 'ticks', function()
        if active then
            state.units = citizen_ids()
            state.scan_in_progress = true
            timer_id = dfhack.timeout(1, 'ticks', scan_batch)
        end
    end)
end

scan_batch = function()
    local ok, err = pcall(run_scan_batch)
    if not ok then
        stop_collection()
        print('The Lorekeeper: collector stopped after an error: ' .. tostring(err))
    end
end

local function start_collection()
    if active or initializing then
        print('The Lorekeeper: collector is already running.')
        return
    end

    if not dfhack.isMapLoaded() or df.global.gamemode ~= df.game_mode.DWARF then
        print('The Lorekeeper: cannot start collector without a loaded fortress map.')
        return
    end

    initializing = true
    local generation = {}
    state.initialization = generation
    local loader = coroutine.create(function()
        local count = 0
        local signatures, err = history.load_latest_signatures(function()
            count = count + 1
            if count % 16 == 0 then coroutine.yield() end
        end)
        if not signatures then error(err) end
        state.signatures = signatures
        state.scanned = 0
        state.recorded = 0
        initializing = false
        active = true
        state.units = citizen_ids()
        timer_id = dfhack.timeout(1, 'ticks', scan_batch)
        print(('The Lorekeeper: collector started for %d citizens.'):format(#state.units))
    end)
    local function resume_loading()
        if not initializing or state.initialization ~= generation then return end
        local ok, err = coroutine.resume(loader)
        if not ok then
            stop_collection()
            print('The Lorekeeper: initialization failed: ' .. tostring(err))
        elseif coroutine.status(loader) ~= 'dead' then
            timer_id = dfhack.timeout(1, 'frames', resume_loading)
        end
    end
    timer_id = dfhack.timeout(1, 'frames', resume_loading)
    print('The Lorekeeper: initializing collector history.')
end

local function print_status()
    print(('The Lorekeeper: collector %s.'):format(initializing and 'initializing' or (active and 'running' or 'stopped')))
    print(('  scanned: %d'):format(state.scanned))
    print(('  recorded: %d'):format(state.recorded))
    print(('  cached_signatures: %d'):format(count_entries(state.signatures)))
    if state.last_scan_tick then
        print(('  last_scan: year %d, tick %d'):format(
            state.last_scan_tick.year,
            state.last_scan_tick.year_tick))
    end
end

dfhack.onStateChange[STATE_KEY] = function(change)
    if change == SC_WORLD_UNLOADED or change == SC_MAP_UNLOADED then
        stop_collection()
        state.signatures = {}
        state.last_recorded_ticks = {}
        state.last_scan_tick = nil
        state.scanned = 0
        state.recorded = 0
    end
end

local command = ({...})[1] or 'status'
if not dfhack_flags.module then
    if command == 'start' then
        start_collection()
    elseif command == 'stop' then
        stop_collection()
        print('The Lorekeeper: collector stopped.')
    elseif command == 'status' then
        print_status()
    else
        print('Usage: lorekeeper/collect start|stop|status')
    end
end
