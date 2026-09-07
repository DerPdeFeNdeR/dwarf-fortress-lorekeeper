-- Bounded directional friendship observations, not dated friendship events.
--@ module = true
local field = reqscript('lorekeeper/references').field

function classify(love)
    if type(love) ~= 'number' or love < 50 or love > 100 then return nil end
    if love == 100 then return 'kindred_spirit' end
    if love >= 75 then return 'close_friend' end
    return 'friend'
end

function capture(vector, resolver)
    local rows, limitations = {}, {}
    if not vector then return rows, {'Friendship container unavailable.'} end
    local visited = 0
    for _,entry in ipairs(vector) do
        if visited >= 128 or #rows >= 32 then
            table.insert(limitations,'Friendship capture truncated (128 contacts / 32 friends).')
            break
        end
        visited = visited + 1
        local love = field(field(entry,'core'),'love')
        local kind = classify(love)
        if kind then
            local target = resolver:resolve('historical_figure',field(entry,'histfig_id'))
            table.insert(rows,{target_hf=target.id,kind=kind,love=love,
                target_name=target.details and target.details.name,
                reference_key=target.key,reference_status=target.status,
                observed_now=true,directional=true,
                classification_source='DFHack core_hf_relationshipst.love thresholds'})
        end
    end
    return rows, limitations
end
