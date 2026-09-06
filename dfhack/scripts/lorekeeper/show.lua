-- Read-only first summary window for The Lorekeeper.
--
-- Run with a unit selected: lorekeeper/show

local gui = require('gui')
local widgets = require('gui.widgets')
local snapshot = reqscript('lorekeeper/snapshot')
local glossary = reqscript('lorekeeper/glossary')
local translation = reqscript('lorekeeper/translation')

local function add_header(choices, text)
    table.insert(choices, {text=text, pen=COLOR_LIGHTCYAN})
end

local function add_unit_summary(choices, snapshot_data)
    add_header(choices, 'Identity')
    table.insert(choices, {text=('Name: %s'):format(snapshot_data.identity.name)})
    table.insert(choices, {text=('Profession: %s'):format(snapshot_data.identity.profession)})
    table.insert(choices, {text=('Unit ID: %d'):format(snapshot_data.identity.id)})

    local model_summary = translation.get_latest_summary(snapshot_data.identity.id)
    add_header(choices, 'Model interpretation')
    if model_summary then
        table.insert(choices, {text=('Summary: %s'):format(model_summary.text)})
        table.insert(choices, {text=('Category: %s / confidence %s'):format(
            model_summary.category or '<unknown>',
            model_summary.confidence or '<unknown>')})
        table.insert(choices, {text=('Explanation: %s'):format(model_summary.explanation)})
    else
        table.insert(choices, {text='No cached model explanation.'})
        table.insert(choices, {text='Run lorekeeper/translate, process the queue, then refresh.'})
    end

    if not snapshot_data.soul_present then
        table.insert(choices, {text='No current soul data is available.', pen=COLOR_YELLOW})
        return
    end

    add_header(choices, 'Thoughts')
    if #snapshot_data.thoughts == 0 then
        table.insert(choices, {text='No recorded thoughts.'})
    else
        for _, thought in ipairs(snapshot_data.thoughts) do
            local thought_description = glossary.describe_thought(thought.thought_name)
            local emotion_description = glossary.describe_emotion(thought.emotion_name)
            table.insert(choices, {text=('- %s / %s / severity %d'):format(
                thought_description.text,
                emotion_description.text,
                thought.severity)})
        end
    end

    add_header(choices, 'Mental state')
    table.insert(choices, {text=('Stress: %d'):format(snapshot_data.mental_state.stress)})

    add_header(choices, 'Personality facets')
    for _, facet in ipairs(snapshot_data.personality_facets) do
        local facet_description = glossary.describe_facet(facet.facet_name)
        table.insert(choices, {text=('%s: %d'):format(facet_description.text, facet.value)})
    end
end

LorekeeperWindow = defclass(LorekeeperWindow, widgets.Window)
LorekeeperWindow.ATTRS {
    frame_title='The Lorekeeper',
    frame={w=62, h=30},
    resizable=true,
    resize_min={w=42, h=12},
}

function LorekeeperWindow:init()
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
            on_activate=self:callback('copy_summary'),
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

function LorekeeperWindow:refresh()
    local choices = {}
    local snapshot_data = snapshot.capture_selected_unit()

    if not snapshot_data then
        table.insert(choices, {text='No unit is currently selected.', pen=COLOR_YELLOW})
    else
        add_unit_summary(choices, snapshot_data)
    end

    self.subviews.content:setChoices(choices)
end

function LorekeeperWindow:copy_summary()
    local lines = {}
    for _, choice in ipairs(self.subviews.content:getChoices()) do
        if type(choice.text) == 'string' then
            table.insert(lines, choice.text)
        end
    end

    dfhack.internal.setClipboardTextCp437Multiline(table.concat(lines, '\n'))
    dfhack.gui.showAnnouncement('Lorekeeper summary copied to clipboard.', COLOR_LIGHTGREEN)
end

LorekeeperScreen = defclass(LorekeeperScreen, gui.ZScreenModal)
LorekeeperScreen.ATTRS {
    focus_path='lorekeeper/show',
}

function LorekeeperScreen:init()
    self:addviews{
        LorekeeperWindow{view_id='window'},
    }
end

if view then
    view:dismiss()
end

view = LorekeeperScreen{}:show()
