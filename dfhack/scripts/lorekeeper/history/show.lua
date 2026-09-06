-- Display a selected dwarf's cached story and grouped history timeline.
--
-- Run: lorekeeper/history/show

local gui = require('gui')
local widgets = require('gui.widgets')
local snapshot = reqscript('lorekeeper/snapshot')
local history = reqscript('lorekeeper/history')
local translation = reqscript('lorekeeper/translation')

local CONTENT_WIDTH = 72

local function add_header(choices, text)
    table.insert(choices, {text=text, pen=COLOR_LIGHTCYAN})
end

local function add_wrapped(choices, text)
    local line = ''
    for word in text:gmatch('%S+') do
        if #line > 0 and #line + #word + 1 > CONTENT_WIDTH then
            table.insert(choices, {text=line})
            line = word
        elseif #line == 0 then
            line = word
        else
            line = line .. ' ' .. word
        end
    end
    if #line > 0 then
        table.insert(choices, {text=line})
    end
end

local function add_event(choices, index, event)
    if event.kind == 'baseline' then
        local time = event.record.ingame_time
        local data = event.record.snapshot
        table.insert(choices, {text=('[%d] Baseline: year %d, tick %d; stress %s; thoughts %d'):format(
            index, time.year, time.year_tick,
            tostring(data.mental_state.stress or '<none>'), #data.thoughts)})
    elseif event.kind == 'stress_trend' then
        local start_time = event.start_record.ingame_time
        local end_time = event.end_record.ingame_time
        table.insert(choices, {text=('[%d] Stress trend: %d to %d across %d snapshot(s)'):format(
            index, event.from_stress, event.to_stress, event.snapshot_count)})
        table.insert(choices, {text=('    Year %d tick %d to year %d tick %d'):format(
            start_time.year, start_time.year_tick,
            end_time.year, end_time.year_tick)})
    else
        local time = event.record.ingame_time
        table.insert(choices, {text=('[%d] Change: year %d, tick %d'):format(
            index, time.year, time.year_tick)})
        for _, change in ipairs(event.changes) do
            table.insert(choices, {text='    - ' .. change})
        end
    end
end

LorekeeperHistoryWindow = defclass(LorekeeperHistoryWindow, widgets.Window)
LorekeeperHistoryWindow.ATTRS {
    frame_title='The Lorekeeper: History',
    frame={w=78, h=30},
    resizable=true,
    resize_min={w=48, h=12},
}

function LorekeeperHistoryWindow:init()
    self:addviews{
        widgets.List{
            view_id='content',
            frame={t=0, l=0, r=0, b=2},
            scroll_keys={},
        },
        widgets.HotkeyLabel{
            frame={b=0, l=0},
            key='CUSTOM_R',
            label='Refresh ',
            auto_width=true,
            on_activate=self:callback('refresh'),
        },
        widgets.HotkeyLabel{
            frame={b=0, l=18},
            key='CUSTOM_CTRL_C',
            label='Copy ',
            auto_width=true,
            on_activate=self:callback('copy_history'),
        },
        widgets.HotkeyLabel{
            frame={b=0, l=32},
            key='LEAVESCREEN',
            label='Close ',
            auto_width=true,
            on_activate=function() self.parent_view:dismiss() end,
        },
    }

    self:refresh()
end

function LorekeeperHistoryWindow:refresh()
    local choices = {}
    local selected = snapshot.capture_selected_unit()
    if not selected then
        table.insert(choices, {text='No unit is currently selected.', pen=COLOR_YELLOW})
        self.subviews.content:setChoices(choices)
        return
    end

    table.insert(choices, {text=('Name: %s'):format(dfhack.utf2df(selected.identity.name)),
        pen=COLOR_LIGHTCYAN})
    local records, error_message = history.load_snapshots(selected.identity.id)
    if not records then
        table.insert(choices, {text='Could not load history: ' .. tostring(error_message),
            pen=COLOR_YELLOW})
        self.subviews.content:setChoices(choices)
        return
    end
    if #records == 0 then
        table.insert(choices, {text='No recorded history for this dwarf.', pen=COLOR_YELLOW})
        self.subviews.content:setChoices(choices)
        return
    end

    local story = translation.get_latest_story(selected.identity.id)
    add_header(choices, 'History story')
    if story then
        add_wrapped(choices, story.text)
        table.insert(choices, {text=('Confidence: %s'):format(story.confidence or '<unknown>')})
    else
        table.insert(choices, {text='No cached story yet.', pen=COLOR_YELLOW})
        table.insert(choices, {text='Run lorekeeper/story, then process the queue and refresh.'})
    end

    local events = history.build_events(records)
    add_header(choices, ('Timeline: %d records, %d events'):format(#records, #events))
    for index, event in ipairs(events) do
        add_event(choices, index, event)
    end
    self.subviews.content:setChoices(choices)
end

function LorekeeperHistoryWindow:copy_history()
    local lines = {}
    for _, choice in ipairs(self.subviews.content:getChoices()) do
        if type(choice.text) == 'string' then
            table.insert(lines, choice.text)
        end
    end
    dfhack.internal.setClipboardTextCp437Multiline(table.concat(lines, '\n'))
    dfhack.gui.showAnnouncement('Lorekeeper history copied to clipboard.', COLOR_LIGHTGREEN)
end

LorekeeperHistoryScreen = defclass(LorekeeperHistoryScreen, gui.ZScreenModal)
LorekeeperHistoryScreen.ATTRS {
    focus_path='lorekeeper/history/show',
}

function LorekeeperHistoryScreen:init()
    self:addviews{
        LorekeeperHistoryWindow{view_id='window'},
    }
end

if view then
    view:dismiss()
end

view = LorekeeperHistoryScreen{}:show()
