-- Request identity must take precedence over the saved chapter being displayed.
--@ module = true
function waiting(job,data)
    return job and (not job.request_file or not data or data.request_file~=job.request_file)
end

function message(job,data)
    if not waiting(job,data) then return nil end
    local text=job.request_file and 'Draft queued; waiting for the writer.' or 'Preparing the requested draft.'
    if data and data.story and data.story~='' then text=text..' Showing previous draft.' end
    return text
end

if not dfhack_flags.module then qerror('Use lorekeeper/chronicles.') end
