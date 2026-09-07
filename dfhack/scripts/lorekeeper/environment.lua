-- Shared, bounded atmospheric observations. No map scans or model execution.
--@module = true
local json=require('json')
state=state or nil
last_error=last_error or nil
local SAMPLE_TICKS=120
local DAY_TICKS=1200

function should_sample(previous,now)
    return not previous or now<previous or now-previous>=SAMPLE_TICKS
end

function should_record(previous,weather,now)
    return not previous or previous.weather~=weather or now-previous.time>=DAY_TICKS
end

function geography()
    local site=df.world_site.find(df.global.plotinfo.site_id)
    if not site then return {status='unavailable'} end
    local x,y=site.pos.x,site.pos.y
    local biome=dfhack.maps.getRegionBiome(x,y)
    local region=biome and df.global.world.world_data.regions[biome.region_id]
    return {status='available',scope='site_anchor_world_tile',x=x,y=y,
        biome=df.biome_type[dfhack.maps.getBiomeType(x,y)],
        region_name=region and dfhack.df2utf(dfhack.translation.translateName(region.name)),
        note='Representative world tile, not every embark tile or underground room.'}
end

local function append(path,row)
    local encoded=json.encode(row,{pretty=false})..'\n'
    if #encoded>4096 then error('Environment row exceeds 4 KiB') end
    local file,err=io.open(path,'ab')
    if not file then error(err) end
    local wrote,write_error=file:write(encoded)
    local size=file:seek('end')
    local closed,close_error=file:close()
    if not wrote or not closed or not size then error(write_error or close_error or 'Environment seek failed') end
    return size
end

function observe(session)
    local year,tick=df.global.cur_year,df.global.cur_year_tick
    local now=year*403200+tick
    if not state or state.branch~=session.branch or state.site_id~=session.site_id then
        local ok,place=pcall(geography)
        state={branch=session.branch,site_id=session.site_id,years={},
            geography=ok and place or {status='unavailable'},samples=0,records=0}
    end
    if not should_sample(state.checked,now) then return end
    state.checked=now -- Failed I/O is retried on the next interval, never each frame.
    local ok,err=pcall(function()
        local weather=df.weather_type[dfhack.world.ReadCurrentWeather()] or 'Unknown'
        state.samples=state.samples+1; state.weather=weather
        local entry=state.years[year]
        if not entry then
            local directory=dfhack.getSavePath()..'/lorekeeper-environment'
            if not dfhack.filesystem.mkdir_recursive(directory) and not dfhack.filesystem.isdir(directory) then
                error('Could not create environment directory')
            end
            local filename=('%d-%s-%d.jsonl'):format(session.site_id,session.branch,year)
            entry={file=filename,rows=0,bytes=0}
            entry.bytes=append(directory..'/'..filename,{schema_version=1,kind='geography',
                site_id=session.site_id,branch=session.branch,year=year,
                save_id=df.global.world.cur_savegame.save_dir,
                captured_tick=tick,geography=state.geography,
                source={df_version=dfhack.getDFVersion(),dfhack_version=dfhack.getDFHackVersion()}})
            state.years[year]=entry
            for old in pairs(state.years) do if old<year-8 then state.years[old]=nil end end
        end
        if not should_record(entry.previous,weather,now) then return end
        if entry.rows>=4096 or entry.bytes>2000000-4096 then error('Environment year storage limit reached') end
        entry.bytes=append(dfhack.getSavePath()..'/lorekeeper-environment/'..entry.file,
            {kind='weather',year=year,tick=tick,weather=weather})
        entry.rows=entry.rows+1; entry.previous={weather=weather,time=now}
        state.records=state.records+1
    end)
    last_error=not ok and tostring(err) or nil
end

function reference(session,year)
    local entry=state and state.branch==session.branch and state.site_id==session.site_id and state.years[year]
    if not entry then return end
    return {version=1,file=entry.file,bytes=entry.bytes,site_id=session.site_id,
        branch=session.branch,year=year}
end

if not dfhack_flags.module then
    print('The Lorekeeper: environment '..(state and 'observing' or 'not started'))
    if state then
        print(('  samples: %d; records: %d; weather: %s'):format(state.samples,state.records,state.weather or 'Unknown'))
        print('  biome: '..tostring(state.geography.biome or 'unavailable'))
        if state.checked then
            print(('  last_check: year %d, tick %d'):format(math.floor(state.checked/403200),state.checked%403200))
        end
        print('  Sampling: every 120 game ticks; central weather cell only.')
    end
    print('  Moon phase: unavailable (not verified).')
    if last_error then dfhack.printerr(last_error) end
end
