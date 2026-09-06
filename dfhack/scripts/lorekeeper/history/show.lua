-- Display history prepared outside the game thread.
local gui = require('gui')
local widgets = require('gui.widgets')
local requests = reqscript('lorekeeper/view_request')
local display_text = reqscript('lorekeeper/display_text')

LorekeeperHistoryWindow = defclass(LorekeeperHistoryWindow, widgets.Window)
LorekeeperHistoryWindow.ATTRS {frame_title='The Lorekeeper: History',
    frame={w=78,h=30}, resizable=true, resize_min={w=60,h=12}}

function LorekeeperHistoryWindow:init()
    self.page = 0
    local unit = dfhack.gui.getSelectedUnit(true)
    if unit then
        self.unit_id = unit.id
        self.name = dfhack.units.getReadableName(unit, true)
        self.request_ok, self.request_error = requests.request(self.unit_id)
    end
    self:addviews{
        widgets.List{view_id='content',frame={t=0,l=0,r=0,b=2},scroll_keys={}},
        widgets.HotkeyLabel{frame={b=0,l=0},key='CUSTOM_R',label='Refresh',
            on_activate=self:callback('refresh')},
        widgets.HotkeyLabel{frame={b=0,l=15},key='CUSTOM_N',label='Next',
            on_activate=function() self.page=self.page+1; self:refresh() end},
        widgets.HotkeyLabel{frame={b=0,l=28},key='CUSTOM_P',label='Previous',
            on_activate=function() self.page=math.max(0,self.page-1); self:refresh() end},
        widgets.HotkeyLabel{frame={b=1,l=0},key='CUSTOM_CTRL_C',label='Copy',
            on_activate=self:callback('copy_history')},
        widgets.HotkeyLabel{frame={b=1,l=20},key='LEAVESCREEN',label='Close',
            on_activate=function() self.parent_view:dismiss() end},
    }
    self:refresh()
end

function LorekeeperHistoryWindow:refresh()
    local choices = {}
    local function add(text)
        for _, line in ipairs(display_text.wrap(text)) do
            table.insert(choices, {text=line})
        end
    end
    if not self.unit_id then
        add('No unit is selected.')
    else
        table.insert(choices,{text='Name: ' .. self.name})
        local data = requests.read(self.unit_id)
        if not requests.worker_available() then add('Background watcher unavailable. Prepared history remains readable.') end
        if not self.request_ok then add('Request failed: ' .. tostring(self.request_error)) end
        if not data then
            add('History queued. Waiting for the background watcher; press R to check.')
        else
            add('Status: ' .. data.state)
            if data.request and (data.request.year ~= df.global.cur_year or
                    data.request.tick ~= df.global.cur_year_tick) then
                add(('Prepared for year %d, tick %d; later records may not be included.'):format(
                    data.request.year, data.request.tick))
            end
            if data.story then
                if data.story_revision ~= data.revision then add('Previous story; newer history is being prepared.') end
                add(data.story)
            end
            if data.error then add(data.error) end
            self.page = math.min(self.page, math.max(0,(data.pages or 1)-1))
            add(('Timeline: %d records, %d events. Page %d of %d.'):format(
                data.record_count or 0,data.event_count or 0,self.page+1,math.max(1,data.pages or 0)))
            local page = requests.read(self.unit_id,self.page,data.revision)
            if page then for _,line in ipairs(page.lines) do add(line) end end
        end
    end
    self.subviews.content:setChoices(choices)
end

function LorekeeperHistoryWindow:copy_history()
    local lines={}
    for _,choice in ipairs(self.subviews.content:getChoices()) do table.insert(lines,choice.text) end
    dfhack.internal.setClipboardTextCp437Multiline(table.concat(lines,'\n'))
end

LorekeeperHistoryScreen=defclass(LorekeeperHistoryScreen,gui.ZScreenModal)
LorekeeperHistoryScreen.ATTRS {focus_path='lorekeeper/history/show'}
function LorekeeperHistoryScreen:init()
    self:addviews{LorekeeperHistoryWindow{view_id='window'}}
end
if view then view:dismiss() end
view=LorekeeperHistoryScreen{}:show()
