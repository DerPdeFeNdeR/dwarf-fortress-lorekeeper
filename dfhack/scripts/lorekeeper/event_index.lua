-- Incremental, session-local historical-event index. No synchronous world scan.
--@module = true
local field = reqscript('lorekeeper/references').field
local specs = {
    HIST_FIGURE_DIED={kind='death', fields={victim_hf='victim', slayer_hf='slayer'}},
    HIST_FIGURE_WOUNDED={kind='wounding', fields={woundee='wounded', wounder='wounder'}},
    HIST_FIGURE_SIMPLE_BATTLE_EVENT={kind='battle', groups={'group1','group2'}},
    HF_ATTACKED_SITE={kind='site_attack', fields={attacker_hf='attacker'}},
    ARTIFACT_CREATED={kind='artifact_creation', fields={creator_hfid='creator'}},
    HIST_FIGURE_ABDUCTED={kind='abduction',fields={target='abducted',snatcher='abductor'}},
    HF_FREED={kind='release',fields={freeing_hf='liberator'},groups={'rescued_hfs'}},
    HF_ENSLAVED={kind='enslavement',fields={enslaved_hf='enslaved',seller_hf='seller'},site='moved_to_site'},
    HF_RANSOMED={kind='ransom',fields={ransomed_hf='ransomed',ransomer_hf='ransomer'},site='moved_to_site'},
    HIST_FIGURE_REUNION={kind='reunion',fields={assistant='assistant'},groups={'missing','reunited_with'}},
    HIST_FIGURE_TRAVEL={kind='travel',groups={'group'}},
    CHANGE_HF_JOB={kind='profession_change',fields={hfid='subject'}},
    CHANGE_HF_STATE={kind='whereabouts_change',fields={hfid='subject'}},
    ADD_HF_ENTITY_LINK={kind='entity_link_added',fields={histfig='subject',appointer_hfid='appointer'}},
    REMOVE_HF_ENTITY_LINK={kind='entity_link_removed',fields={histfig='subject'}},
    ADD_HF_HF_LINK={kind='relationship_added',fields={hf='subject',hf_target='target'}},
    REMOVE_HF_HF_LINK={kind='relationship_removed',fields={hf='subject',hf_target='target'}},
    CHANGE_HF_MOOD={kind='mood_change',fields={histfig='subject'}},
    MASTERPIECE_CREATED_ITEM={kind='masterwork_item',fields={maker='maker'}},
}
local enum_fields={
    profession_change={old_job='profession',new_job='profession'},
    whereabouts_change={state='whereabouts_type',reason='history_event_reason'},
    mood_change={mood='mood_type',reason='history_event_reason'},
    entity_link_added={link_type='histfig_entity_link_type'},
    entity_link_removed={link_type='histfig_entity_link_type'},
    relationship_added={type='histfig_hf_link_type'},
    relationship_removed={type='histfig_hf_link_type'},
}

function importance(row)
    if row.kind=='death' then return 5 end
    if row.kind=='wounding' or row.kind=='abduction' or row.kind=='enslavement' or
        row.kind=='ransom' or row.kind=='release' or row.kind=='artifact_creation' then return 4 end
    if row.kind=='travel' or row.kind=='whereabouts_change' then return 0 end
    if row.kind=='profession_change' or row.kind=='masterwork_item' then return 1 end
    return 2
end

function select_events(bucket,limit)
    local ordered={table.unpack(bucket)}
    table.sort(ordered,function(a,b)
        if importance(a)==importance(b) then return a.id>b.id end
        return importance(a)>importance(b)
    end)
    local rows,counts,selected={},{},{}
    for _,row in ipairs(ordered) do
        if #rows>=limit then break end
        if (counts[row.kind] or 0)<2 then
            table.insert(rows,row); selected[row.id]=true
            counts[row.kind]=(counts[row.kind] or 0)+1
        end
    end
    for _,row in ipairs(ordered) do
        if #rows>=limit then break end
        if not selected[row.id] then table.insert(rows,row) end
    end
    return rows
end

function normalize(event, token)
    local spec = specs[token]
    if not spec then return end
    local row = {id=event.id, kind=spec.kind, year=event.year, tick=event.seconds,
        site_id=field(event,spec.site or 'site'),
        location_role=spec.site and 'destination' or 'event_site',participants={}}
    for name in pairs(enum_fields[spec.kind] or {}) do row[name..'_id']=field(event,name) end
    if spec.kind=='entity_link_added' or spec.kind=='entity_link_removed' then
        row.entity_id=field(event,'civ')
        row.position_id=field(event,'position_id')
    end
    if spec.kind=='masterwork_item' then row.item_id=field(event,'item_id') end
    if spec.kind=='travel' then
        row.is_return=field(field(event,'reason'),'is_return')
        row.is_escape=field(field(event,'reason'),'is_escape')
    end
    local function participant(id, role)
        if type(id)=='number' and id>=0 then
            table.insert(row.participants,{histfig_id=id,role=role})
        end
    end
    for name,role in pairs(spec.fields or {}) do participant(field(event,name),role) end
    for _,group in ipairs(spec.groups or {}) do
        local vector = field(event,group)
        if vector then
            local visited=0
            for _,id in ipairs(vector) do
                if visited>=32 then row.participants_truncated=true; break end
                visited=visited+1
                participant(id,group)
            end
        end
    end
    if row.kind=='artifact_creation' then
        row.artifact_id=field(event,'artifact_id')
        row.naming_only=field(field(event,'flags2'),'name_only')
        -- Naming an existing item is not creating a new artifact.
        if row.naming_only==nil then return end
    end
    if row.kind=='death' then row.death_cause_id=field(event,'death_cause') end
    if row.kind=='battle' then row.subtype_id=field(event,'subtype') end
    if row.kind=='wounding' then row.part_lost=field(event,'part_lost') end
    table.sort(row.participants,function(a,b)
        if a.role==b.role then return a.histfig_id<b.histfig_id end
        return a.role<b.role
    end)
    return row
end

function new_index(limit)
    local index={version=5,by_figure={}, site_years={},site_truncated={},slots={},next_slot=1,links=0, limit=limit or 50000, truncated=false,
        scanned=0, errors=0}
    function index:add_site(row,site_id,current_year)
        if row.site_id~=site_id or row.year<current_year-1 or row.year>current_year then return end
        local bucket=self.site_years[row.year] or {}
        self.site_years[row.year]=bucket
        if #bucket>=256 then
            self.site_truncated[row.year]=true
            local lowest=1
            for i=2,#bucket do
                if importance(bucket[i])<importance(bucket[lowest]) then lowest=i end
            end
            if importance(row)<importance(bucket[lowest]) then return end
            table.remove(bucket,lowest)
        end
        table.insert(bucket,row)
    end
    function index:remove_link(hfid,event_id)
        local bucket=self.by_figure[hfid] or {}
        for i,row in ipairs(bucket) do
            if row.id==event_id then
                table.remove(bucket,i)
                self.links=self.links-1
                if #bucket==0 then self.by_figure[hfid]=nil end
                return
            end
        end
    end
    function index:add(row)
        local seen={}
        for _,p in ipairs(row.participants) do
            local id=p.histfig_id
            if not seen[id] then
                seen[id]=true
                local bucket=self.by_figure[id]
                if bucket and #bucket>=32 then
                    self.truncated=true
                    local lowest=1
                    for i=2,#bucket do
                        if importance(bucket[i])<importance(bucket[lowest]) or
                            (importance(bucket[i])==importance(bucket[lowest]) and bucket[i].id<bucket[lowest].id) then lowest=i end
                    end
                    if importance(row)>=importance(bucket[lowest]) then
                        table.remove(bucket,lowest)
                        self.links=self.links-1
                    else goto next_participant end
                end
                -- A fixed-size ring evicts oldest retained links instead of
                -- refusing all newer figures/events once world history fills it.
                local old=self.slots[self.next_slot]
                if old then
                    self:remove_link(old.hfid,old.event_id)
                    self.truncated=true
                end
                bucket=self.by_figure[id] or {}
                self.by_figure[id]=bucket
                table.insert(bucket,row)
                self.links=self.links+1
                self.slots[self.next_slot]={hfid=id,event_id=row.id}
                self.next_slot=self.next_slot%self.limit+1
            end
            ::next_participant::
        end
    end
    return index
end

state = state or nil
timer = timer or nil

function needs_reset(index,total,time)
    return not index or total<index.scanned or time<index.time
end

function stop()
    if timer then dfhack.timeout_active(timer,nil) end
    timer=nil
    state=nil
end

local function pump()
    timer=nil
    if not dfhack.isMapLoaded() then stop(); return end
    local events=df.global.world.history.events
    local now=df.global.cur_year*403200+df.global.cur_year_tick
    if needs_reset(state,#events,now) then state=new_index() end
    state.time=now
    local started=os.clock()
    local count=0
    while state.scanned<#events and count<128 and os.clock()-started<0.002 do
        local event=events[state.scanned]
        local ok,row=pcall(function()
            return normalize(event,df.history_event_type[event:getType()])
        end)
        if not ok then state.errors=state.errors+1
        elseif row then
            state:add(row)
            state:add_site(row,df.global.plotinfo.site_id,df.global.cur_year)
        end
        state.scanned=state.scanned+1
        count=count+1
    end
    state.total=#events
    for year in pairs(state.site_years) do
        if year<df.global.cur_year-1 then state.site_years[year]=nil; state.site_truncated[year]=nil end
    end
    state.last_batch_ms=(os.clock()-started)*1000
    state.max_batch_ms=math.max(state.max_batch_ms or 0,state.last_batch_ms)
    timer=dfhack.timeout(state.scanned<#events and 1 or 100,'frames',pump)
end

function start()
    if not dfhack.isMapLoaded() then return end
    if timer and dfhack.timeout_active(timer) then return end
    timer=dfhack.timeout(1,'frames',pump)
end

function enrich(source,resolver,hfid)
    local row={}
    for key,value in pairs(source) do if key~='participants' then row[key]=value end end
    row.participants={}
    for j,p in ipairs(source.participants) do
        if j>8 then row.participants_truncated=true; break end
        local ref=resolver:resolve('historical_figure',p.histfig_id)
        table.insert(row.participants,{histfig_id=p.histfig_id,role=p.role,
            name=ref.details and ref.details.name,reference_status=ref.status})
    end
    row.subject_roles={}
    for _,p in ipairs(source.participants) do
        if p.histfig_id==hfid then table.insert(row.subject_roles,p.role) end
    end
    local site=resolver:resolve('site',source.site_id)
    row.site_name=site.details and site.details.name
    if source.artifact_id then
        local artifact=resolver:resolve('artifact',source.artifact_id)
        row.artifact_name=artifact.details and artifact.details.name
        row.artifact_status=artifact.status
    end
    if source.death_cause_id then row.death_cause=field(df.death_type,source.death_cause_id) end
    if source.kind=='death' or source.kind=='wounding' then
        local ok,details=pcall(reqscript('lorekeeper/event_method').capture,source)
        row.method=ok and details or {status='unavailable'}
    end
    if source.subtype_id then row.subtype=field(df.history_event_simple_battle_subtype,source.subtype_id) end
    for name,enum in pairs(enum_fields[source.kind] or {}) do row[name]=field(df[enum],source[name..'_id']) end
    if source.entity_id then
        local entity=resolver:resolve('entity',source.entity_id)
        row.entity_name=entity.details and entity.details.name
        row.entity_details=entity.details
    end
    if source.item_id then
        local item=resolver:resolve('item',source.item_id)
        row.item_name=item.details and item.details.name
        row.item_status=item.status
    end
    return row
end

function capture(hfid, resolver)
    local now=df.global.cur_year*403200+df.global.cur_year_tick
    if state and needs_reset(state,#df.global.world.history.events,now) then stop() end
    start()
    local rows={}
    local coverage={status=state and state.scanned==state.total and 'ready' or 'building',
        scanned=state and state.scanned or 0,total=state and state.total or 0,
        truncated=state and state.truncated or false, errors=state and state.errors or 0}
    local bucket=state and state.by_figure[hfid] or {}
    coverage.subject_events=#bucket
    coverage.subject_truncated=#bucket>8
    for _,source in ipairs(select_events(bucket,8)) do
        table.insert(rows,enrich(source,resolver,hfid))
    end
    return {events=rows,coverage=coverage}
end

dfhack.onStateChange['lorekeeper.event_index']=function(change)
    if change==SC_MAP_UNLOADED or change==SC_WORLD_UNLOADED then stop() end
end
-- Hot reload must not reuse an index built with a narrower supported-type set.
if state and state.version~=5 then stop() end

if dfhack_flags.module then return end
start()
print(('The Lorekeeper: event index %s; scanned %d/%d; errors %d; max batch %.2f ms'):format(
    state and state.scanned==state.total and 'ready' or 'building',
    state and state.scanned or 0,state and state.total or 0,state and state.errors or 0,
    state and state.max_batch_ms or 0))
