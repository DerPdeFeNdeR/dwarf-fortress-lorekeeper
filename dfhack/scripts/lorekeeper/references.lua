-- Typed, bounded reference resolution. Cache lifetime is one profile capture.
--@module = true

function field(object, key)
    local ok, value = pcall(function() return object[key] end)
    if ok then return value end
end

local thought_types = {
    Death='historical_figure', UnexpectedDeath='historical_figure',
    WitnessDeath='incident', SawDeadBody='incident',
}

function thought_kind(name)
    return thought_types[name] or 'unresolved'
end

function new(providers, limit)
    local resolver = {records={}, cache={}, limit=limit or 160}
    function resolver:resolve(kind, id, extra, depth)
        depth = depth or 0
        local key = kind .. ':' .. tostring(id) .. ':' .. tostring(extra)
        if self.cache[key] then return self.cache[key] end
        local row = {key=key, kind=kind, id=id, extra=extra}
        if #self.records >= self.limit then row.status='budget_exhausted'; return row end
        table.insert(self.records, row)
        self.cache[key] = row
        if type(id) ~= 'number' or id < 0 or id % 1 ~= 0 then
            row.status = 'invalid_id'
        elseif depth > 2 then
            row.status = 'depth_exceeded'
        elseif not providers[kind] then
            row.status = 'unsupported_type'
        else
            -- Insert before following links so cycles never trigger repeat lookups.
            row.status = 'resolving'
            local ok, value = pcall(providers[kind], id, extra, function(k, i, e)
                return self:resolve(k, i, e, depth + 1)
            end)
            if not ok then row.status='lookup_error'
            elseif not value then row.status='missing'
            else
                row.status='resolved'
                row.details=value
            end
        end
        return row
    end
    return resolver
end

local function utf(text)
    return dfhack.df2utf(text)
end

function game_providers()
    local providers = {}
    providers.historical_figure = function(id)
        local object = df.historical_figure.find(id)
        if object then return {name=utf(dfhack.translation.translateName(object.name)),
            unit_id=object.unit_id} end
    end
    providers.unit = function(id)
        local object = df.unit.find(id)
        if object then return {name=utf(dfhack.units.getReadableName(object, true)),
            histfig_id=object.hist_figure_id, race=object.race, caste=object.caste} end
    end
    providers.incident = function(id, _, resolve)
        local object = df.incident.find(id)
        if not object then return end
        local victim = resolve('unit', object.victim)
        local hfid = field(field(object, 'victim_hf'), 'hfid')
        local historical_victim = resolve('historical_figure', hfid)
        local victim_details = victim.details or historical_victim.details
        return {victim_unit_id=object.victim, victim_reference=victim.key,
            victim_status=victim.status,
            victim_historical_reference=historical_victim.key,
            victim_name=victim_details and victim_details.name,
            victim_histfig_id=victim.details and victim.details.histfig_id or hfid,
            year=object.event_year, tick=object.event_time,
            death_cause_id=object.death_cause,
            site_reference=resolve('site', object.site).key}
    end
    providers.item = function(id)
        local object = df.item.find(id)
        if object then return {name=utf(dfhack.items.getDescription(object, 0, false))} end
    end
    providers.material = function(mat_type, mat_index)
        local material = dfhack.matinfo.decode(mat_type, mat_index)
        if material then return {name=utf(material:toString()), token=material:getToken()} end
    end
    for kind, type_name in pairs({site='world_site', entity='historical_entity',
            poetic_form='poetic_form', musical_form='musical_form', dance_form='dance_form'}) do
        providers[kind] = function(id)
            local object = df[type_name].find(id)
            if object then return {name=utf(dfhack.translation.translateName(object.name, true))} end
        end
    end
    providers.creature = function(id)
        local object = df.global.world.raws.creatures.all[id]
        if object then return {name=utf(object.name[0]), token=object.creature_id} end
    end
    providers.plant = function(id)
        local object = df.global.world.raws.plants.all[id]
        if object then return {name=utf(object.name), token=object.id} end
    end
    for kind, vector in pairs({color='colors', shape='shapes'}) do
        providers[kind] = function(id)
            local object = df.global.world.raws.descriptors[vector][id]
            if object then return {name=utf(object.name), token=object.id} end
        end
    end
    providers.item_type = function(id, subtype)
        local name = df.item_type[id]
        if not name then return end
        if subtype and subtype >= 0 then
            local definition = dfhack.items.getSubtypeDef(id, subtype)
            if definition then return {name=utf(definition.name), item_type=name} end
            return nil
        end
        return {name=name}
    end
    return providers
end

function preference_targets(row, name)
    -- Preference fields overlap in DF unions. Only resolve fields active for the type.
    if name == 'LikeMaterial' or name == 'LikeFood' then
        return {{kind='material', id=row.mattype, extra=row.matindex}}
    elseif name == 'LikeCreature' or name == 'HateCreature' then
        return {{kind='creature', id=row.creature_id}}
    elseif name == 'LikePlant' or name == 'LikeTree' then
        return {{kind='plant', id=row.plant_id}}
    elseif name == 'LikeItem' then
        return {{kind='item_type', id=row.item_type, extra=row.item_subtype}}
    end
    local fields = {LikeColor={'color','color_id'}, LikeShape={'shape','shape_id'},
        LikePoeticForm={'poetic_form','poetic_form_id'},
        LikeMusicalForm={'musical_form','musical_form_id'}, LikeDanceForm={'dance_form','dance_form_id'}}
    local mapping = fields[name]
    if mapping then return {{kind=mapping[1], id=row[mapping[2]]}} end
    return {{kind='unresolved', id=row.type}}
end
