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
local biography_overlay = reqscript('lorekeeper/overlay')
local friends = reqscript('lorekeeper/friends')
local event_index = reqscript('lorekeeper/event_index')
local chronicle = reqscript('lorekeeper/chronicle')
local storytelling = reqscript('lorekeeper/storytelling')

local passed = 0

local function assert_true(condition, description)
    if not condition then
        error('FAIL: ' .. description)
    end
    passed = passed + 1
    print('PASS: ' .. description)
end

local paragraphs = display_text.wrap('First paragraph.\n\nLater records.')
local atmosphere=reqscript('lorekeeper/environment')
assert_true(atmosphere.should_sample(nil,100) and not atmosphere.should_sample(100,100),
    'environment samples once while game time is paused')
assert_true(not atmosphere.should_sample(100,219) and atmosphere.should_sample(100,220),
    'environment sampling is bounded by game ticks')
assert_true(atmosphere.should_sample(220,100), 'environment detects backward observation time')
assert_true(not atmosphere.should_record({weather='Rain',time=100},'Rain',1299)
    and atmosphere.should_record({weather='Rain',time=100},'Rain',1300),
    'environment emits daily checkpoints without repeated unchanged rows')
assert_true(atmosphere.should_record({weather='Rain',time=100},'Snow',220),
    'environment records precipitation changes')
local event_method=reqscript('lorekeeper/event_method')
local detail_lookups=0
local method_event={id=7,death_cause=df.death_type.DROWN,weapon={
    item_type=df.item_type.AMMO,item_subtype=0,item=10,
    shooter_item_type=df.item_type.WEAPON,shooter_item_subtype=0,shooter_item=11}}
function method_event:getType() return df.history_event_type.HIST_FIGURE_DIED end
local function find_method(id) detail_lookups=detail_lookups+1; return method_event end
local method=event_method.capture({id=7,kind='death'},find_method,
    function(raw) return raw.role=='launcher' and 'crossbow' or 'bolt' end)
assert_true(detail_lookups==1 and method.death_cause=='DROWN' and #method.weapons==2
    and method.weapons[1].name=='bolt' and method.weapons[2].name=='crossbow',
    'event methods resolve one exact event and separate impact item from launcher')
assert_true(event_method.capture({id=8,kind='death'},find_method).status=='unavailable',
    'method lookup rejects an unrelated event identity')
assert_true(event_method.capture({id=7,kind='wounding'},find_method).status=='wrong_event_type',
    'method lookup rejects the wrong event type')
method=event_method.capture({id=7,kind='death'},find_method,function() error('unsupported') end)
assert_true(method.weapons[1].status=='unavailable' and method.weapons[1].name==nil,
    'unsupported weapon resolution does not fabricate a description')
detail_lookups=0
assert_true(event_method.capture({id=7,kind='battle'},find_method)==nil and detail_lookups==0,
    'unrelated events do no method lookup')
local narrator=reqscript('lorekeeper/narrator')
local eventful={{id=1,year=102,site_id=745},{id=1,year=102,site_id=745},
    {id=2,year=101,site_id=745},{id=3,year=102,site_id=999}}
assert_true(narrator.weight(eventful,102,745)==2 and narrator.weight({},102,745)==1,
    'narrator weights unique local year events and retains quiet citizens')
for i=4,20 do table.insert(eventful,{id=i,year=102,site_id=745}) end
assert_true(narrator.weight(eventful,102,745)==9,'narrator event bonus is bounded')
local selection={count=0,total=0}
narrator.consider(selection,1,1,function() return 1 end)
narrator.consider(selection,2,9,function(total) return total end)
assert_true(selection.chosen==1 and selection.total==10 and selection.count==2,
    'weighted narrator draw does not always choose the most eventful dwarf')
narrator.consider(selection,3,9,function() return 1 end)
assert_true(selection.chosen==3,'weighted narrator draw can select another citizen')
local saved_voice=require('json').encode({version=1,status='selected',year=102,site_id=745,
    histfig_id=7,name='Test dwarf',personality_facets={HUMOR=80},values={},
    mental_attributes={version=1,status='unavailable',attributes={}}})
local function never_write() error('Persisted narrator must not be replaced') end
local function read_voice() return saved_voice end
local first_voice=narrator.for_year('unused',102,745,{},never_write,read_voice)
local second_voice=narrator.for_year('unused',102,745,{},never_write,read_voice)
assert_true(first_voice.histfig_id==7 and second_voice.personality_facets.HUMOR==80,
    'saved annual narrator and voice survive draft retry and reload without selection')
local ok=pcall(narrator.for_year,'unused',103,745,{},never_write,read_voice)
assert_true(not ok,'wrong-year narrator is rejected rather than silently reused')
ok=pcall(narrator.for_year,'unused',102,745,{},never_write,function() return '{broken' end)
assert_true(not ok,'corrupt saved narrator is not randomly replaced')
assert_true(narrator.traits({traits={HUMOR=80,ORDERLINESS=30}}).HUMOR==80 and
    next(narrator.traits(nil))==nil,'bounded voice capture handles missing personality')
assert_true(narrator.displayed_voice({story='Older external account',narrator={name='New dwarf'}})==nil,
    'pending memoire never attributes older external prose to the new narrator')
assert_true(narrator.displayed_voice({story='Saved account',story_narrator={name='Original dwarf'},
    narrator={name='Requested dwarf'}}).name=='Original dwarf',
    'display attribution belongs to the published story, not pending work')
assert_true(narrator.relative_attribute(500,1000)=='lower' and
    narrator.relative_attribute(1000,1000)=='typical' and narrator.relative_attribute(1500,1000)=='higher',
    'mental voice bands compare each attribute with its caste baseline')
assert_true(narrator.relative_attribute(1500,2000)=='typical' and
    narrator.relative_attribute(1000,nil)=='unknown','missing baselines are not guessed')
local mental_calls=0
local mental=narrator.mental_attributes({status={current_soul={}}},function(_,name)
    mental_calls=mental_calls+1
    if name=='MEMORY' then error('unavailable') end
    return 1500,1000
end)
assert_true(mental_calls==4 and mental.status=='partial' and
    mental.attributes.LINGUISTIC_ABILITY.relative_level=='higher' and mental.attributes.MEMORY==nil,
    'mental capture uses four bounded reads and reports unsupported attributes')
assert_true(narrator.mental_attributes(nil).status=='unavailable',
    'missing soul does not fabricate mental attributes')
local old_voice={status='selected',histfig_id=7,name='Original'}
assert_true(narrator.add_missing_mental_attributes(old_voice,{hist_figure_id=8}) and
    old_voice.histfig_id==7 and old_voice.mental_attributes.status=='unavailable',
    'voice upgrade preserves narrator and rejects a reused unit identity')
assert_true(not narrator.add_missing_mental_attributes(old_voice,nil),
    'mental voice enrichment is saved once rather than recaptured on refresh')
local stored_companion,companion_writes=nil,0
local legacy=require('json').encode({version=1,status='selected',year=102,site_id=745,
    histfig_id=7,name='Original',personality_facets={HUMOR=80},values={}})
local function companion_read(path)
    if path:find('.mental.json',1,true) then return stored_companion end
    return legacy
end
local function companion_write(data,name)
    assert(name=='745-102.narrator.mental.json','Original narrator must never be overwritten')
    companion_writes=companion_writes+1; stored_companion=require('json').encode(data)
end
local upgraded=narrator.for_year('unused',102,745,{},companion_write,companion_read)
local reused=narrator.for_year('unused',102,745,{},companion_write,companion_read)
assert_true(companion_writes==1 and upgraded.histfig_id==7 and reused.mental_attributes.status=='unavailable',
    'legacy narrator enrichment uses one immutable companion and preserves original identity')
local culture=reqscript('lorekeeper/culture_index')
local cultural_index=culture.new(745,0)
local telling={id=1,site=745,event_year=102,event_time=10,type=df.incident_type.Performance,
    data={Performance={performance_event=df.performance_event_type.STORYTELLING_EVENT}}}
culture.add(cultural_index,telling,102); culture.add(cultural_index,telling,102)
assert_true(#cultural_index.years[102]==1,'chronicle deduplicates storytelling incidents')
telling.id=2; telling.site=999; culture.add(cultural_index,telling,102)
telling.site=745; telling.data.Performance.performance_event=df.performance_event_type.POETRY_RECITAL
culture.add(cultural_index,telling,102)
assert_true(#cultural_index.years[102]==1,'culture index excludes other sites and non-story performances')
telling.data.Performance.performance_event=df.performance_event_type.STORYTELLING_EVENT
for i=2,270 do telling.id=i; culture.add(cultural_index,telling,102) end
local cultural_selected,cultural_truncated=culture.select(cultural_index,102)
assert_true(#cultural_index.years[102]==256 and #cultural_selected==4 and cultural_truncated,
    'culture index bounds retention and annual selection')
local chapter_list={{key='intro'},{key='000102-03'},{key='000101-11'}}
assert_true(reader_text.selected_chapter(chapter_list).key=='intro',
    'memoire opens on introduction by default')
assert_true(reader_text.selected_chapter(chapter_list,'000102-03').key=='000102-03',
    'background refresh preserves explicitly selected month')
assert_true(reader_text.selected_chapter({{key='000102-03'}},'intro')==nil,
    'pending introduction does not jump to a monthly chapter')
local relationships=reader_text.relationship_lines({
    relationships={{kind='<type: histfig hf link motherst>',target_name='Momuz Lilumuzol'}},
    friends={{kind='close_friend',target_name='Urist McTester'},
        {kind='close_friend',target_name='Urist McTester'}}},68)
assert_true(#relationships==3 and relationships[1]=='Relationships' and
    relationships[2]=='- Mother: Momuz Lilumuzol' and relationships[3]=='- Close friend: Urist McTester',
    'memoire introduction appends deduplicated current relationships from the latest profile')
local chapter_requests = reqscript('lorekeeper/view_request')
assert_true(chapter_requests.read_chapter(1,'../another.json') == nil and
    chapter_requests.read_chapter(1,'2.monthly.abc.json') == nil,
    'monthly reader rejects traversal and another dwarf chapter')
assert_true(reader_text.status({monthly_version=1,state='ready'},nil,true):find('browse months',1,true) ~= nil,
    'monthly reader explains chapter navigation')
local calls=0
local function story_resolver(kind,id)
    calls=calls+1
    return {key=kind..':'..id,status='resolved',details={name='Test narrator'}}
end
local performance={type=df.incident_type.Performance,event_year=102,event_time=10,site=1,
    data={Performance={performance_event=df.performance_event_type.POETRY_RECITAL,reference_id=41,
        written_content_id=-1,participants={}}}}
storytelling.performance(performance,story_resolver)
assert_true(calls==0,'poetry reference IDs are never resolved as historical story events')
performance.data.Performance.performance_event=df.performance_event_type.STORYTELLING_EVENT
local story=storytelling.performance(performance,story_resolver)
assert_true(story.subject_reference=='story_subject:41' and story.year==102 and calls==1,
    'storytelling resolves the historical subject while preserving performance time')
performance.data.Performance.written_content_id=8
story=storytelling.performance(performance,story_resolver)
assert_true(story.subject_status=='unsupported_reference' and calls==1,
    'unsupported written story references do not guess a historical event')
local office=storytelling.position_definition({positions={own={{id=7,name={[0]='copper voice'},flags={ELECTED=true}}}}},7)
assert_true(office.name=='copper voice' and office.definition_observed_now,
    'story office resolves by definition ID without inferring a historical location')
assert_true(reader_text.status({state='ready',biography_update={mode='defer'}},nil,true,nil)==
    'No significant new developments. Saved memoire unchanged.',
    'reader explains deferred routine developments without claiming a new story')
local annual_state={year=101,time=101*403200+400000}
local closed=chronicle.advance(annual_state,102,10)
assert_true(#closed==1 and closed[1]==101,'annual rollover closes exactly the completed year')
assert_true(#chronicle.advance(annual_state,102,20)==0,'annual rollover does not duplicate chapter requests')
local backwards,why=chronicle.advance(annual_state,101,30)
assert_true(backwards==nil and why=='time_reversal','annual monitor detects incompatible time reversal')
local site_index=event_index.new_index()
site_index:add_site({id=1,kind='battle',site_id=745,year=102},745,102)
site_index:add_site({id=2,kind='battle',site_id=900,year=102},745,102)
site_index:add_site({id=3,kind='battle',site_id=745,year=100},745,102)
assert_true(#site_index.site_years[102]==1 and not site_index.site_years[100],
    'annual index isolates fortress site and bounded year range')
for id=4,300 do site_index:add_site({id=id,kind='battle',site_id=745,year=102},745,102) end
assert_true(#site_index.site_years[102]==256 and site_index.site_truncated[102],
    'annual site buckets remain bounded and report truncation')
local skipped_state={year=80,time=80*403200}
local skipped_years,_,skipped_count=chronicle.advance(skipped_state,102,0)
assert_true(#skipped_years==8 and skipped_count==14,
    'annual catch-up bounds work and reports omitted years')
local abduction=event_index.normalize({id=10,target=1,snatcher=2},'HIST_FIGURE_ABDUCTED')
assert_true(abduction.kind=='abduction' and abduction.participants[1].role=='abducted',
    'abduction retains victim and abductor roles')
local released=event_index.normalize({id=11,freeing_hf=2,rescued_hfs={1,3}},'HF_FREED')
assert_true(#released.participants==3 and released.kind=='release',
    'release indexes both liberator and rescued figures')
local travel=event_index.normalize({id=12,group={1},reason={is_return=false,is_escape=true}},'HIST_FIGURE_TRAVEL')
assert_true(travel.is_escape and travel.is_return==false,'travel preserves explicit escape and return flags')
local link=event_index.normalize({id=13,hf=1,hf_target=2,type=7},'ADD_HF_HF_LINK')
assert_true(link.type_id==7 and link.participants[1].histfig_id==1 and link.participants[1].role=='subject',
    'personal link events retain source target direction and type')
local job=event_index.normalize({id=14,hfid=1,old_job=2,new_job=3},'CHANGE_HF_JOB')
assert_true(job.old_job_id==2 and job.new_job_id==3,'profession events retain both endpoints')
local candidates={{id=1,kind='artifact_creation'}}
for i=2,20 do table.insert(candidates,{id=i,kind='travel'}) end
local selected=event_index.select_events(candidates,8)
assert_true(#selected==8 and selected[1].kind=='artifact_creation',
    'routine travel does not displace a distinctive artifact in selection')
local protected=event_index.new_index()
protected:add({id=1,kind='artifact_creation',participants={{histfig_id=1}}})
for i=2,50 do protected:add({id=i,kind='travel',participants={{histfig_id=1}}}) end
local has_artifact=false
for _,row in ipairs(protected.by_figure[1]) do if row.kind=='artifact_creation' then has_artifact=true end end
assert_true(has_artifact and #protected.by_figure[1]==32,'bounded retention protects milestones from routine churn')
assert_true(event_index.needs_reset({scanned=5,time=10},4,10) and
    event_index.needs_reset({scanned=5,time=10},5,9) and
    not event_index.needs_reset({scanned=5,time=10},6,11),
    'historical index resets on shrink or time reversal but not append')
assert_true(reader_text.status({state='ready',historical_event_coverage={status='building'}},nil,true):find('indexing'),
    'reader discloses historical events still indexing at capture')
local battle=event_index.normalize({id=1,year=2,seconds=3,group1={4},group2={5}},
    'HIST_FIGURE_SIMPLE_BATTLE_EVENT')
assert_true(battle.participants[2].role=='group2' and battle.participants[2].histfig_id==5,
    'historical battles preserve explicit participant sides')
assert_true(event_index.normalize({id=1},'WAR_FIELD_BATTLE')==nil,
    'fortress-wide battle does not imply individual participation')
local artifact=event_index.normalize({id=2,flags2={name_only=true},creator_hfid=4},'ARTIFACT_CREATED')
assert_true(artifact.naming_only and artifact.participants[1].role=='creator',
    'artifact event preserves naming-only flag')
local index=event_index.new_index(2)
index:add(battle)
index:add({id=2,participants={{histfig_id=6}}})
assert_true(index.links==2 and index.truncated and index.by_figure[6] and not index.by_figure[4],
    'historical event index bounds links while retaining new evidence at capacity')
local bounded=event_index.new_index()
for i=1,40 do bounded:add({id=i,participants={{histfig_id=4},{histfig_id=4}}}) end
assert_true(#bounded.by_figure[4]==32 and bounded.links==32 and bounded.by_figure[4][1].id==9,
    'historical index deduplicates participant links and retains bounded recent events')
assert_true(friends.classify(49)==nil and friends.classify(50)=='friend' and
    friends.classify(74)=='friend' and friends.classify(75)=='close_friend' and
    friends.classify(100)=='kindred_spirit' and friends.classify(101)==nil,
    'friendship classification respects documented love thresholds')
local friend_rows=friends.capture({{histfig_id=1,core={love=5}}, {histfig_id=2,core={love=60}}},
    references.new({historical_figure=function(id) return {name='Friend '..id} end}))
assert_true(#friend_rows==1 and friend_rows[1].target_hf==2 and friend_rows[1].directional,
    'friend capture excludes acquaintances and preserves direction')
local contacts={}
for i=1,129 do table.insert(contacts,{histfig_id=i,core={love=0}}) end
local _,friend_limits=friends.capture(contacts,references.new({}))
assert_true(#friend_limits==1,'friendship capture bounds contact scanning')
assert_true(biography_overlay.eligible({open=true,active_sheet=0,active_id=7},0),
    'memoire button is eligible on an open unit sheet')
assert_true(not biography_overlay.eligible({open=false,active_sheet=0,active_id=7},0) and
    not biography_overlay.eligible({open=true,active_sheet=1,active_id=7},0),
    'memoire button excludes closed and non-unit sheets')
assert_true(not biography_overlay.eligible({open=true,active_sheet=0,active_id=-1},0) and
    not biography_overlay.eligible({open=true,active_sheet=0,active_id=7,unit_overview_customizing=true},0),
    'memoire shortcut is inactive during customization or invalid selection')
local reader_request={unit_id=7,year=102,tick=123,nonce=456}
local reader_data={state='ready',request=reader_request,story='A quiet life.\n\nA lasting memory.',
    record_count=50,event_count=34}
assert_true(not reader_text.pending(reader_data,reader_request),
    'reader recognizes the completed requested memoire')
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
    'reader explains offline status without hiding saved memoires')
assert_true(reader_text.status(nil,reader_request,true)=='Preparing this Memoire...' and
    table.concat(reader_text.lines(nil,68),' '):find('keep playing',1,true)~=nil,
    'reader explains first-generation waiting without technical clutter')
local overview = profile.quick_overview({status={}})
assert_true(#overview == 2 and overview[1]:find('not a generated memoire', 1, true) ~= nil,
    'shows an immediate factual fallback without requiring a model')
assert_true(#display_text.wrap('') == 1 and display_text.wrap('')[1] == '',
    'preserves an explicit memoire-to-timeline spacer')
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
