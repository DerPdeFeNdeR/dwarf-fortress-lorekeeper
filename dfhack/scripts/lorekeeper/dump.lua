-- Read-only selected-unit inspector for The Lorekeeper.
--
-- Install this repository's dfhack/scripts directory as a DFHack script path,
-- then run: lorekeeper/dump

local snapshot = reqscript('lorekeeper/snapshot')

local function print_thoughts(thoughts)
    print('  thoughts:')
    if #thoughts == 0 then
        print('    <none>')
        return
    end

    for index, thought in ipairs(thoughts) do
        print(('    [%d] thought=%s emotion=%s severity=%d relative_strength=%d subthought=%d'):format(
            index,
            thought.thought_name,
            thought.emotion_name,
            thought.severity,
            thought.relative_strength,
            thought.subthought))
    end
end

local function print_personality(snapshot_data)
    if not snapshot_data.soul_present then
        print('  soul: <none>')
        return
    end

    print('  soul: present')
    print(('  stress: %d'):format(snapshot_data.mental_state.stress))
    print('  personality_traits:')

    for _, facet in ipairs(snapshot_data.personality_facets) do
        print(('    %s=%d'):format(facet.facet_name, facet.value))
    end
end

local snapshot_data = snapshot.capture_selected_unit()
if not snapshot_data then
    print('The Lorekeeper: no unit is currently selected.')
    return
end

print('The Lorekeeper: selected unit')
print(('  df_version: %s'):format(snapshot_data.source.df_version))
print(('  dfhack_version: %s'):format(snapshot_data.source.dfhack_version))
print(('  id: %d'):format(snapshot_data.identity.id))
print(('  name: %s'):format(snapshot_data.identity.name))
print(('  race: %s'):format(snapshot_data.identity.race))
print(('  caste: %s'):format(snapshot_data.identity.caste))
print(('  profession: %s'):format(snapshot_data.identity.profession))
print(('  citizen: %s'):format(snapshot_data.identity.citizen and 'true' or 'false'))
print_thoughts(snapshot_data.thoughts)
print_personality(snapshot_data)
