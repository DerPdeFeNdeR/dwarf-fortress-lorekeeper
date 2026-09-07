"""Immutable annual fortress chapters, separate from refreshable current-year drafts."""
import hashlib
import json
import re
import time

from codex_batch import run_batch, generation_settings
from historical_episodes import SUPPORTED
from historian import STORY_NOTICE
from process_queue import load_results, write_results
from story_coverage import CoverageError, requirements, validate as validate_coverage
from cultural_events import collect as collect_culture, requirements as cultural_requirements
from fortress_calendar import month_name
from narrative_voice import MENTAL_VOICE_CONTEXT
from environment import ATMOSPHERE_CONTEXT, annual as annual_environment, calendar
from chronicle_correction import correct, apply_edits

CHRONICLE_CONTEXT = """Write an annual fortress chronicle, not one dwarf's biography.
Mention the chapter year at most once, optionally in the opening; the heading
already establishes it. For specific local events use the supplied month label,
not repeated 'In year ...' or raw ticks. An unknown month stays unspecified.
Group nearby events from the same month under one natural month-setting phrase.
Once Hematite is established, continue that month's account without opening every
sentence or paragraph with 'In Hematite'. Reintroduce a month only when the time
changes or a return would otherwise be unclear. Vary transitions and sentence
rhythm, but do not invent causal links or an order finer than the supplied dates.
Older years inside a tale's historical subject are different and must remain
when supplied: the performance's month dates the telling, not its subject.
When narrator.status is selected, write in that dwarf's first-person voice.
Use the saved personality_facets and explicit values to shape diction, rhythm,
attention, humor, and emotional openness. Choose a few distinctive traits, not
a checklist, caricature, modern slang, or stock stone-and-ale catchphrases.
Express traits through the telling rather than announcing your personality scores
or listing your virtues. A reserved voice can be spare; an outgoing voice warmer.
Do not infer personality from profession. Missing traits stay unspecified.
This is a fictionalized retrospective voice, not actual speech or a found diary.
The UI identifies the narrator; do not invent a writing commission or appointment.
The narrator's identity and voice are fixed for the year. Current traits do not
prove historical traits, and voice must not erase unflattering factual events.
Use I/my for supported personal participation, and our fortress for the broader
account. Other citizens' events are reported history, not automatically witnessed
or experienced by the narrator. Never invent how news reached the narrator,
private thoughts of others, quotations, conversations, or attendance at tellings.
When narrator is absent or unavailable, use an unnamed external chronicler without
claiming a dwarf identity or first-person participation.
Be lively for joys and absurdities, restrained for grief and hardship. Personality
can color interpretation but never excuse harm or make suffering a punchline.
Use only the supplied site and year's events. Residents' other lives are not
fortress history. Preserve named participants and their exact roles. Do not invent
causes, dialogue, battles, victories, criminal intent, emotions, immigration,
population counts, or a peaceful year from missing evidence. A scuffle is not a
siege. A location shared by events does not establish a common cause or episode.
When location_role is destination, the site is where a person was moved, not
necessarily the location of their capture, enslavement, or ransom transaction.
Plausible interpretation may be marked 'perhaps', but not invented facts.
Integrate every required_event_coverage fact without quoting, negating or
contradicting it. Killed does not imply murder. Each row supplies ordered clauses;
include one alternative from each clause group, in order, within one sentence,
with no more than 240 characters between them. The sentence field is a factual
example, NOT mandatory wording or a sentence-opening template. Date the local
event using its supplied month context, which may cover several events. Preserve
the clauses' named roles and actions, but choose punctuation and connective prose
freely. Include all deaths, including those without a named slayer or known month.
Treat artifact naming as naming, not creation. Do not infer a strange mood
unless an explicit mood event supports it. Use chronology and contrasting
developments to organize the chapter, not a roster of events or citizens.
Aim for 4-8 paragraphs for a busy year, less for sparse evidence, at most 900
words. Avoid repeating factual anchors elsewhere. Leave technical coverage,
recording branches, and draft labels outside the narrative; the UI supplies them.
Never mention supplied data, inputs, absent cultural tellings, selected events,
coverage, the writing process, or the amount of evidence in the prose. Empty lists
are not events. For sparse evidence tell a short account and stop, without an
explanation of why it is short. Put necessary source caveats in explanation only.
Do not write meta-commentary such as 'I will not invent motives', 'the record does
not provide', or explanations of what you refuse to claim. State supported facts
and leave the unknown unsaid. Personality and values are properties of the
narrator, not facts about fortress conditions: disliking harmony does NOT mean
the fortress lacked harmony. Do not turn an artifact's name into its material,
appearance, or properties. Name spellings and nicknames must remain intact.
Drafts describe only the year so far; final chapters cover only the specified
completed year. Narration is fictionalized, not proof of eyewitness knowledge.
Cultural events are local storytelling performances. Name resolved storytellers
and the historical subject; their topic's date is NOT the date of this telling.
The named organization did not visit merely because someone told a story about it.
At FIRST mention of each unfamiliar organization or subject, briefly explain its
supplied entity_details (race and organization type) in an adjacent appositive or
immediately following sentence. For example, a named organization may be followed
by ', a human government,' when supported. Never postpone several classifications
to a glossary-like list at the paragraph or chapter end. Explain each entity once;
later mentions can be shorter without losing identity. Recognize
classification_observed_now as current context, not proof of its historical form.
Never invent an unknown storyteller, audience, quotation, allegiance, or visit.
Before returning, verify EVERY required_event_coverage row, including every
incident: cultural fact. Do not omit a telling because several concern appointments.
Keep each teller tied to the correct subject; topic years date that subject, not
the local performance. Insert entity explanations beside the first subject mention,
between clause groups if needed. Reduce optional commentary before dropping a fact.
""" + MENTAL_VOICE_CONTEXT + ATMOSPHERE_CONTEXT


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
    if data.get('schema_version') not in (1,2) or not re.fullmatch(r'\d+-\d+',str(data.get('branch',''))):
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
    if data['schema_version']==2:
        voice=data.get('narrator')
        if (not isinstance(voice,dict) or voice.get('version')!=1
                or voice.get('year')!=data['year'] or voice.get('site_id')!=data['site_id']
                or voice.get('status') not in ('selected','unavailable')):
            raise ValueError('Invalid annual narrator')
        if voice['status']=='selected' and (type(voice.get('histfig_id')) is not int
                or voice['histfig_id']<0 or not isinstance(voice.get('name'),str)
                or not voice['name'] or len(voice['name'])>512
                or not isinstance(voice.get('personality_facets'),dict)
                or not isinstance(voice.get('values'),list) or len(voice['values'])>32):
            raise ValueError('Invalid annual narrator identity or voice')
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
        event['month']=month_name(event['time'])
        event['calendar']=calendar(request['year'],tick)
        if event['kind']=='artifact_creation':
            if not isinstance(event.get('naming_only'),bool): continue
            if event['naming_only']: event['kind']='artifact_naming'
        seen.add(event['id']); events.append(event)
    events.sort(key=lambda e:(e.get('tick',-1),e['id']))
    anchors=[]
    for event in events:
        anchors.extend(requirements({'events':[event]}, (request.get('narrator') or {}).get('histfig_id'), annual=True))
    culture=collect_culture(request)
    for event in culture:
        event['month']=month_name(event['time'])
        event['calendar']=calendar(request['year'],event['time'].get('tick'))
    anchors.extend(cultural_requirements(culture))
    return dict(site_name=request['site_name'],site_id=request['site_id'],cultural_events=culture,
                narrator=request.get('narrator'),
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


def recheck_rejected(save, key, repair=False, edits=None):
    """Explicit operator recovery: revalidate the same failed candidate, no model call."""
    if not re.fullmatch(r'\d+-\d+-\d+-\d+-(draft|final)', key):
        raise ValueError('Invalid chapter key')
    directory=save/'lorekeeper-chronicles'
    output=directory/(key+'.chapter.json')
    state=load_results(output)
    rejected=load_results(directory/(key+'.rejected.json'))
    filename=state.get('request_file','')
    if not re.fullmatch(r'[\w-]+\.request\.json',filename):
        raise ValueError('Invalid original request filename')
    request_path=directory/filename
    request=load_request(request_path)
    digest=hashlib.sha256(request_path.read_bytes()).hexdigest()
    if (state.get('state')!='failed' or chapter_key(request)!=key
            or rejected.get('request_digest')!=digest or state.get('request_digest')!=digest
            or rejected.get('request_file')!=filename):
        raise ValueError('Rejected candidate does not match the current failed request')
    text=(rejected.get('corrected_text') if rejected.get('correction_status')=='passed'
          else rejected.get('text'))
    if not isinstance(text,str) or len(text.encode('utf-8'))>16000:
        raise ValueError('Invalid rejected candidate')
    payload=chapter_input(request)
    if edits is not None:
        if repair:
            raise ValueError('Choose saved edits or a model correction, not both')
        text,coverage=apply_edits(rejected['text'],edits,rejected['missing_event_ids'],
                                  payload['required_event_coverage'])
        rejected.update(corrected_text=text,correction_status='passed',
                        operator_correction_response=edits)
        write_results(directory/(key+'.rejected.json'),rejected)
    elif repair:
        if rejected.get('required_event_coverage')!=payload['required_event_coverage']:
            raise ValueError('Saved correction requirements no longer match the request')
        text,coverage=repair_diagnostic(directory,key,rejected)
    else:
        coverage=validate_coverage(text,payload['required_event_coverage'],label='Chronicle')
    current=load_results(output)
    if current.get('request_digest')!=digest or current.get('state')!='failed':
        raise ValueError('Chapter changed during recovery; corrected candidate retained only')
    state.update(state='ready',story=text,story_coverage=coverage,
                 generation=rejected.get('generation'),story_narrator=request.get('narrator'),
                 event_ids=[e['id'] for e in payload['events']],
                 cultural_event_ids=[e['source_key'] for e in payload['cultural_events']],
                 recovered_from_diagnostic=True,updated_at=time.time())
    state.pop('error',None)
    write_results(output,state)
    publish_catalog(directory)
    return coverage


def repair_diagnostic(directory,key,rejected):
    if rejected.get('correction_attempted'):
        raise ValueError('The single correction attempt was already used')
    rejected['correction_attempted']=True
    path=directory/(key+'.rejected.json')
    # Persist BEFORE calling the model so restart/failure cannot create a loop.
    write_results(path,rejected)
    def retain(response):
        if isinstance(response,str) and len(response.encode())<=16000:
            rejected['correction_response']=response
            write_results(path,rejected)
    try:
        text,coverage=correct(rejected['text'],rejected['missing_event_ids'],
            rejected['required_event_coverage'],run_batch,rejected['generation'],key,retain=retain)
        rejected.update(corrected_text=text,correction_status='passed')
        write_results(path,rejected)
        return text,coverage
    except Exception as error:
        rejected.update(correction_status='failed',correction_error=str(error)[-500:])
        write_results(path,rejected)
        raise


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
    # One chapter per cycle: initial generation plus at most one targeted correction.
    for key,(path,request) in reversed(list(latest.items())):
        output=directory/(key+'.chapter.json')
        previous=load_results(output)
        if request['kind']=='final' and previous.get('state')=='ready': continue
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if previous.get('request_digest')==digest and previous.get('state') in ('ready','failed'): continue
        if previous.get('request_digest')==digest and previous.get('state')=='processing':
            diagnostic=load_results(directory/(key+'.rejected.json'))
            if diagnostic.get('request_digest')==digest and diagnostic.get('correction_attempted'):
                previous.update(state='failed',updated_at=time.time(),
                    error='Chronicle correction was interrupted; saved draft preserved.',
                    correction_status='interrupted')
                write_results(output,previous); publish_catalog(directory)
                break  # Never regenerate/reset the attempt budget after a crash.
        payload=chapter_input(request)
        payload['environment']=annual_environment(save,request)
        state=dict(key=key,year=request['year'],kind=request['kind'],branch=request['branch'],
                   site_id=request['site_id'],site_name=request['site_name'],state='processing',
                   request_digest=digest,updated_at=time.time(),coverage=request.get('coverage',{}),
                   story=previous.get('story'),notice=STORY_NOTICE,source=request.get('source',{}),
                   request_file=path.name,narrator=request.get('narrator'),
                   story_narrator=previous.get('story_narrator'))
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
                try:
                    coverage=validate_coverage(text,payload['required_event_coverage'],label='Chronicle')
                except CoverageError as error:
                    rejected_file=key+'.rejected.json'
                    try:
                        rejected=dict(
                            status='rejected_not_for_display',text=text,
                            missing_event_ids=error.missing_event_ids,
                            required_event_coverage=payload['required_event_coverage'],
                            request_file=path.name,request_digest=digest,
                            prompt_digest=hashlib.sha256(CHRONICLE_CONTEXT.encode()).hexdigest(),
                            generation=settings,created_at=time.time())
                        write_results(directory/rejected_file,rejected)
                        state['rejected_draft_file']=rejected_file
                    except OSError:
                        state['diagnostic_warning']='Could not save rejected draft diagnostics.'
                        raise error
                    try:
                        text,coverage=repair_diagnostic(directory,key,rejected)
                        state['correction_status']='passed'
                    except Exception as correction_error:
                        state['correction_status']='failed'
                        state['correction_error']=str(correction_error)[-500:]
                        raise error
                state.update(story=text,generation=settings,story_coverage=coverage,
                             story_narrator=request.get('narrator'))
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
