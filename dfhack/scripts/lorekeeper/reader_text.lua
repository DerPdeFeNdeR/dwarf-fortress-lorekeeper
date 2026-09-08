-- Player-facing reader states; no game collection or filesystem access.
--@module = true
local display = reqscript('lorekeeper/display_text')

function selected_chapter(chapters, key)
    key = key or 'intro'
    for i,row in ipairs(chapters or {}) do
        if row.key == key then return row,i end
    end
    -- Do not jump away from the introduction as background results arrive.
    if key == 'intro' then return nil end
    return chapters and chapters[1],1
end

function pending(data, requested)
    if not requested then return false end
    local prepared = data and data.request
    return not prepared or prepared.nonce ~= requested.nonce or
        prepared.year ~= requested.year or prepared.tick ~= requested.tick or
        prepared.unit_id ~= requested.unit_id or data.state == 'processing'
end

function status(data, requested, available, request_error)
    if request_error then return 'Could not request an update. See Details.' end
    if not available then return 'Historian offline. Saved memoires are still readable.' end
    if pending(data, requested) then
        if data and data.monthly_version then
            return 'Writing monthly chapters in the background. Saved chapters remain readable.'
        end
        return data and data.story and 'Updating Memoire. The previous version is shown below.' or
            'Preparing this Memoire...'
    end
    if data and data.state == 'failed' then return 'The update failed. Press U to retry, or see Details.' end
    if data and data.biography_update and data.biography_update.mode=='defer' then
        return 'No significant new developments. Saved memoire unchanged.'
    end
    if data and data.state == 'empty' then return 'No recorded history yet.' end
    if data and data.monthly_version then
        return 'N/P: browse months and introduction. Update checks for important developments.'
    end
    if data and data.historical_event_coverage and data.historical_event_coverage.status=='building' then
        return 'Older events were still indexing. Choose Update to include newly indexed events.'
    end
    return 'Saved Memoire. Choose Update to include newer experiences.'
end

function lines(data, width)
    if data and data.story and data.story ~= '' then return display.wrap(data.story, width) end
    return display.wrap('This dwarf\'s memoire will appear here when it is ready.\n\n' ..
        'You can close this window and keep playing. There is no need to wait here.', width)
end

local function relationship_label(kind)
    kind = tostring(kind or 'connection'):lower()
    kind = kind:gsub('^<', ''):gsub('>$', '')
    kind = kind:gsub('^type:%s*', ''):gsub('^histfig%s+hf%s+link%s+', 'histfig_hf_link_')
    local labels = {
        histfig_hf_link_spousest='Spouse',
        histfig_hf_link_motherst='Mother',
        histfig_hf_link_fatherst='Father',
        histfig_hf_link_parentst='Parent',
        histfig_hf_link_grandparentst='Grandparent',
        histfig_hf_link_grandchildst='Grandchild',
        histfig_hf_link_childst='Child',
        histfig_hf_link_siblingst='Sibling',
        spouse='Spouse', mother='Mother', father='Father', parent='Parent',
        grandparent='Grandparent', grandchild='Grandchild', child='Child', sibling='Sibling',
        close_friend='Close friend', friend='Friend', kindred_spirit='Kindred spirit',
    }
    return labels[kind] or tostring(kind or 'connection'):gsub('^histfig_hf_link_', ''):gsub('st$', ''):gsub('_', ' ')
end

function relationship_lines(profile, width)
    if not profile then return {} end
    local rows = {}
    local seen = {}
    local function add(kind, name)
        if type(name) ~= 'string' or name == '' then return end
        local key = relationship_label(kind) .. '\0' .. name
        if seen[key] then return end
        seen[key] = true
        table.insert(rows, '- ' .. relationship_label(kind) .. ': ' .. name)
    end
    for _, row in ipairs(profile.relationships or {}) do add(row.kind, row.target_name) end
    for _, row in ipairs(profile.friends or {}) do add(row.kind, row.target_name) end
    if #rows == 0 then return {} end
    local result = {}
    for _, line in ipairs(display.wrap('Relationships', width)) do table.insert(result, line) end
    table.insert(result, '')
    for _, line in ipairs(rows) do
        for _, wrapped in ipairs(display.wrap(line, width)) do table.insert(result, wrapped) end
    end
    return result
end
