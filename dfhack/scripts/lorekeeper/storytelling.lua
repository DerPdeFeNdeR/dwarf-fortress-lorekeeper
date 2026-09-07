-- Typed performance references. No world scan and no collector-side enrichment.
--@module = true
local refs=reqscript('lorekeeper/references')
local field=refs.field

function position_definition(entity, position_id)
    local visited=0
    for _,section in ipairs({'own','site','conquered_site'}) do
        local positions=field(field(entity,'positions'),section)
        for _,position in ipairs(positions or {}) do
            visited=visited+1
            if visited>128 then return {status='truncated'} end
            if position.id==position_id then
                return {status='resolved',name=dfhack.df2utf(position.name[0]),
                    elected=field(position.flags,'ELECTED'),definition_observed_now=true}
            end
        end
    end
    return {status='missing'}
end

function performance(object, resolve)
    if not object or field(df.incident_type,object.type)~='Performance' then return end
    local data=field(field(object,'data'),'Performance')
    if not data then return end
    local kind=field(df.performance_event_type,data.performance_event)
    local result={performance_type=kind,year=object.event_year,tick=object.event_time,
        site_id=object.site,reference_id=data.reference_id,written_content_id=data.written_content_id}
    -- Union references are type-specific: a poem's ID is never an event ID.
    if kind~='STORYTELLING_EVENT' then return result end
    if data.written_content_id>=0 or data.reference_id<0 then
        result.subject_status='unsupported_reference'; return result
    end
    local subject=resolve('story_subject',data.reference_id)
    result.subject_reference=subject.key; result.subject_status=subject.status
    result.performers={}
    for i,person in ipairs(data.participants) do
        if #result.performers>=4 then result.performers_truncated=true; break end
        local id=field(field(person,'hf'),'hfid')
        local target=resolve('historical_figure',id)
        table.insert(result.performers,{histfig_id=id,name=target.details and target.details.name,
            reference_status=target.status})
    end
    return result
end

function subject(event, resolve)
    if not event then return end
    local token=df.history_event_type[event:getType()]
    local index=reqscript('lorekeeper/event_index')
    local row=index.normalize(event,token)
    if not row and token=='ENTITY_CREATED' then
        row={id=event.id,kind='entity_created',year=event.year,tick=event.seconds,
            entity_id=event.entity,site_id=event.site,participants={}}
    end
    if not row then return {id=event.id,kind=token,status='unsupported_event'} end
    local adapter={resolve=function(_,kind,id,extra)
        return resolve(kind=='historical_figure' and 'story_figure' or kind,id,extra)
    end}
    local result=index.enrich(row,adapter)
    result.status='resolved'
    -- No listener ID or subject_roles: these are events being TOLD ABOUT.
    result.subject_roles=nil
    if row.kind=='entity_link_added' and result.link_type=='POSITION' then
        local office=resolve('story_office',row.entity_id,row.position_id)
        result.office=office.details; result.office_status=office.status
    end
    return result
end
