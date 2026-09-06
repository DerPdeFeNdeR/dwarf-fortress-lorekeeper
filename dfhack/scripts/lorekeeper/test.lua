-- Run Lorekeeper's pure collector tests inside DFHack.
--
-- Run: lorekeeper/test

local history = reqscript('lorekeeper/history')
local policy = reqscript('lorekeeper/policy')
local glossary = reqscript('lorekeeper/glossary')
local translation = reqscript('lorekeeper/translation')

local passed = 0

local function assert_true(condition, description)
    if not condition then
        error('FAIL: ' .. description)
    end
    passed = passed + 1
    print('PASS: ' .. description)
end

local function copy_snapshot(snapshot_data)
    local copy = {
        identity={
            id=snapshot_data.identity.id,
            name=snapshot_data.identity.name,
            race=snapshot_data.identity.race,
            caste=snapshot_data.identity.caste,
            profession=snapshot_data.identity.profession,
            citizen=snapshot_data.identity.citizen,
        },
        soul_present=snapshot_data.soul_present,
        mental_state={stress=snapshot_data.mental_state.stress},
        thoughts={},
        personality_facets={},
    }

    for index, thought in ipairs(snapshot_data.thoughts) do
        copy.thoughts[index] = {
            thought_id=thought.thought_id,
            thought_name=thought.thought_name,
            emotion_id=thought.emotion_id,
            emotion_name=thought.emotion_name,
            severity=thought.severity,
            relative_strength=thought.relative_strength,
            subthought=thought.subthought,
        }
    end

    for index, facet in ipairs(snapshot_data.personality_facets) do
        copy.personality_facets[index] = {
            facet_id=facet.facet_id,
            facet_name=facet.facet_name,
            value=facet.value,
        }
    end

    return copy
end

local fixture = {
    identity={
        id=9001,
        name='Test Dwarf',
        race='DWARF',
        caste='MALE',
        profession='Miner',
        citizen=true,
    },
    soul_present=true,
    mental_state={stress=1000},
    thoughts={
        {
            thought_id=165,
            thought_name='Talked',
            emotion_id=66,
            emotion_name='FONDNESS',
            severity=0,
            relative_strength=0,
            subthought=17,
        },
        {
            thought_id=189,
            thought_name='WatchPerform',
            emotion_id=36,
            emotion_name='DELIGHT',
            severity=0,
            relative_strength=0,
            subthought=500,
        },
    },
    personality_facets={
        {facet_id='CONFIDENCE', facet_name='CONFIDENCE', value=50},
    },
}

local base_signature = history.signature(fixture)
local subthought_changed = copy_snapshot(fixture)
subthought_changed.thoughts[1].subthought = 99
assert_true(history.signature(subthought_changed) == base_signature,
    'ignores subthought-only changes')

local reordered = copy_snapshot(fixture)
reordered.thoughts[1], reordered.thoughts[2] = reordered.thoughts[2], reordered.thoughts[1]
assert_true(history.signature(reordered) == base_signature,
    'ignores thought list ordering')

local thought_added = copy_snapshot(fixture)
table.insert(thought_added.thoughts, copy_snapshot(fixture).thoughts[1])
assert_true(history.signature(thought_added) ~= base_signature,
    'detects thought count changes')

local small_stress_change = copy_snapshot(fixture)
small_stress_change.mental_state.stress = 1200
assert_true(history.signature(small_stress_change) == base_signature,
    'ignores stress changes within one signature band')

local large_stress_change = copy_snapshot(fixture)
large_stress_change.mental_state.stress = 1600
assert_true(history.signature(large_stress_change) ~= base_signature,
    'detects stress band changes')

local facet_changed = copy_snapshot(fixture)
facet_changed.personality_facets[1].value = 51
assert_true(history.signature(facet_changed) ~= base_signature,
    'detects personality changes')

assert_true(history.should_append(nil, fixture),
    'appends when no previous snapshot exists')
assert_true(not history.should_append(fixture, subthought_changed),
    'skips duplicate snapshots')
assert_true(history.should_append(fixture, thought_added),
    'appends changed snapshots')

assert_true(not policy.should_record(base_signature, base_signature, 100, 200, 100),
    'skips unchanged signatures')
assert_true(policy.should_record('old', 'new', nil, 200, 100),
    'records first changed snapshot')
assert_true(not policy.should_record('old', 'new', 150, 200, 100),
    'honors recording cooldown')
assert_true(policy.should_record('old', 'new', 100, 200, 100),
    'records after cooldown')

local no_soul = copy_snapshot(fixture)
no_soul.soul_present = false
no_soul.mental_state.stress = nil
no_soul.thoughts = {}
no_soul.personality_facets = {}
local no_soul_signature = history.signature(no_soul)
assert_true(no_soul_signature ~= nil,
    'signs snapshots without a soul')

local known_thought = glossary.describe_thought('Talked')
assert_true(known_thought.known and known_thought.source == 'glossary' and
        known_thought.confidence == 'high' and known_thought.raw == 'Talked',
    'returns structured known glossary output')

assert_true(glossary.describe_thought('SatisfiedAtWork').known,
    'labels work satisfaction thoughts')
assert_true(glossary.describe_emotion('SATISFACTION').known,
    'labels satisfaction emotions')
assert_true(glossary.describe_facet('VENGEFUL').known,
    'labels the full personality facet set')

local no_changes = history.describe_changes(fixture, subthought_changed)
assert_true(#no_changes == 0,
    'history ignores subthought-only changes')

local history_change = history.describe_changes(fixture, thought_added)
assert_true(#history_change == 1 and history_change[1]:find('thoughts changed'),
    'history describes thought changes')

local records = {
    {ingame_time={year=1, year_tick=1}, snapshot=fixture},
    {ingame_time={year=1, year_tick=2}, snapshot=large_stress_change},
    {ingame_time={year=1, year_tick=3}, snapshot=(function()
        local snapshot_data = copy_snapshot(large_stress_change)
        snapshot_data.mental_state.stress = 2200
        return snapshot_data
    end)()},
    {ingame_time={year=1, year_tick=4}, snapshot=thought_added},
}
local events = history.build_events(records)
assert_true(#events == 3 and events[2].kind == 'stress_trend' and
        events[2].snapshot_count == 2,
    'groups consecutive stress changes into one event')
assert_true(events[3].kind == 'change' and
        events[3].changes[2]:find('thoughts changed') ~= nil,
    'preserves discrete history changes as events')

local story_input = history.build_story_input(records)
assert_true(story_input.schema_version == 2 and #story_input.events == 3 and
        story_input.events[2].kind == 'stress_trend',
    'builds compact structured story input')
assert_true(#story_input.events[3].thoughts_added == 1 and
        story_input.events[3].thoughts_added[1].thought_name == 'Talked',
    'includes exact thought additions in story input')
assert_true(translation.repair_story_text(
        'Doren ├▓nulokil worked as a woodcutter.',
        'Doren ònulokil, Woodcutter') ==
    dfhack.utf2df('Doren ònulokil') .. ' worked as a woodcutter.',
    'repairs CP437-mojibake story names')

local unknown_thought = glossary.describe_thought('FutureThoughtToken')
assert_true(not unknown_thought.known and unknown_thought.source == 'unknown' and
        unknown_thought.confidence == 'none' and
        unknown_thought.raw == 'FutureThoughtToken',
    'preserves unknown glossary tokens')

print(('The Lorekeeper: %d tests passed.'):format(passed))
