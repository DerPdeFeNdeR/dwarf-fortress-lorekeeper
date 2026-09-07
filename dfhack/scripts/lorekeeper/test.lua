-- Run Lorekeeper's pure collector tests inside DFHack.
--
-- Run: lorekeeper/test

local history = reqscript('lorekeeper/history')
local policy = reqscript('lorekeeper/policy')
local glossary = reqscript('lorekeeper/glossary')
local translation = reqscript('lorekeeper/translation')
local display_text = reqscript('lorekeeper/display_text')
local profile = reqscript('lorekeeper/profile')
local references = reqscript('lorekeeper/references')
local reader_text = reqscript('lorekeeper/reader_text')

local passed = 0

local function assert_true(condition, description)
    if not condition then
        error('FAIL: ' .. description)
    end
    passed = passed + 1
    print('PASS: ' .. description)
end

local paragraphs = display_text.wrap('First paragraph.\n\nLater records.')
local reader_request={unit_id=7,year=102,tick=123,nonce=456}
local reader_data={state='ready',request=reader_request,story='A quiet life.\n\nA lasting memory.',
    record_count=50,event_count=34}
assert_true(not reader_text.pending(reader_data,reader_request),
    'reader recognizes the completed requested biography')
assert_true(reader_text.pending(reader_data,{unit_id=7,year=102,tick=123,nonce=457}),
    'reader distinguishes an older ready result from a pending update')
assert_true(table.concat(reader_text.lines(reader_data,68),'\n')==reader_data.story,
    'reader shows paragraphs without technical timeline data')
reader_data.state='processing'
assert_true(reader_text.status(reader_data,reader_request,true):find('previous version',1,true)~=nil and
    reader_text.lines(reader_data,68)[1]=='A quiet life.',
    'reader retains the previous story during generation')
reader_data.state='failed'
assert_true(reader_text.status(reader_data,reader_request,true):find('failed',1,true)~=nil and
    reader_text.lines(reader_data,68)[1]=='A quiet life.',
    'reader retains saved prose after failed generation')
assert_true(reader_text.status(reader_data,reader_request,false):find('offline',1,true)~=nil,
    'reader explains offline status without hiding saved biographies')
assert_true(reader_text.status(nil,reader_request,true):find('preparing',1,true)~=nil and
    table.concat(reader_text.lines(nil,68),' '):find('keep playing',1,true)~=nil,
    'reader explains first-generation waiting without technical clutter')
local overview = profile.quick_overview({status={}})
assert_true(#overview == 2 and overview[1]:find('not a generated biography', 1, true) ~= nil,
    'shows an immediate factual fallback without requiring a model')
assert_true(#display_text.wrap('') == 1 and display_text.wrap('')[1] == '',
    'preserves an explicit biography-to-timeline spacer')
assert_true(profile.reference_kind('Death') == 'historical_figure' and
    profile.reference_kind('UnexpectedDeath') == 'historical_figure',
    'resolves verified death thought reference types')
assert_true(profile.reference_kind('WitnessDeath') == 'incident' and
    profile.reference_kind('SawDeadBody') == 'incident',
    'does not confuse incident references with historical figures')
local lookups = 0
local resolver = references.new({unit=function(id)
    lookups=lookups+1; return {name='Victim', histfig_id=id+1}
end, incident=function(id, _, resolve)
    local victim = resolve('unit', 8421)
    return {victim_name=victim.details.name, victim_reference=victim.key}
end}, 4)
local incident = resolver:resolve('incident', 141)
resolver:resolve('unit', 8421)
assert_true(incident.details.victim_name == 'Victim' and lookups == 1,
    'resolves incident victims with deduplicated typed lookups')
assert_true(resolver:resolve('unknown', 141).status == 'unsupported_type' and
    resolver:resolve('unit', -1).status == 'invalid_id',
    'retains explicit unsupported and invalid reference statuses')
assert_true(resolver:resolve('unit', 99).status == 'budget_exhausted',
    'caps reference resolution work')
local missing = references.new({unit=function() return nil end,
    item=function() error('unsupported layout') end})
assert_true(missing:resolve('unit', 1).status == 'missing' and
    missing:resolve('item', 1).status == 'lookup_error',
    'distinguishes missing objects from unsupported layouts')
local targets = references.preference_targets({creature_id=4, color_id=7}, 'LikeColor')
assert_true(#targets == 1 and targets[1].kind == 'color' and targets[1].id == 7,
    'resolves only active preference union fields')
local typed = references.new({unit=function() return {name='Unit'} end,
    historical_figure=function() return {name='Figure'} end})
assert_true(typed:resolve('unit', 1).details.name ~= typed:resolve('historical_figure', 1).details.name,
    'keeps identical numeric IDs in different namespaces distinct')
local chain = references.new({unit=function(id, _, resolve)
    return {next=resolve('unit', id+1).status}
end})
chain:resolve('unit', 1)
assert_true(#chain.records == 4 and chain.records[4].status == 'depth_exceeded',
    'bounds nested reference traversal')
assert_true(table.concat(display_text.wrap('Minkot Udistatír—a “small” comfort…', 100), '\n') ==
    dfhack.utf2df('Minkot Udistatír -- a "small" comfort...'),
    'renders Unicode punctuation without damaging accented names')
assert_true(#paragraphs == 3 and paragraphs[1] == 'First paragraph.' and
    paragraphs[2] == '' and paragraphs[3] == 'Later records.',
    'preserves story paragraph breaks without question marks')
local windows_lines = display_text.wrap('First\r\n\r\nSecond\rThird\tword')
assert_true(table.concat(windows_lines, '\n') == 'First\n\nSecond\nThird word',
    'normalizes story line endings and tabs before display conversion')
local name_lines = display_text.wrap('Doren ònulokil\n\nMistêm Oslandakas')
assert_true(name_lines[1] == dfhack.utf2df('Doren ònulokil') and
    name_lines[3] == dfhack.utf2df('Mistêm Oslandakas'),
    'preserves accented names across story paragraphs')
assert_true(table.concat(display_text.wrap('one two three', 7), '\n') == 'one two\nthree',
    'wraps story words within the display width')

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
