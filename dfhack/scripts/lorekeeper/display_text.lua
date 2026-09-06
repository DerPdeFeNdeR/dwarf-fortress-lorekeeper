-- Convert UTF-8 prose into individual DF display lines.
--@module = true

function wrap(text, width)
    width = width or 68
    local lines = {}
    -- Use display-safe punctuation without transliterating names or cache text.
    text = text:gsub('—', ' -- '):gsub('–', '-')
        :gsub('“', '"'):gsub('”', '"'):gsub('‘', "'"):gsub('’', "'")
        :gsub('…', '...')
    text = text:gsub('\r\n', '\n'):gsub('\r', '\n')
    -- Split before conversion: DF display encoding does not preserve newlines.
    for paragraph in (text .. '\n'):gmatch('(.-)\n') do
        local line = ''
        for word in dfhack.utf2df(paragraph:gsub('\t', ' ')):gmatch('%S+') do
            if line ~= '' and #line + 1 + #word > width then
                table.insert(lines, line)
                line = ''
            end
            line = line == '' and word or line .. ' ' .. word
        end
        table.insert(lines, line)
    end
    return lines
end
