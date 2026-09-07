-- Bounded on-demand event detail resolution. Never scan combat reports or units.
--@module = true
local field=reqscript('lorekeeper/references').field

local function weapon_description(raw)
    if type(raw.item_type)~='number' or raw.item_type<0 then return end
    local definition=dfhack.items.getSubtypeDef(raw.item_type,raw.item_subtype or -1)
    local name=definition and field(definition,'name')
    if not name or name=='' then return end
    local material
    if type(raw.mattype)=='number' and raw.mattype>=0 then
        material=dfhack.matinfo.decode(raw.mattype,raw.matindex)
    end
    return dfhack.df2utf((material and material:toString()..' ' or '')..name)
end

function capture(source,find,describe)
    if source.kind~='death' and source.kind~='wounding' then return end
    find=find or df.history_event.find
    describe=describe or weapon_description
    local event=find(source.id)
    if not event or event.id~=source.id then return {status='unavailable'} end
    local token=df.history_event_type[event:getType()]
    if (source.kind=='death' and token~='HIST_FIGURE_DIED') or
        (source.kind=='wounding' and token~='HIST_FIGURE_WOUNDED') then
        return {status='wrong_event_type'}
    end
    local result={version=1,status='available',source_event_id=source.id}
    if source.kind=='death' then
        result.death_cause=field(df.death_type,field(event,'death_cause'))
        result.weapons={}
        local weapon=field(event,'weapon')
        for _,prefix in ipairs({'','shooter_'}) do
            local raw={role=prefix=='' and 'impact_item' or 'launcher'}
            for _,key in ipairs({'item','item_type','item_subtype','mattype','matindex'}) do
                raw[key]=field(weapon,prefix..key)
            end
            if type(raw.item_type)=='number' and raw.item_type>=0 then
                local ok,name=pcall(describe,raw)
                raw.name=ok and name or nil
                raw.status=raw.name and 'resolved' or 'unavailable'
                table.insert(result.weapons,raw)
            end
        end
    else
        result.injury_type=field(df.history_damage_type,field(event,'injury_type'))
        result.part_lost=field(event,'part_lost')
        local race=field(df.global.world.raws.creatures.all,field(event,'woundee_race'))
        local caste=race and field(race.caste,field(event,'woundee_caste'))
        local part=caste and field(caste.body_info.body_parts,field(event,'body_part'))
        local name=part and field(part.name_singular,0)
        if name and type(name)~='string' then name=field(name,'value') end
        if type(name)=='string' and name~='' then result.body_part=dfhack.df2utf(name) end
    end
    return result
end
