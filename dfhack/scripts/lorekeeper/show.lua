-- Read-only first summary window for The Lorekeeper.
--
-- Run with a unit selected: lorekeeper/show

local gui = require('gui')
local widgets = require('gui.widgets')

local function get_enum_name(enum, value)
    if type(value) == 'string' then
        return value
    end

    local direct_name = enum[value]
    if type(direct_name) == 'string' then
        return direct_name
    end

    for enum_value, enum_name in ipairs(enum) do
        if enum_value == value then
            return enum_name
        end
    end

    return ('<unknown:%s>'):format(tostring(value))
end

local function get_unit_name(unit)
    return dfhack.df2console(dfhack.units.getReadableName(unit, true))
end

local function add_header(choices, text)
    table.insert(choices, {text=text, pen=COLOR_LIGHTCYAN})
end

local function add_unit_summary(choices, unit)
    add_header(choices, 'Identity')
    table.insert(choices, {text=('Name: %s'):format(get_unit_name(unit))})
    table.insert(choices, {text=('Profession: %s'):format(dfhack.units.getProfessionName(unit))})
    table.insert(choices, {text=('Unit ID: %d'):format(unit.id)})

    local soul = unit.status and unit.status.current_soul
    if not soul then
        table.insert(choices, {text='No current soul data is available.', pen=COLOR_YELLOW})
        return
    end

    local personality = soul.personality
    add_header(choices, 'Thoughts')
    if #personality.emotions == 0 then
        table.insert(choices, {text='No recorded thoughts.'})
    else
        for _, thought in ipairs(personality.emotions) do
            table.insert(choices, {text=('- %s / %s / severity %d'):format(
                get_enum_name(df.unit_thought_type, thought.thought),
                get_enum_name(df.emotion_type, thought.type),
                thought.severity)})
        end
    end

    add_header(choices, 'Mental state')
    table.insert(choices, {text=('Stress: %d'):format(personality.stress)})

    local traits = {}
    for facet, value in pairs(personality.traits) do
        table.insert(traits, {
            name=get_enum_name(df.personality_facet_type, facet),
            value=value,
        })
    end
    table.sort(traits, function(a, b) return a.name < b.name end)

    add_header(choices, 'Personality facets')
    for _, trait in ipairs(traits) do
        table.insert(choices, {text=('%s: %d'):format(trait.name, trait.value)})
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
            on_activate=function() self:dismiss() end,
        },
    }

    self:refresh()
end

function LorekeeperWindow:refresh()
    local choices = {}
    local unit = dfhack.gui.getSelectedUnit(true)

    if not unit then
        table.insert(choices, {text='No unit is currently selected.', pen=COLOR_YELLOW})
    else
        add_unit_summary(choices, unit)
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
