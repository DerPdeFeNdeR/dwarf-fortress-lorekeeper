"""DF fortress calendar labels; unknown dates never acquire a guessed month."""
MONTH_TICKS = 33600
MONTHS = ('Granite', 'Slate', 'Felsite', 'Hematite', 'Malachite', 'Galena',
          'Limestone', 'Sandstone', 'Timber', 'Moonstone', 'Opal', 'Obsidian')


def month_name(when):
    tick = (when or {}).get('tick', (when or {}).get('year_tick'))
    return MONTHS[tick // MONTH_TICKS] if type(tick) is int and 0 <= tick < 12 * MONTH_TICKS else None


def annual_prefix(when):
    month = month_name(when)
    return f'In {month}, ' if month else ''
