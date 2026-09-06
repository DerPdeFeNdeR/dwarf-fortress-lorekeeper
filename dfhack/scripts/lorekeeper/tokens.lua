-- Export token names from the active DF/DFHack runtime.
--
-- Run: lorekeeper/tokens
-- Copy to the system clipboard: lorekeeper/tokens copy

local function append_enum(lines, title, enum)
    table.insert(lines, title)
    if not enum then
        table.insert(lines, '  <not available in this DFHack build>')
        return
    end

    for id, name in ipairs(enum) do
        table.insert(lines, ('  %d = %s'):format(id, name))
    end
end

local function append_syndromes(lines)
    table.insert(lines, 'world_syndromes')
    if not dfhack.isWorldLoaded() then
        table.insert(lines, '  <no world loaded>')
        return
    end

    local syndromes = df.global.world.raws.mat_table.syndromes.all
    if not syndromes or #syndromes == 0 then
        table.insert(lines, '  <none>')
        return
    end

    for id, syndrome in ipairs(syndromes) do
        if syndrome.syn_name and syndrome.syn_name ~= '' then
            table.insert(lines, ('  %d = %s'):format(id, syndrome.syn_name))
        end
    end
end

local function build_catalog()
    local lines = {
        '# The Lorekeeper token catalog',
        ('df_version = %s'):format(dfhack.getDFVersion()),
        ('dfhack_version = %s'):format(dfhack.getDFHackVersion()),
        '',
    }

    append_enum(lines, 'thought_types', df.unit_thought_type)
    table.insert(lines, '')
    append_enum(lines, 'emotion_types', df.emotion_type)
    table.insert(lines, '')
    append_enum(lines, 'personality_facets', df.personality_facet_type)
    table.insert(lines, '')
    append_syndromes(lines)

    return lines
end

local lines = build_catalog()
local output = table.concat(lines, '\n')
print(output)

if ({...})[1] == 'copy' then
    dfhack.internal.setClipboardTextCp437Multiline(output)
    dfhack.gui.showAnnouncement('Lorekeeper token catalog copied to clipboard.', COLOR_LIGHTGREEN)
end
