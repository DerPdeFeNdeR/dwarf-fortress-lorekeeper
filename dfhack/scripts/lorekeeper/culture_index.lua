-- Incremental local storytelling incident index; no enrichment during scanning.
--@module = true
local field=reqscript('lorekeeper/references').field
state=state or nil

function new(site,now)
    return {site=site,time=now,scanned=0,total=0,years={},truncated={},errors=0}
end

function add(index,incident,year)
    if incident.site~=index.site or incident.event_year<year-1 or incident.event_year>year or
        field(df.incident_type,incident.type)~='Performance' then return end
    local data=field(field(incident,'data'),'Performance')
    if not data or field(df.performance_event_type,data.performance_event)~='STORYTELLING_EVENT' then return end
    local bucket=index.years[incident.event_year] or {}
    index.years[incident.event_year]=bucket
    for _,row in ipairs(bucket) do if row.id==incident.id then return end end
    if #bucket>=256 then table.remove(bucket,1); index.truncated[incident.event_year]=true end
    table.insert(bucket,{id=incident.id,year=incident.event_year,tick=incident.event_time,
        site_id=incident.site,kind='storytelling',source_kind='incident'})
end

function scan()
    local incidents=df.global.world.incidents.all
    local year=df.global.cur_year
    local now=year*403200+df.global.cur_year_tick
    local site=df.global.plotinfo.site_id
    if not state or state.site~=site or now<state.time or #incidents<state.scanned then state=new(site,now) end
    state.time=now; state.total=#incidents
    local started,count=os.clock(),0
    while state.scanned<#incidents and count<128 and os.clock()-started<0.002 do
        local ok=pcall(add,state,incidents[state.scanned],year)
        if not ok then state.errors=state.errors+1 end
        state.scanned=state.scanned+1; count=count+1
    end
    for y in pairs(state.years) do
        if y<year-1 then state.years[y]=nil; state.truncated[y]=nil end
    end
    state.last_batch_ms=(os.clock()-started)*1000
    return state.scanned==state.total
end

function select(index,year)
    local bucket=index.years[year] or {}
    local rows={}
    for i=#bucket,math.max(1,#bucket-3),-1 do table.insert(rows,bucket[i]) end
    return rows,#bucket>4 or index.truncated[year] or false
end

function enrich(row,resolver)
    local result={}
    for k,v in pairs(row) do result[k]=v end
    local ref=resolver:resolve('performance_incident',row.id)
    result.reference_status=ref.status
    if ref.details then
        result.performance={}
        for k,v in pairs(ref.details) do result.performance[k]=v end
        local subject=resolver.cache[ref.details.subject_reference]
        result.performance.topic=subject and subject.details
    end
    return result
end

function stop() state=nil end
