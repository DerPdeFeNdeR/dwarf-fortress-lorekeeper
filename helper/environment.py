"""Optional atmosphere from a bounded shared observation log, never invented history."""
import json
import re
from functools import lru_cache

from fortress_calendar import MONTH_TICKS, MONTHS, month_name

SEASONS = ('spring', 'summer', 'autumn', 'winter')
WEATHER = {'None': 'no precipitation observed', 'Rain': 'rain observed', 'Snow': 'snow observed'}
ATMOSPHERE_CONTEXT = """
Atmosphere is optional supporting context, never an event checklist. Usually use
no more than one brief atmospheric detail in a passage, often none. Do not repeat
seasonal openings mechanically. Calendar labels establish time, not temperature,
sunshine, foliage, wind, visibility, or an outdoor location. Geography describes
one representative surface world tile, not every room or every embark tile.
Weather rows sample the map's central weather cell at exact dates, not the entire
embark or continuous weather,
storm beginnings, or weather during another event. Do not attach a weather row
to an older event or even another event on that day without matching evidence.
No precipitation does not imply clear skies. Do not invent moon phases, moonlight,
rainbows, storms, snow cover, cold, floods, or weather effects from a season alone.
A Memoire cannot claim personal weather/sky experiences from fortress observations.
Only the dwarf's own thoughts/memories can support those experiences. Never invent
going outdoors, seeing the moon, or hearing rain underground. Annual narrators
may report dated fortress observations, but may not claim to have witnessed them.
Environmental details do not replace required event coverage or justify causality.
"""


def calendar(year, tick):
    month = month_name({'tick': tick})
    if type(year) is not int or year < 0 or not month:
        return None
    return dict(year=year, month=month, season=SEASONS[tick // (3 * MONTH_TICKS)],
                day=tick // 1200 % 28 + 1)


@lru_cache(maxsize=8)
def _read(path, size, modified):
    # Read only the committed prefix captured by Lua, even if the file has grown.
    with path.open('rb') as stream:
        raw = stream.read(size)
    if len(raw) != size or not raw.endswith(b'\n'):
        raise ValueError('Incomplete environment prefix')
    lines = raw.splitlines()
    if len(lines) > 4097 or any(len(line) > 4096 for line in lines):
        raise ValueError('Environment row limit exceeded')
    rows = [json.loads(line) for line in lines]
    if not rows or any(not isinstance(row, dict) for row in rows):
        raise ValueError('Invalid environment rows')
    return rows


def observations(save, reference, year, until):
    """Fail closed on optional data; malformed atmosphere never blocks a story."""
    if not isinstance(reference, dict):
        return {'status': 'unavailable'}
    site, branch = reference.get('site_id'), reference.get('branch')
    size, filename = reference.get('bytes'), reference.get('file')
    if (reference.get('version') != 1 or type(site) is not int or site < 0
            or not re.fullmatch(r'\d+-\d+', str(branch))
            or type(year) is not int or reference.get('year') != year
            or filename != f'{site}-{branch}-{year}.jsonl'
            or type(size) is not int or not 0 < size <= 2000000
            or type(until) is not int or not 0 <= until < 403200):
        return {'status': 'invalid_reference'}
    try:
        path = save / 'lorekeeper-environment' / filename
        # A reference must not escape the shared save directory via a symlink.
        if path.resolve().parent != (save / 'lorekeeper-environment').resolve():
            raise ValueError('Environment path escaped save directory')
        rows = _read(path, size, path.stat().st_mtime_ns)
        header = rows[0]
        if (header.get('schema_version') != 1 or header.get('kind') != 'geography'
                or header.get('site_id') != site or header.get('branch') != branch
                or header.get('year') != year):
            raise ValueError('Environment provenance mismatch')
        geography = header.get('geography')
        if not isinstance(geography, dict):
            raise ValueError('Invalid geography')
        selected = {}
        previous = -1
        for row in rows[1:]:
            tick = row.get('tick')
            if (row.get('kind') != 'weather' or row.get('year') != year
                    or type(tick) is not int or not previous < tick < 403200):
                raise ValueError('Invalid observation chronology')
            previous = tick
            if tick > until or row.get('weather') not in WEATHER:
                continue
            month = tick // MONTH_TICKS
            # At most one observation per month; prefer precipitation over none.
            if month not in selected or (selected[month]['weather'] == WEATHER['None']
                                          and row['weather'] != 'None'):
                selected[month] = dict(time=calendar(year, tick), tick=tick,
                                       weather=WEATHER[row['weather']])
        return dict(status='available', geography=geography,
                    weather=list(selected.values()), weather_scope='central_map_weather_cell',
                    moon_phase='unavailable_unverified')
    except (OSError, ValueError, TypeError, RecursionError):
        return {'status': 'unavailable_or_invalid'}


def annual(save, request):
    year = request['year']
    until = request['captured_tick'] if year == request['captured_year'] else 403199
    reference = request.get('environment')
    if reference and (not isinstance(reference,dict) or reference.get('site_id') != request['site_id']
                      or reference.get('branch') != request['branch']):
        return {'status': 'provenance_mismatch'}
    return observations(save, reference, year, until)


def personal(save, request, chapter):
    # Shared weather NEVER crosses the personal-knowledge boundary. Old monthly
    # chapters receive only their calendar, not today's geography or precipitation.
    if chapter != 'intro':
        year, month = map(int, chapter.split('-'))
        return dict(calendar=dict(year=year, month=MONTHS[month], season=SEASONS[month // 3]))
    context = observations(save, request.get('environment'), request['year'], request['tick'])
    return dict(status=context['status'], current_setting=context.get('geography'),
                scope='current fortress setting only; not the location of undated memories')
