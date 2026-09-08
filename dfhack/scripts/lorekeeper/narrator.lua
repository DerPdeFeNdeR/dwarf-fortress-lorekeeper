-- Bounded voice capture and one durable narrator per fortress year.
--@module = true
local json=require('json')

local facets={'ANXIETY_PROPENSITY','ANGER_PROPENSITY','CHEER_PROPENSITY',
    'ORDERLINESS','ALTRUISM','BRAVERY','CRUELTY','DUTIFULNESS','FRIENDLINESS',
    'STRESS_VULNERABILITY','HUMOR','GREGARIOUSNESS','BASHFUL','ASSERTIVENESS',
    'CONFIDENCE','PRIDE','POLITENESS','IMAGINATION','ABSTRACT_INCLINED',
    'ART_INCLINED','CURIOUS','EMOTIONALLY_OBSESSIVE','PRIVACY'}

local mental_names={'LINGUISTIC_ABILITY','ANALYTICAL_ABILITY','CREATIVITY','MEMORY'}

function relative_attribute(value,median)
    if type(value)~='number' or value<0 or type(median)~='number' or median<=0 then return 'unknown' end
    -- Editorial voice bands, not DF description tiers or an intelligence diagnosis.
    if value<median*0.75 then return 'lower' end
    if value>median*1.25 then return 'higher' end
    return 'typical'
end

function mental_attributes(unit,read)
    local result={version=1,attributes={},status='unavailable'}
    if not unit or not unit.status.current_soul then return result end
    read=read or function(subject,name)
        local id=df.mental_attribute_type[name]
        local caste=df.global.world.raws.creatures.all[subject.race].caste[subject.caste]
        return dfhack.units.getMentalAttrValue(subject,id),caste.attributes.ment_att_range[id][3]
    end
    local count=0
    for _,name in ipairs(mental_names) do
        local ok,value,median=pcall(read,unit,name)
        if ok and type(value)=='number' and value>=0 then
            result.attributes[name]={value=value,caste_median=median,
                relative_level=relative_attribute(value,median)}
            count=count+1
        end
    end
    result.status=count==4 and 'available' or count>0 and 'partial' or 'unavailable'
    return result
end

function add_missing_mental_attributes(data,unit)
    if data.status~='selected' or data.mental_attributes then return false end
    -- Upgrade the already chosen dwarf, never replace them or guess by name.
    if not unit or unit.hist_figure_id~=data.histfig_id then unit=nil end
    data.mental_attributes=mental_attributes(unit)
    data.mental_attributes.captured_at={year=df.global.cur_year,tick=df.global.cur_year_tick}
    return true
end

function traits(personality)
    local result={}
    if not personality then return result end
    for _,name in ipairs(facets) do
        local ok,value=pcall(function() return personality.traits[name] end)
        if ok and type(value)=='number' then result[name]=value end
    end
    return result
end

function displayed_voice(data)
    if data.story and data.story~='' then return data.story_narrator end
    return data.narrator
end

function weight(events,year,site_id)
    local seen,count={},0
    for _,event in ipairs(events or {}) do
        if event.year==year and event.site_id==site_id and not seen[event.id] then
            seen[event.id]=true; count=count+1
        end
    end
    return 1+math.min(count,8) -- Quiet citizens retain a chance; prolific actors cannot dominate.
end

function consider(selection,candidate,candidate_weight,random)
    selection.total=selection.total+candidate_weight
    selection.count=selection.count+1
    if random(selection.total)<=candidate_weight then selection.chosen=candidate end
end

local function capture(unit,year,site_id,selection)
    if not unit then
        return {version=1,status='unavailable',site_id=site_id,year=year,
            reason='No eligible living adult dwarf citizen was available at selection.'}
    end
    local mind=unit.status.current_soul.personality
    local figure=df.historical_figure.find(unit.hist_figure_id)
    local birth_year=unit.birth_year or (figure and figure.birth_year)
    local age
    if type(birth_year)=='number' and birth_year>=0 and birth_year<=year then
        local years=year-birth_year
        local life_stage=years<1 and 'baby' or years<12 and 'child' or 'adult'
        local profession=dfhack.units.getProfessionName(unit)
        local stage_source='birth_year_estimate'
        if profession=='Dwarven Baby' then life_stage,stage_source='baby','unit_life_stage'
        elseif profession=='Dwarven Child' then life_stage,stage_source='child','unit_life_stage' end
        -- "older_adult" is our prose-delivery band, not a DF life stage.
        age={years=years,life_stage=life_stage,source=stage_source,
            narrative_band=years>=60 and life_stage=='adult' and 'older_adult' or life_stage}
    end
    local values={}
    for _,value in ipairs(mind.values) do
        if #values>=32 then break end
        table.insert(values,{name=df.value_type[value.type],strength=value.strength})
    end
    return {version=1,status='selected',year=year,site_id=site_id,
        unit_id=unit.id,histfig_id=unit.hist_figure_id,
        name=dfhack.df2utf(dfhack.units.getReadableName(unit,true)),
        personality_facets=traits(mind),values=values,age=age,mental_attributes=mental_attributes(unit),
        captured_at={year=df.global.cur_year,tick=df.global.cur_year_tick},
        selection={method='weighted_reservoir',eligible=selection.count,
            total_weight=selection.total,max_event_bonus=8},
        limitations={'Voice observed at selection, not proof of past personality or eyewitness presence.',
            'Only explicit personal values are supplied; cultural defaults are unresolved.'}}
end

local function read_saved(path)
    local file,err,code=io.open(path,'r')
    if file then
        local raw=file:read(32769); file:close()
        return raw
    end
    if code~=2 then error('Cannot read saved annual narrator: '..tostring(err)) end
end

local function eligible(unit)
    local raw=unit and df.global.world.raws.creatures.all[unit.race]
    return unit and raw and raw.creature_id=='DWARF' and unit.hist_figure_id>=0 and
        unit.status.current_soul and dfhack.units.isCitizen(unit) and
        dfhack.units.isAlive(unit) and dfhack.units.isAdult(unit)
end

function for_year(directory,year,site_id,by_figure,write,read)
    local name=('%d-%d.narrator.json'):format(site_id,year)
    local raw=(read or read_saved)(directory..'/'..name)
    if raw then
        local ok,data=pcall(json.decode,raw)
        if not ok or #raw>32768 or type(data)~='table' or data.version~=1 or
            data.site_id~=site_id or data.year~=year or
            (data.status~='selected' and data.status~='unavailable') then
            error('Saved annual narrator is invalid; refusing to choose a different voice.')
        end
        if data.status=='selected' and (type(data.histfig_id)~='number' or data.histfig_id<0 or
            type(data.name)~='string' or data.name=='' or type(data.personality_facets)~='table') then
            error('Saved annual narrator identity is invalid; refusing to reroll.')
        end
        if not data.mental_attributes and data.status=='selected' then
            -- Windows rename does not replace existing files. Keep the original
            -- choice immutable; one new companion holds the added observation.
            local extra_name=name:gsub('%.json$','.mental.json')
            local extra_raw=(read or read_saved)(directory..'/'..extra_name)
            if extra_raw then
                local extra_ok,extra=pcall(json.decode,extra_raw)
                if not extra_ok or #extra_raw>32768 or type(extra)~='table' or
                    extra.year~=year or extra.site_id~=site_id or extra.histfig_id~=data.histfig_id or
                    type(extra.mental_attributes)~='table' then
                    error('Saved narrator mental attributes are invalid; refusing to replace them.')
                end
                data.mental_attributes=extra.mental_attributes
            else
                local unit=type(data.unit_id)=='number' and df.unit.find(data.unit_id) or nil
                add_missing_mental_attributes(data,unit)
                write({version=1,year=year,site_id=site_id,histfig_id=data.histfig_id,
                    mental_attributes=data.mental_attributes},extra_name)
            end
        end
        return data
    end
    local selection={count=0,total=0}
    -- Bounded batches outside UI activation, with a 2 ms target per frame.
    local units=df.global.world.units.active
    local size=#units
    local visited,started=0,os.clock()
    for i=0,size-1 do
        if i>=#units then break end
        local unit=units[i]
        if eligible(unit) then
            consider(selection,unit.id,weight(by_figure[unit.hist_figure_id],year,site_id),math.random)
        end
        visited=visited+1
        if visited>=32 or os.clock()-started>=0.002 then
            coroutine.yield(); visited=0; started=os.clock()
        end
    end
    local unit=selection.chosen and df.unit.find(selection.chosen)
    if not eligible(unit) then unit=nil end
    local data=capture(unit,year,site_id,selection)
    if #json.encode(data)>32768 then error('Annual narrator exceeds 32 KiB') end
    write(data,name) -- Persist BEFORE requesting generation; retries cannot reroll.
    return data
end

if dfhack_flags.module then return end
print('The Lorekeeper: narrator is an internal module.')
