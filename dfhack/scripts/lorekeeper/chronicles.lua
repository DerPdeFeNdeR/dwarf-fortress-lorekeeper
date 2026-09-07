-- Browse annual fortress chapters without leaving the game.
local gui=require('gui')
local widgets=require('gui.widgets')
local chronicle=reqscript('lorekeeper/chronicle')
local display=reqscript('lorekeeper/display_text')
local requests=reqscript('lorekeeper/view_request')

ChroniclesWindow=defclass(ChroniclesWindow,widgets.Window)
ChroniclesWindow.ATTRS{frame_title='The Lorekeeper: Fortress Chronicles',frame={w=86,h=36}}
function ChroniclesWindow:init()
    self.page=1
    chronicle.start()
    self:addviews{
        widgets.Label{view_id='heading',frame={t=0,l=1,r=1},text='Fortress Chronicles',text_pen=COLOR_YELLOW},
        widgets.Label{view_id='status',frame={t=2,l=1,r=1},text='',text_pen=COLOR_GREY},
        widgets.List{view_id='content',frame={t=6,l=1,r=1,b=5},
            text_pen=COLOR_WHITE,cursor_pen=COLOR_WHITE,text_hpen=COLOR_WHITE},
        widgets.Label{frame={b=3,l=1},text='Based on game events, with imagined motives and interpretation.',text_pen=COLOR_DARKGREY},
        widgets.HotkeyLabel{view_id='draft',frame={b=1,l=1,w=24},key='CUSTOM_D',label='Year so far',on_activate=function()
            local ok,err=chronicle.draft(); self.message=ok and 'Draft requested; preparation runs in the background.' or err
            self:refresh(true)
        end},
        widgets.HotkeyLabel{view_id='retry',frame={b=1,l=28,w=26},key='CUSTOM_R',label='Retry failed chapter',
            enabled=function() return self.data and self.data.state=='failed' end,
            on_activate=function()
                local ok,err=chronicle.retry(self.data)
                self.message=ok and 'Retry requested.' or err; self:refresh(true)
            end},
        widgets.HotkeyLabel{view_id='previous',frame={b=0,l=1,w=24},key='CUSTOM_P',label='Previous chapter',on_activate=function()
            self.page=math.max(1,self.page-1); self.selected=nil; self:refresh(true)
        end},
        widgets.HotkeyLabel{view_id='next',frame={b=0,l=28,w=26},key='CUSTOM_N',label='Next chapter',on_activate=function()
            self.page=math.min(#(self.chapters or {}),self.page+1); self.selected=nil; self:refresh(true)
        end},
        widgets.HotkeyLabel{view_id='close',frame={b=1,r=1,w=12},key='LEAVESCREEN',label='Close',on_activate=function() self.parent_view:dismiss() end},
    }
    self:refresh(true)
end
function ChroniclesWindow:onRenderFrame(dc,rect)
    self.super.onRenderFrame(self,dc,rect)
    if dfhack.getTickCount()>=(self.next_check or 0) then
        self.next_check=dfhack.getTickCount()+1000; self:refresh()
    end
end
function ChroniclesWindow:refresh(force)
    local catalog=chronicle.read_file('index.json',65536) or {}
    self.chapters={}
    for _,row in ipairs(catalog.chapters or {}) do
        if row.site_id==df.global.plotinfo.site_id then table.insert(self.chapters,row) end
    end
    if self.selected then
        for i,row in ipairs(self.chapters) do if row.key==self.selected then self.page=i end end
    end
    self.page=math.max(1,math.min(self.page,#self.chapters))
    local entry=self.chapters[self.page]
    local data=entry and chronicle.read_file(entry.key..'.chapter.json',65536)
    self.data=data
    local worker_available=requests.worker_available()
    local signature=tostring(data and data.updated_at)..tostring(entry and entry.key)..tostring(self.message)..tostring(chronicle.last_error)..tostring(worker_available)
    if not force and signature==self.signature then return end
    self.signature=signature; self.selected=entry and entry.key
    local heading='Fortress Chronicles'
    local status=self.message or 'Finished chapters are written automatically after each year ends.'
    local body='Choose Year so far for a draft. You can close this window while the historian writes.'
    if data then
        heading=('%s: year %d (%s) — %d/%d'):format(data.site_name,data.year,
            data.kind=='draft' and 'Draft' or 'Annual chapter',self.page,#self.chapters)
        status=data.state=='ready' and 'Saved chapter. Coverage: supported retained events only.' or 'Historian: '..data.state
        if data.error then status=status..' — '..data.error end
        if data.coverage and (data.coverage.midyear_start or data.coverage.truncated or
            data.coverage.culture_truncated or (data.coverage.culture_errors or 0)>0 or data.coverage.unavailable_year) then
            status=status..' Incomplete coverage.'
        end
        if chronicle.runtime and data.branch~=chronicle.runtime.branch then status=status..' Earlier recording branch.' end
        body=data.story and data.story~='' and data.story or
            (data.state=='processing' and 'The historian is writing. You can keep playing while this finishes.' or
             'No supported events are available for this chapter yet.')
        if data.state~='ready' and data.story and data.story~='' then status=status..' Showing previous draft.' end
        local voice=reqscript('lorekeeper/narrator').displayed_voice(data)
        if voice and voice.status=='selected' then
            body='Narrated by '..voice.name..'\n\n'..body
        elseif voice and voice.status=='unavailable' then
            body='No eligible dwarf narrator was available; external chronicler.\n\n'..body
        end
    end
    if catalog.older_archived then status=status..' Showing the newest 100 chapters; older files remain archived.' end
    if not worker_available then status='Historian offline. Saved chapters remain readable.' end
    if chronicle.last_error then status='Chapter preparation failed: '..chronicle.last_error end
    self.subviews.heading:setText(table.concat(display.wrap(heading,78),'\n'))
    self.subviews.status:setText(table.concat(display.wrap(status,78),'\n'))
    local choices={}
    for _,line in ipairs(display.wrap(body,78)) do table.insert(choices,{text=line}) end
    self.subviews.content:setChoices(choices,force and 1 or self.subviews.content:getSelected())
end
ChroniclesScreen=defclass(ChroniclesScreen,gui.ZScreenModal)
ChroniclesScreen.ATTRS{focus_path='lorekeeper/chronicles'}
function ChroniclesScreen:init() self:addviews{ChroniclesWindow{view_id='window'}} end
if not dfhack.isMapLoaded() then qerror('Load a fortress first.') end
if view then view:dismiss() end
view=ChroniclesScreen{}:show()
