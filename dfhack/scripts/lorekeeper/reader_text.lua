-- Player-facing reader states; no game collection or filesystem access.
--@module = true
local display = reqscript('lorekeeper/display_text')

function pending(data, requested)
    if not requested then return false end
    local prepared = data and data.request
    return not prepared or prepared.nonce ~= requested.nonce or
        prepared.year ~= requested.year or prepared.tick ~= requested.tick or
        prepared.unit_id ~= requested.unit_id or data.state == 'processing'
end

function status(data, requested, available, request_error)
    if request_error then return 'Could not request an update. See Details.' end
    if not available then return 'Historian offline. Saved biographies are still readable.' end
    if pending(data, requested) then
        return data and data.story and 'Updating biography. The previous version is shown below.' or
            'The historian is preparing this biography...'
    end
    if data and data.state == 'failed' then return 'The update failed. Try Update or see Details.' end
    if data and data.state == 'empty' then return 'No recorded history yet.' end
    return 'Saved biography. Choose Update to include newer experiences.'
end

function lines(data, width)
    if data and data.story and data.story ~= '' then return display.wrap(data.story, width) end
    return display.wrap('This dwarf\'s biography will appear here when it is ready.\n\n' ..
        'You can close this window and keep playing. There is no need to wait here.', width)
end
