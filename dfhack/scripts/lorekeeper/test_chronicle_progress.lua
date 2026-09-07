-- Focused, pure reader checks; no collection, model calls, or game mutations.
local progress=reqscript('lorekeeper/chronicle_progress')
local previous={request_file='old.request.json',story='Saved prose',state='ready'}
local job={key='new-draft'}
assert(progress.waiting(job,previous))
assert(progress.message(job,previous)=='Preparing the requested draft. Showing previous draft.')
job.request_file='new.request.json'
assert(progress.waiting(job,previous))
assert(progress.message(job,previous)=='Draft queued; waiting for the writer. Showing previous draft.')
assert(progress.waiting(job,nil))
for _,state in ipairs({'processing','failed','ready'}) do
    local current={request_file=job.request_file,state=state}
    assert(not progress.waiting(job,current))
    assert(progress.message(job,current)==nil)
end
assert(progress.message(nil,previous)==nil)
print('PASS: Chronicle request progress distinguishes old prose, queued work, and matching results.')
