"""Local tellings, never a promotion of their subjects into local history."""
from heard_stories import office_subject, storyteller_names
from fortress_calendar import annual_prefix

SMALL_YEARS = ('zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven',
               'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen',
               'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty')


def office_clauses(topic, fallback):
    if not office_subject(topic):
        return [[fallback]]
    person = next(p['name'] for p in topic['participants']
                  if p.get('role')=='subject' and p.get('reference_status')=='resolved' and p.get('name'))
    office, entity = topic['office']['name'], topic['entity_name']
    return [[person], [f'{verb} {office} {preposition} {entity}'
        for verb,preposition in (('taking the office of','in'),('took the office of','in'),
                                ('becoming','of'),('became','of'),('became','in'),
                                ('becoming','in'))]]


def collect(request):
    result, seen = [], set()
    for source in request.get('cultural_events', [])[:4]:
        identity = source.get('id')
        performance = source.get('performance') or {}
        topic = performance.get('topic') or {}
        if (type(identity) is not int or identity < 0 or identity in seen
                or source.get('source_kind') != 'incident' or source.get('kind') != 'storytelling'
                or source.get('site_id') != request['site_id'] or source.get('year') != request['year']
                or type(source.get('tick')) is not int or not 0 <= source['tick'] < 403200
                or performance.get('performance_type') != 'STORYTELLING_EVENT'
                or performance.get('site_id') != source['site_id']
                or performance.get('year') != source['year'] or performance.get('tick') != source['tick']
                or source.get('reference_status') != 'resolved'):
            continue
        if request['kind'] == 'draft' and source['tick'] > request['captured_tick']:
            continue
        topic_year, topic_tick = topic.get('year', -1), topic.get('tick', -1)
        if type(topic_year) is int and (topic_year, max(0, topic_tick or 0)) > (source['year'], source['tick']):
            continue
        seen.add(identity)
        result.append(dict(source_key=f'incident:{identity}', performance_id=identity,
            time=dict(year=source['year'],tick=source['tick']),site_id=source['site_id'],
            performers=performance.get('performers',[])[:4],topic=topic,
            subject_status=performance.get('subject_status')))
    return sorted(result,key=lambda row:(row['time']['tick'],row['performance_id']))


def requirements(events):
    required = []
    for event in events:
        topic = event['topic']
        subject = office_subject(topic) or topic.get('entity_name') or topic.get('artifact_name')
        if not subject or topic.get('status') != 'resolved':
            continue
        names = storyteller_names(event)
        teller = ' and '.join(names) if names else 'an unidentified storyteller'
        sentence = f"{annual_prefix(event['time'])}{teller} told a story about {subject}."
        # Leave space after the organization name for its first-mention context.
        year = topic.get('year', -1)
        dated = office_subject(topic) and type(year) is int and year >= 0
        topic_clause = subject.removesuffix(f' in year {year}') if dated else subject
        clauses = [[f'{teller} {verb}' for verb in ('told a story about',
                    'recounted a tale about', 'told a tale of', 'recounted the story of',
                    'told the story of', 'recounted a story about', 'related a tale of',
                    'told a story of', 'later told a story about',
                    'followed with a tale of', 'followed with a story about',
                    'shared a tale of', 'shared a story about',
                    'recounted how', 'told of')]] + office_clauses(topic, topic_clause)
        if dated:
            years = [str(year)] + ([SMALL_YEARS[year]] if year < len(SMALL_YEARS) else [])
            clauses.append([f'{prefix} {value}' for value in years for prefix in ('year','in','of')])
        required.append(dict(event_id=event['source_key'],kind='storytelling',
                             sentence=sentence,clauses=clauses,teller=teller))
    return required
