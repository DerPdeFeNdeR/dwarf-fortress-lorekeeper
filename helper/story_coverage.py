"""Deterministic factual anchors for consequential selected historical events."""
import re
import unicodedata
from fortress_calendar import annual_prefix
from event_methods import details as method_details


class CoverageError(ValueError):
    def __init__(self, missing, label='Memoire'):
        self.missing_event_ids = missing
        super().__init__(label + ' coverage check could not verify: ' + ', '.join(map(str, missing)))


def participant(event, role, narrator_id=None, pronoun='I'):
    for row in event.get('participants', []):
        if row.get('role') == role and row.get('reference_status') == 'resolved' and row.get('name'):
            return pronoun if narrator_id is not None and row.get('histfig_id') == narrator_id else row['name']
    return None


def statement(event, narrator_id=None, annual=False, include_method=True):
    """No age, criminal intent, emotion, or causal interpretation is inferred."""
    kind = event['kind']
    def person(role, pronoun='I'):
        return participant(event, role, narrator_id, pronoun)
    victim, slayer = person('victim'), person('slayer')
    if kind == 'death' and victim:
        fact = f"{slayer} killed {person('victim', 'me')}" if slayer else f'{victim} died'
    elif kind == 'artifact_creation' and person('creator') and event.get('artifact_name'):
        fact = f"{person('creator')} created {event['artifact_name']}"
    elif kind == 'wounding' and person('wounded'):
        victim, actor = person('wounded'), person('wounder')
        fact = f"{actor} wounded {person('wounded', 'me')}" if actor else f'{victim} was wounded'
    elif kind == 'abduction' and person('abducted'):
        victim, actor = person('abducted'), person('abductor')
        fact = f"{actor} abducted {person('abducted', 'me')}" if actor else f'{victim} was abducted'
    elif kind == 'enslavement' and person('enslaved'):
        fact = f"{person('enslaved')} was enslaved"
    elif kind == 'ransom' and person('ransomed'):
        fact = f"{person('ransomed')} was ransomed"
    elif kind == 'release' and person('rescued_hfs'):
        fact = f"{person('rescued_hfs')} was freed"
    else:
        return None
    year = (event.get('time') or {}).get('year')
    prefix = f'In year {year}, ' if isinstance(year, int) and year >= 0 else ''
    if annual:
        prefix = annual_prefix(event.get('time'))
    # Location can be a destination in captivity events: do not call it the scene.
    site = event.get('site_name') if kind in {'death', 'wounding', 'artifact_creation', 'abduction'} else None
    method = method_details(event) if include_method else []
    return prefix + fact + (f' at {site}' if site else '') + (
        '; ' + '; '.join(method) if method else '') + '.'


def requirements(episodes, narrator_id=None, annual=False):
    rows = []
    for event in episodes.get('events', [])[:8]:
        fact = statement(event, narrator_id, annual)
        if fact:
            row = dict(event_id=event['id'], kind=event['kind'], sentence=fact)
            if annual:
                core = statement(event, narrator_id, annual, include_method=False)
                core = core.removeprefix(annual_prefix(event.get('time'))).removesuffix('.')
                row['clauses'] = [[core]]
                victim = participant(event, 'victim', narrator_id)
                slayer = participant(event, 'slayer', narrator_id)
                if event['kind']=='death' and victim and slayer:
                    site = f" at {event['site_name']}" if event.get('site_name') else ''
                    row['clauses'][0].append(f'{victim} was killed by {slayer}{site}')
                    # Explicit victim-first frames bind the following pronoun
                    # locally; do not resolve arbitrary pronouns across prose.
                    for pronoun in ('him', 'her', 'them'):
                        row['clauses'][0].extend([
                            f'{victim} died{site} when {slayer} killed {pronoun}',
                            f'death came to {victim}{site} when {slayer} killed {pronoun}'])
                for detail in method_details(event):
                    flexible = detail.startswith(('the cause of death was ',
                                                  'the weapon was ', 'the launcher was '))
                    value = detail.split(' was ', 1)[-1] if flexible else detail
                    row['clauses'].append([detail, value] if value != detail else [detail])
            rows.append(row)
    return rows


def normalized(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', text)).strip()


def validate(text, required, label='Memoire'):
    prose = normalized(text)
    missing = [row['event_id'] for row in required if not covered(text, prose, row)]
    if missing:
        raise CoverageError(missing, label)
    return {'checked_event_ids': [row['event_id'] for row in required],
            'method': 'bounded_factual_clauses' if any(r.get('clauses') for r in required)
                      else 'required_factual_sentences', 'status': 'passed'}


def covered(text, prose, row):
    clauses = row.get('clauses')
    if not clauses:
        sentence = normalized(row['sentence'])
        alternatives = [sentence]
        if row.get('kind') == 'heard_story' and sentence.startswith('I heard '):
            alternatives.append('I have heard ' + sentence[len('I heard '):])
        return any(alternative in prose for alternative in alternatives)
    # Keep roles/actions ordered and nearby in ONE paragraph. Independent name
    # mentions elsewhere are not coverage of who did what to whom.
    parts = []
    for index, choices in enumerate(clauses):
        alternatives = []
        for choice in choices:
            value = re.escape(normalized(choice))
            teller = row.get('teller') if row.get('kind') == 'storytelling' else None
            if index == 0 and teller and choice.startswith(teller + ' '):
                # A parenthetical transition does not change the storyteller.
                prefix = re.escape(normalized(teller))
                value = prefix + r'(?:,\s*(?:too|in turn|meanwhile),)?' + value[len(prefix):]
            alternatives.append(value)
        parts.append('(?:' + '|'.join(alternatives) + ')')
    pattern = parts[0]
    for index, part in enumerate(parts[1:]):
        pattern += f'(?P<gap{index}>[^.!?]{{0,240}}?)' + part
    for paragraph in re.split(r'\n\s*\n', text):
        for match in re.finditer(r'(?<!\w)' + pattern + r'(?!\w)', normalized(paragraph)):
            if not any(re.search(r"\b(not|never|denied|refused|didn't)\b", gap, re.I)
                       for gap in match.groupdict().values()):
                return True
    return False
