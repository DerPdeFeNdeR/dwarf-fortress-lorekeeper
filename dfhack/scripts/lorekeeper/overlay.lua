-- Open the memoire reader from the vanilla unit sheet.
--@ module = true
local gui = require('gui')
local widgets = require('gui.widgets')
local overlay = require('plugins.overlay')

function eligible(sheet, unit_sheet_type)
    return sheet and sheet.open and sheet.active_sheet == unit_sheet_type and
        type(sheet.active_id) == 'number' and sheet.active_id >= 0 and
        not sheet.unit_overview_customizing
end

local function active()
    return dfhack.isMapLoaded() and eligible(
        df.global.game.main_interface.view_sheets, df.view_sheet_type.UNIT)
end

MemoireButton = defclass(MemoireButton, overlay.OverlayWidget)
MemoireButton.ATTRS{
    desc='Open the Lorekeeper memoire reader for the viewed unit.',
    default_enabled=true,
    default_pos={x=2,y=6},
    viewscreens='dwarfmode/ViewSheets/UNIT',
    active=active,
    frame={w=27,h=3},
    frame_style=gui.FRAME_MEDIUM,
    frame_title='Lorekeeper',
}

function MemoireButton:init()
    self:addviews{
        widgets.HotkeyLabel{view_id='read',frame={t=0,l=0},
            key='CUSTOM_CTRL_L',label='Read Memoire',
            on_activate=self:callback('open_reader')},
    }
end

function MemoireButton:open_reader()
    -- Recheck at activation: never retain a unit pointer across selections.
    if not active() then return end
    local sheet = df.global.game.main_interface.view_sheets
    local unit = dfhack.gui.getSelectedUnit(true)
    if unit and unit.id == sheet.active_id then
        dfhack.run_script('lorekeeper/read')
    end
end

ChroniclesButton=defclass(ChroniclesButton,overlay.OverlayWidget)
ChroniclesButton.ATTRS{
    desc='Read the annual fortress chronicles.',default_enabled=true,
    default_pos={x=6,y=10},viewscreens='dwarfmode',
    active=function() return dfhack.isMapLoaded() end,
    frame={w=30,h=3},frame_style=gui.FRAME_MEDIUM,frame_title='Lorekeeper',
}
function ChroniclesButton:init()
    self:addviews{widgets.HotkeyLabel{frame={t=0,l=0},key='CUSTOM_CTRL_H',label='Fortress chronicles',
        on_activate=function() dfhack.run_script('lorekeeper/chronicles') end}}
end
OVERLAY_WIDGETS = {biography=MemoireButton,chronicles=ChroniclesButton}
if dfhack_flags.module then return end
print('Lorekeeper Memoire button: use the unit sheet, or run lorekeeper/memoire.')
