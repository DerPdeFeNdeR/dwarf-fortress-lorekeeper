-- Annual chapter requests; all model execution remains outside DFHack.
--@module = true
local json=require('json')
local index=reqscript('lorekeeper/event_index')
local references=reqscript('lorekeeper/references')
local culture=reqscript('lorekeeper/culture_index')

runtime=runtime or nil
timer=timer or nil
last_error=last_error or nil

function directory()
    return dfhack.getSavePath()..'/lorekeeper-chronicles'
end

function read_file(name,limit)
    if not name:match('^[%w%.%-]+$') then return end
    local file=io.open(directory()..'/'..name,'r')
    if not file then return end
    local raw=file:read((limit or 32768)+1); file:close()
    if not raw or #raw>(limit or 32768) then return end
    local ok,data=pcall(json.decode,raw)
    if ok then return data end
end

function advance(state,year,tick)
    local now=year*403200+tick
    if now<state.time then return nil,'time_reversal' end
    local closed={}
    for y=math.max(state.year,year-8),year-1 do table.insert(closed,y) end
    local skipped=math.max(0,year-state.year-8)
    state.year=year; state.time=now
    return closed,nil,skipped
end

local function new_session()
    local year,tick=df.global.cur_year,df.global.cur_year_tick
    return {branch=tostring(os.time())..'-'..tostring(dfhack.getTickCount()),
        site_id=df.global.plotinfo.site_id,year=year,time=year*403200+tick,
        started_year=year,started_tick=tick,pending={},sequence=0}
end

function stop()
    if timer then dfhack.timeout_active(timer,nil) end
    timer=nil; runtime=nil
    culture.stop()
end

local function write_request(payload,name)
    local encoded=json.encode(payload,{pretty=false})
    if #encoded>131072 then error('Annual chapter input exceeds 128 KiB') end
    local path=directory()
    if not dfhack.filesystem.mkdir_recursive(path) and not dfhack.filesystem.isdir(path) then
        error('Could not create chronicle directory')
    end
    local target=path..'/'..name
    local file,err=io.open(target..'.tmp','w')
    if not file then error(err) end
    local wrote,write_error=file:write(encoded)
    local closed,close_error=file:close()
    if not wrote or not closed then error(write_error or close_error) end
    local renamed,rename_error=os.rename(target..'.tmp',target)
    if not renamed then error(rename_error) end
end

function retry(data)
    if not data or data.state~='failed' or type(data.request_file)~='string' or
        not data.request_file:match('^[%w%-]+%.request%.json$') then
        return nil,'Only failed chapters can be retried.'
    end
    local payload=read_file(data.request_file,131072)
    if not payload then return nil,'Original chapter request unavailable.' end
    local suffix=tostring(os.time())..'-'..tostring(dfhack.getTickCount())
    payload.retry_nonce=suffix
    local name=data.request_file:gsub('%.request%.json$','-retry-'..suffix..'.request.json')
    local ok,err=pcall(write_request,payload,name)
    return ok,err
end

local function export_request(job)
    local state=index.state
    local resolver=references.new(references.game_providers(),256)
    local site=resolver:resolve('site',runtime.site_id)
    local bucket=state.site_years[job.year] or {}
    local selected=index.select_events(bucket,16)
    local performances,culture_truncated=culture.select(culture.state,job.year)
    local payload={schema_version=1,site_id=runtime.site_id,
        site_name=site.details and site.details.name or 'Unnamed fortress',
        save_id=df.global.world.cur_savegame.save_dir,branch=runtime.branch,
        year=job.year,kind=job.kind,captured_year=df.global.cur_year,
        captured_tick=df.global.cur_year_tick,events={},cultural_events={},
        source={df_version=dfhack.getDFVersion(),dfhack_version=dfhack.getDFHackVersion()},
        coverage={supported_types_only=true,index_errors=state.errors,
            retained_events=#bucket,selected_events=#selected,
            truncated=state.site_truncated[job.year] or #bucket>#selected,
            started_year=runtime.started_year,started_tick=runtime.started_tick,
            midyear_start=job.year==runtime.started_year and runtime.started_tick>0,
            unavailable_year=job.year<df.global.cur_year-1,
            separate_load_branch=true,skipped_years=runtime.skipped_years or 0,
            culture_scanned=culture.state.scanned,culture_errors=culture.state.errors,
            culture_selected=#performances,culture_truncated=culture_truncated}}
    for _,event in ipairs(selected) do
        table.insert(payload.events,index.enrich(event,resolver))
        coroutine.yield() -- At most one event's bounded name resolution per frame.
    end
    for _,event in ipairs(performances) do
        table.insert(payload.cultural_events,culture.enrich(event,resolver))
        coroutine.yield()
    end
    runtime.sequence=runtime.sequence+1
    payload.nonce=tostring(os.time())..'-'..runtime.sequence
    local base=('%d-%s-%d-%s'):format(payload.site_id,payload.branch,payload.year,payload.kind)
    write_request(payload,base..'-'..payload.nonce..'.request.json')
end

local function pump()
    timer=nil
    if not dfhack.isMapLoaded() then stop(); return end
    if runtime and runtime.site_id~=df.global.plotinfo.site_id then index.stop(); runtime=nil end
    if not runtime then runtime=new_session() end
    local closed,reset,skipped=advance(runtime,df.global.cur_year,df.global.cur_year_tick)
    if reset then runtime=new_session(); index.stop(); closed={} end
    runtime.skipped_years=(runtime.skipped_years or 0)+(skipped or 0)
    for _,year in ipairs(closed) do table.insert(runtime.pending,{year=year,kind='final'}) end
    index.start()
    local culture_ready=culture.scan()
    if not runtime.capture and #runtime.pending>0 and index.state and
        index.state.scanned==#df.global.world.history.events and culture_ready then
        local job=runtime.pending[1]
        runtime.capture=coroutine.create(function() export_request(job) end)
    end
    if runtime.capture then
        local ok,err=coroutine.resume(runtime.capture)
        if not ok then
            last_error=tostring(err)
            runtime.capture=nil
            -- Leave the job queued for a later retry, without busy-looping.
            timer=dfhack.timeout(100,'frames',pump)
            return
        elseif coroutine.status(runtime.capture)=='dead' then
            table.remove(runtime.pending,1); runtime.capture=nil; last_error=nil
        end
    end
    timer=dfhack.timeout((runtime.capture or not culture_ready) and 1 or 100,'frames',pump)
end

function start()
    if not dfhack.isMapLoaded() or df.global.gamemode~=df.game_mode.DWARF then return end
    if not runtime then runtime=new_session() end
    if not timer or not dfhack.timeout_active(timer) then timer=dfhack.timeout(1,'frames',pump) end
end

function draft()
    start()
    if not runtime then return nil,'Load a fortress first.' end
    for _,job in ipairs(runtime.pending) do
        if job.kind=='draft' and job.year==df.global.cur_year then return true end
    end
    table.insert(runtime.pending,{year=df.global.cur_year,kind='draft'})
    return true
end

dfhack.onStateChange['lorekeeper.chronicle']=function(change)
    if change==SC_MAP_UNLOADED or change==SC_WORLD_UNLOADED then stop() end
end
if dfhack_flags.module then return end
start()
print('The Lorekeeper: annual chronicle monitor '..(runtime and 'running' or 'stopped'))
if last_error then print(last_error) end
