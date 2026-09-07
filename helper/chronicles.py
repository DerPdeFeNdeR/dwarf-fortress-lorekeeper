"""Immutable annual fortress chapters, separate from refreshable current-year drafts."""
import hashlib
import json
import re
import time

from codex_batch import run_batch, generation_settings
from historical_episodes import SUPPORTED
from historian import STORY_NOTICE
from process_queue import load_results, write_results
from story_coverage import requirements, validate as validate_coverage
from cultural_events import collect as collect_culture, requirements as cultural_requirements

CHRONICLE_CONTEXT = """Write an annual fortress chronicle, not one dwarf's biography.
Use one learned, observant fortress historian, proud of craftsmanship and dryly
witty about ordinary absurdities, restrained and compassionate about suffering.
Use only the supplied site and year's events. Residents' other lives are not
fortress history. Preserve named participants and their exact roles. Do not invent
causes, dialogue, battles, victories, criminal intent, emotions, immigration,
population counts, or a peaceful year from missing evidence. A scuffle is not a
siege. A location shared by events does not establish a common cause or episode.
When location_role is destination, the site is where a person was moved, not
necessarily the location of their capture, enslavement, or ransom transaction.
Plausible interpretation may be marked 'perhaps', but not invented facts.
Integrate every required_event_coverage sentence verbatim in normal prose,
without quoting, negating, or contradicting it. Killed does not imply murder.
Treat artifact naming as naming, not creation. Do not infer a strange mood
unless an explicit mood event supports it. Use chronology and contrasting
developments to organize the chapter, not a roster of events or citizens.
Aim for 4-8 paragraphs for a busy year, less for sparse evidence, at most 900
words. Avoid repeating factual anchors elsewhere. Leave technical coverage,
recording branches, and draft labels outside the narrative; the UI supplies them.
Drafts describe only the year so far; final chapters cover only the specified
completed year. This narrator is fictional, not a claimed eyewitness.
Cultural events are local storytelling performances. Name resolved storytellers
and the historical subject; their topic's date is NOT the date of this telling.
The named organization did not visit merely because someone told a story about it.
Briefly explain supplied entity_details (race and organization type), recognizing
classification_observed_now as current context, not proof of its historical form.
Never invent an unknown storyteller, audience, quotation, allegiance, or visit.
Before returning, verify that EVERY required_event_coverage sentence appears
unchanged in text, including every incident: cultural anchor. Do not combine,
shorten, rephrase, or omit one of those sentences even when several tellings
concern appointments. Keep the anchors as separate sentences within a coherent
cultural paragraph. Reduce optional visitor lists or commentary before dropping
a required sentence. Entity explanations may follow, not alter, the anchors.
"""


def load_request(path):
    with path.open('rb') as stream:
        raw=stream.read(131073)
    if len(raw)>131072:
        raise ValueError('Chronicle input exceeds 128 KiB')
    data=json.loads(raw.decode('utf-8'))
    if not isinstance(data,dict):
        raise ValueError('Chronicle request must be an object')
    for field in ('site_id','year','captured_year','captured_tick'):
        if type(data.get(field)) is not int or data[field]<0:
            raise ValueError('Invalid chronicle '+field)
    if data.get('schema_version')!=1 or not re.fullmatch(r'\d+-\d+',str(data.get('branch',''))):
        raise ValueError('Invalid chronicle schema or branch')
    if data.get('kind') not in ('draft','final'):
        raise ValueError('Invalid chapter kind')
    if data['kind']=='final' and data['year']>=data['captured_year']:
        raise ValueError('Cannot finalize an unfinished year')
    if data['kind']=='draft' and data['year']!=data['captured_year']:
        raise ValueError('Draft must describe the current year')
    if not isinstance(data.get('events'),list) or len(data['events'])>16:
        raise ValueError('Invalid chronicle event count')
    culture=data.get('cultural_events',[])
    if not isinstance(culture,list) or len(culture)>4 or any(not isinstance(e,dict) for e in culture):
        raise ValueError('Invalid chronicle cultural event count')
    for event in data['events']:
        if not isinstance(event,dict) or any(type(event.get(k)) is not int for k in ('id','year','tick')):
            raise ValueError('Invalid chronicle event')
    if not isinstance(data.get('site_name'),str) or len(data['site_name'])>512:
        raise ValueError('Invalid fortress name')
    return data


def chapter_key(request):
    return f"{request['site_id']}-{request['branch']}-{request['year']}-{request['kind']}"


def chapter_input(request):
    events=[]; seen=set()
    for source in request['events']:
        if (source.get('kind') not in SUPPORTED or source.get('site_id')!=request['site_id']
                or source.get('year')!=request['year'] or source.get('id') in seen):
            continue
        tick=source.get('tick',-1)
        if request['kind']=='draft' and tick>request['captured_tick']:
            continue
        if type(source.get('id')) is not int or source['id']<0:
            continue
        event=dict(source,time={'year':source['year']})
        if tick>=0: event['time']['tick']=tick
        if event['kind']=='artifact_creation':
            if not isinstance(event.get('naming_only'),bool): continue
            if event['naming_only']: event['kind']='artifact_naming'
        seen.add(event['id']); events.append(event)
    events.sort(key=lambda e:(e.get('tick',-1),e['id']))
    anchors=[]
    for event in events:
        anchors.extend(requirements({'events':[event]}))
    culture=collect_culture(request)
    anchors.extend(cultural_requirements(culture))
    return dict(site_name=request['site_name'],site_id=request['site_id'],cultural_events=culture,
                year=request['year'],kind=request['kind'],events=events,
                required_event_coverage=anchors)


def publish_catalog(directory):
    rows=[]
    for path in directory.glob('*.chapter.json'):
        state=load_results(path)
        rows.append({key:state.get(key) for key in
                     ('key','year','kind','branch','site_id','site_name','state','updated_at')})
    rows.sort(key=lambda row:(row['year'],row['updated_at']),reverse=True)
    write_results(directory/'index.json',dict(chapters=rows[:100],older_archived=len(rows)>100))


def process_chronicles(save):
    directory=save/'lorekeeper-chronicles'
    if not directory.exists(): return
    latest={}
    for path in sorted(directory.glob('*.request.json'),key=lambda p:p.stat().st_mtime_ns):
        try:
            request=load_request(path)
        except (OSError,ValueError,TypeError) as error:
            print(f'Lorekeeper: invalid chronicle request {path.name}: {error}',flush=True)
            continue
        latest[chapter_key(request)]=(path,request)
    # At most one model job per watcher cycle; completed chapters are never rewritten.
    for key,(path,request) in reversed(list(latest.items())):
        output=directory/(key+'.chapter.json')
        previous=load_results(output)
        if request['kind']=='final' and previous.get('state')=='ready': continue
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if previous.get('request_digest')==digest and previous.get('state') in ('ready','failed'): continue
        payload=chapter_input(request)
        state=dict(key=key,year=request['year'],kind=request['kind'],branch=request['branch'],
                   site_id=request['site_id'],site_name=request['site_name'],state='processing',
                   request_digest=digest,updated_at=time.time(),coverage=request.get('coverage',{}),
                   story=previous.get('story'),notice=STORY_NOTICE,source=request.get('source',{}),
                   request_file=path.name)
        write_results(output,state); publish_catalog(directory)
        started=time.perf_counter()
        try:
            if payload['events'] or payload['cultural_events']:
                settings=generation_settings()
                item=dict(id=key,kind='fortress_year',raw=json.dumps(payload,ensure_ascii=False),
                          context=CHRONICLE_CONTEXT)
                result=run_batch([item],settings=settings)['results'][0]
                text=result['text']
                if len(text.encode('utf-8'))>16000: raise ValueError('Annual chapter exceeds display limit')
                coverage=validate_coverage(text,payload['required_event_coverage'])
                state.update(story=text,generation=settings,story_coverage=coverage)
            else:
                state.update(story='',empty=True)
            state['state']='ready'
            state['event_ids']=[event['id'] for event in payload['events']]
            state['cultural_event_ids']=[event['source_key'] for event in payload['cultural_events']]
        except Exception as error:
            state.update(state='failed',error=str(error)[-500:])
        state.update(updated_at=time.time(),generation_seconds=time.perf_counter()-started)
        write_results(output,state); publish_catalog(directory)
        break
