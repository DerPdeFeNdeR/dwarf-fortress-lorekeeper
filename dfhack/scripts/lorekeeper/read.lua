-- Read the selected dwarf's Memoire. Technical history is optional.
local gui = require('gui')
local widgets = require('gui.widgets')
local requests = reqscript('lorekeeper/view_request')
local text = reqscript('lorekeeper/reader_text')
local display = reqscript('lorekeeper/display_text')

MemoireWindow = defclass(MemoireWindow, widgets.Window)
MemoireWindow.ATTRS{frame_title='The Lorekeeper: Memoire', frame={w=78,h=34},
    resizable=true, resize_min={w=72,h=22}}

function MemoireWindow:init()
    local unit = dfhack.gui.getSelectedUnit(true)
    self.unit_id = unit and unit.id
    self.page = 0
    self.chapter_key = 'intro'
    self:addviews{
        widgets.Label{frame={t=0,l=1,r=1}, text=unit and dfhack.units.getReadableName(unit,true) or
            'Select a dwarf, then open Lorekeeper.', text_pen=COLOR_YELLOW},
        widgets.Label{view_id='status',frame={t=2,l=1,r=1},text='',text_pen=COLOR_GREY},
        widgets.List{view_id='content',frame={t=4,l=1,r=1,b=6},
            text_pen=COLOR_WHITE,cursor_pen=COLOR_WHITE,text_hpen=COLOR_WHITE},
        widgets.Label{frame={b=3,l=1},text='Based on game events, with imagined motives\nand interpretation.',
            text_pen=COLOR_DARKGREY},
        widgets.HotkeyLabel{frame={b=1,l=1,w=18},key='CUSTOM_U',label='U Update',
            enabled=function() return self.unit_id ~= nil and
                (not text.pending(self.data,self.requested) or not self.available or self.request_error ~= nil) end,
            on_activate=self:callback('update_memoire')},
        widgets.HotkeyLabel{frame={b=1,l=22,w=18},key='CUSTOM_D',label='D Details',
            on_activate=function() self.details=not self.details; self:refresh(true,true) end},
        widgets.HotkeyLabel{frame={b=1,r=1,w=14},key='LEAVESCREEN',label='Esc Close',
            on_activate=function() self.parent_view:dismiss() end},
        widgets.HotkeyLabel{frame={b=0,l=1},key='CUSTOM_P',label='Previous',
            on_activate=function() self:turn_page(-1) end},
        widgets.HotkeyLabel{frame={b=0,l=25},key='CUSTOM_N',label='Next',
            on_activate=function() self:turn_page(1) end},
        widgets.HotkeyLabel{frame={b=0,r=1},key='CUSTOM_I',label='Introduction',
            visible=function() return not self.details end,
            on_activate=function() self.chapter_key='intro'; self:refresh(true,true) end},
    }
    self:update_memoire()
end

function MemoireWindow:turn_page(delta)
    if self.details then
        self.page=math.max(0,self.page+delta)
    else
        local chapters=self.data and self.data.chapters or {}
        local index=self.chapter_key=='intro' and 0 or 1
        for i,row in ipairs(chapters) do if row.key==self.chapter_key then index=i end end
        index=math.max(1,math.min(#chapters,index+delta))
        self.chapter_key=chapters[index] and chapters[index].key
    end
    self:refresh(true,true)
end

function MemoireWindow:update_memoire()
    if self.unit_id then
        local ok, err, requested = requests.request(self.unit_id)
        self.request_error = not ok and tostring(err) or nil
        if ok then self.requested = requested end
    end
    self:refresh(true)
end

function MemoireWindow:onRenderFrame(dc, rect)
    self.super.onRenderFrame(self,dc,rect)
    local width = math.max(20,math.min(80,(self.subviews.content.frame_body.width or 68)-2))
    local now = dfhack.getTickCount()
    if width ~= self.width or now >= (self.next_check or 0) then
        local resized = width ~= self.width
        self.width = width
        self.next_check = now + 1000
        self:refresh(resized)
    end
end

function MemoireWindow:refresh(force, reset_scroll)
    self.data = self.unit_id and requests.read(self.unit_id) or nil
    self.profile = self.data and self.data.request and
        requests.read_profile(self.unit_id, self.data.request.profile_file) or nil
    self.available = self.unit_id and requests.worker_available() or false
    local data = self.data
    local signature = table.concat({tostring(data and data.updated_at),tostring(data and data.state),
        tostring(data and data.revision),tostring(data and data.story_revision),tostring(self.available),
        tostring(self.request_error), tostring(self.data and self.data.request and self.data.request.profile_file),
        tostring(self.profile and self.profile.captured_at and self.profile.captured_at.tick)}, '|')
    if not force and signature == self.signature then return end
    self.signature = signature
    local status = self.unit_id and text.status(data,self.requested,self.available,self.request_error) or 'No dwarf selected.'
    self.subviews.status:setText(table.concat(display.wrap(status,self.width or 68),'\n'))
    local lines = text.lines(data,self.width or 68)
    if not self.details and data and data.chapters and #data.chapters>0 then
        local selected,index=text.selected_chapter(data.chapters,self.chapter_key)
        if selected then
            self.chapter_key=selected.key
            local chapter=requests.read_chapter(self.unit_id,selected.file)
            lines=display.wrap(selected.title .. (' (%d/%d)\n\n'):format(index,#data.chapters) ..
                (chapter and chapter.text or 'This saved chapter could not be read.'),self.width or 68)
            if selected.key == 'intro' then
                local relationship_lines=text.relationship_lines(self.profile, self.width or 68)
                if #relationship_lines > 0 then table.insert(lines, '') end
                for _, line in ipairs(relationship_lines) do table.insert(lines, line) end
            end
        else
            lines=display.wrap('Introduction\n\nThe introduction is not ready yet. '..
                'Saved monthly chapters can still be browsed.',self.width or 68)
            local relationship_lines=text.relationship_lines(self.profile, self.width or 68)
            if #relationship_lines > 0 then table.insert(lines, '') end
            for _, line in ipairs(relationship_lines) do table.insert(lines, line) end
        end
    end
    if self.details then
        lines = {}
        local function add(value)
            for _,line in ipairs(display.wrap(value,self.width or 68)) do table.insert(lines,line) end
        end
        add('Technical history')
        if self.request_error then add(self.request_error) end
        if data then
            add('Status: ' .. tostring(data.state))
            if data.chapters_truncated then add('Showing the newest 99 monthly chapters; older files remain on disk.') end
            if data.error then add(data.error) end
            local coverage=data.historical_event_coverage
            if coverage and coverage.status then
                add(('Historical event index: %s; scanned %d/%d; errors %d.'):format(
                    coverage.status,coverage.scanned or 0,coverage.total or 0,coverage.errors or 0))
                if coverage.truncated or coverage.subject_truncated then
                    add('Historical event coverage is capped; this is not a complete life history.')
                end
            end
            local pages=math.max(1,data.pages or 0)
            self.page=math.min(self.page,pages-1)
            add(('Timeline: %d records, %d events. Page %d of %d.'):format(
                data.record_count or 0,data.event_count or 0,self.page+1,pages))
            if data.request then add(('Prepared for year %d, tick %d.'):format(data.request.year,data.request.tick)) end
            local page=data.revision and requests.read(self.unit_id,self.page,data.revision)
            if page then for _,line in ipairs(page.lines or {}) do add(line) end end
        else add('No prepared timeline is available yet.') end
    end
    local choices={}
    for _,line in ipairs(lines) do table.insert(choices,{text=line}) end
    self.subviews.content:setChoices(choices,reset_scroll and 1 or self.subviews.content:getSelected())
end

MemoireScreen = defclass(MemoireScreen,gui.ZScreenModal)
MemoireScreen.ATTRS{focus_path='lorekeeper/read'}
function MemoireScreen:init()
    self:addviews{MemoireWindow{view_id='window'}}
end
if view then view:dismiss() end
view=MemoireScreen{}:show()
