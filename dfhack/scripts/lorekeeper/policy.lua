-- Pure collection decisions for The Lorekeeper.
--@module = true

function should_record(previous_signature, current_signature,
        last_recorded_tick, current_tick, minimum_interval_ticks)
    if previous_signature == current_signature then
        return false
    end

    if not last_recorded_tick then
        return true
    end

    return current_tick < last_recorded_tick or
        current_tick - last_recorded_tick >= minimum_interval_ticks
end
