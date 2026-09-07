"""One bounded edit pass; never regenerate a chapter or relax factual coverage."""
import json
import re
from story_coverage import validate

CONTEXT = """Correct only the flagged factual coverage in an annual chronicle.
Return a JSON array serialized in the result text, with objects containing exactly
event_id, sentence_id, new. sentence_id is the integer index of one supplied
sentence; new replaces only that sentence. Do not copy the original sentence
into your response. Do not return a rewritten chapter or Markdown fences.
Use one edit per missing event, at most four. Preserve voice, existing facts,
dates, classifications, names, and wording except the minimal required correction.
Retain every original word in its original order; insert missing information only.
Use the full required name even if the draft shortened it. Restore missing topic
years: these date the story's subject, NOT the local telling. Preserve the supplied
month of the telling; do not move events to another month. Include one alternative
from every required clause group in order within the replacement sentence.
Do not invent facts or add commentary. Do not edit unrelated sentences. If an event
cannot be fixed with one sentence replacement, return an empty array.
"""


def apply_edits(text, encoded, missing, required):
    if not isinstance(encoded,str) or len(encoded.encode())>16000:
        raise ValueError('Correction exceeds limit')
    edits=json.loads(encoded)
    if not isinstance(edits,list) or not 1<=len(edits)<=4:
        raise ValueError('Correction requires one to four sentence edits')
    remaining=set(missing); spans=[]
    anchors={row['event_id']:row for row in required}
    for edit in edits:
        if isinstance(edit,dict) and set(edit)=={'event_id','sentence_id','new'}:
            sentences=sentence_list(text)
            index=edit['sentence_id']
            if type(index) is not int or not 0<=index<len(sentences):
                raise ValueError('Invalid correction sentence index')
            edit=dict(event_id=edit['event_id'],old=sentences[index],new=edit['new'])
        if not isinstance(edit,dict) or set(edit)!={'event_id','old','new'}:
            raise ValueError('Invalid correction fields')
        identity=edit['event_id']; old=edit['old']; new=edit['new']
        if not isinstance(identity,(str,int)) or identity not in remaining:
            raise ValueError('Correction targets an unrelated or duplicate event')
        for sentence in (old,new):
            if (not isinstance(sentence,str) or not 1<=len(sentence)<=1600
                    or '\n' in sentence or not re.fullmatch(r'[^.!?]+[.!?]',sentence)):
                raise ValueError('Correction must replace one bounded complete sentence')
        if text.count(old)!=1:
            raise ValueError('Correction source must occur exactly once')
        words=iter(re.findall(r'\w+',new))
        if not all(any(candidate==word for candidate in words) for word in re.findall(r'\w+',old)):
            raise ValueError('Correction removed or reordered original wording')
        start=text.index(old); end=start+len(old)
        if text[:start].rstrip() and text[:start].rstrip()[-1] not in '.!?':
            raise ValueError('Correction source starts inside a sentence')
        if any(start<b and end>a for a,b,_ in spans):
            raise ValueError('Overlapping correction edits')
        validate(new,[anchors[identity]],label='Chronicle correction')
        spans.append((start,end,new)); remaining.remove(identity)
    if remaining:
        raise ValueError('Correction did not address every flagged event')
    for start,end,new in sorted(spans,reverse=True):
        text=text[:start]+new+text[end:]
    if len(text.encode())>16000:
        raise ValueError('Corrected chapter exceeds display limit')
    return text,validate(text,required,label='Chronicle')


def sentence_list(text):
    return [match.group(0).strip() for match in re.finditer(r'[^.!?]+[.!?]',text)]


def correct(text, missing, required, generate, settings, identity, retain=None):
    if not 1<=len(missing)<=4:
        raise ValueError('Too many missing events for a bounded correction')
    item=dict(id=identity+':correction',kind='chronicle_correction',
        context=CONTEXT,raw=json.dumps(dict(sentences=[dict(sentence_id=i,text=s)
            for i,s in enumerate(sentence_list(text))],
            required=[row for row in required if row['event_id'] in missing]),ensure_ascii=False))
    result=generate([item],settings=settings)['results'][0]
    if retain:
        retain(result['text'])
    return apply_edits(text,result['text'],missing,required)
