"""Deterministic factual anchors for consequential selected historical events."""
import re
import unicodedata


class CoverageError(ValueError):
    pass


def participant(event, role):
    for row in event.get('participants', []):
        if row.get('role') == role and row.get('reference_status') == 'resolved' and row.get('name'):
            return row['name']
    return None


def statement(event):
    """No age, criminal intent, emotion, or causal interpretation is inferred."""
    kind = event['kind']
    victim, slayer = participant(event, 'victim'), participant(event, 'slayer')
    if kind == 'death' and victim:
        fact = f'{slayer} killed {victim}' if slayer else f'{victim} died'
    elif kind == 'artifact_creation' and participant(event, 'creator') and event.get('artifact_name'):
        fact = f"{participant(event, 'creator')} created {event['artifact_name']}"
    elif kind == 'wounding' and participant(event, 'wounded'):
        victim, actor = participant(event, 'wounded'), participant(event, 'wounder')
        fact = f'{actor} wounded {victim}' if actor else f'{victim} was wounded'
    elif kind == 'abduction' and participant(event, 'abducted'):
        victim, actor = participant(event, 'abducted'), participant(event, 'abductor')
        fact = f'{actor} abducted {victim}' if actor else f'{victim} was abducted'
    elif kind == 'enslavement' and participant(event, 'enslaved'):
        fact = f"{participant(event, 'enslaved')} was enslaved"
    elif kind == 'ransom' and participant(event, 'ransomed'):
        fact = f"{participant(event, 'ransomed')} was ransomed"
    elif kind == 'release' and participant(event, 'rescued_hfs'):
        fact = f"{participant(event, 'rescued_hfs')} was freed"
    else:
        return None
    year = (event.get('time') or {}).get('year')
    prefix = f'In year {year}, ' if isinstance(year, int) and year >= 0 else ''
    # Location can be a destination in captivity events: do not call it the scene.
    site = event.get('site_name') if kind in {'death', 'wounding', 'artifact_creation', 'abduction'} else None
    return prefix + fact + (f' at {site}' if site else '') + '.'


def requirements(episodes):
    rows = []
    for event in episodes.get('events', [])[:8]:
        fact = statement(event)
        if fact:
            rows.append(dict(event_id=event['id'], kind=event['kind'], sentence=fact))
    return rows


def normalized(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', text)).strip()


def validate(text, required):
    prose = normalized(text)
    missing = [row['event_id'] for row in required if normalized(row['sentence']) not in prose]
    if missing:
        raise CoverageError('Biography omitted required event coverage: ' + ', '.join(map(str, missing)))
    return {'checked_event_ids': [row['event_id'] for row in required],
            'method': 'required_factual_sentences', 'status': 'passed'}
