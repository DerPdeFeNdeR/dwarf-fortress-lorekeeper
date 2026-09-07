"""Dispatch validated model-owned prompts and response assembly."""
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import anchored_chronicle
import luna_writing
from model_input import compact_raw
from writer_settings import STRATEGY_VERSIONS
from writing_brief import is_writing_task, build_brief, build_threaded_brief, prose_schema, adapt_prose


@dataclass(frozen=True)
class PreparedWriting:
    strategy: str
    version: str
    prompt: str
    schema: dict

    def provenance(self):
        return dict(strategy=self.strategy, strategy_version=self.version,
                    prompt_digest=hashlib.sha256(self.prompt.encode()).hexdigest(),
                    schema_digest=hashlib.sha256(json.dumps(self.schema, sort_keys=True).encode()).hexdigest())


def literary_prompt(items):
    return luna_writing.build_prompt(items)


def direct_prompt(items, writing=False, options=None):
    fields = 'id and text' if writing else 'id, text, explanation, category, and confidence (high, medium, or low)'
    sections = [f'Return a JSON object with a results array, one result per request in order. '
                f'Preserve every request id. Each result needs {fields}.',
                'Evidence tables with record_columns and record_rows represent lists of objects: '
                'each row has the corresponding column names, in order. For record_schemas, '
                'the first entry in each row is the zero-based schema index; remaining entries '
                'correspond to that schema\'s field names. They preserve every field.']
    for item in items:
        context, raw = build_brief(item,options) if writing else (item.get('context', ''), compact_raw(item['raw']))
        sections.extend([
            'Request identity: ' + json.dumps({k: v for k, v in item.items() if k not in ('context', 'raw')}, ensure_ascii=False),
            'Writing instructions:\n' + context, 'Supplied game evidence:\n' + raw])
    sections.append('Write only supported facts and clearly signaled interpretation. '
                    'A profession supplies no personality, length of service, routine, or past experiences. '
                    'For sparse evidence, a few sentences are enough; do not fill gaps with a fictional life. '
                    'Do not invent conversations, witnesses, events, or sources. '
                    + ('' if writing else 'Keep explanation to one short sentence. ') + 'Return only the requested JSON.')
    return '\n\n'.join(sections)


def task_type(item):
    if item['kind'] == 'fortress_year':
        return 'chronicle'
    if is_writing_task(item):
        return 'memoire'
    return 'legacy' if item['kind'] == 'dwarf_history' else 'translation'


def prepare(items, settings):
    kinds = {task_type(item) for item in items}
    if len(kinds) != 1:
        raise ValueError('Batch mixes incompatible writing task types')
    kind = kinds.pop()
    strategy = settings['strategies'].get(kind, 'translation')
    if kind in ('legacy', 'translation') and settings['model'] == 'gpt-5.6-luna':
        strategy = 'luna-literary'
    if strategy == 'luna-literary':
        prompt, schema = luna_writing.prepare(items)
        return PreparedWriting(strategy, STRATEGY_VERSIONS[strategy], prompt, schema)
    if strategy == 'anchored':
        if len(items) != 1:
            raise ValueError('Anchored chronicles require one chapter per request')
        if anchored_chronicle.supported(items[0]):
            context, evidence = anchored_chronicle.brief(items[0])
            return PreparedWriting(strategy, STRATEGY_VERSIONS[strategy], context + '\n\n' + evidence,
                                   anchored_chronicle.schema(items[0]))
        strategy = 'compact'  # No mandatory facts to assemble; record the actual fallback.
    if strategy == 'anchored-weave':
        if len(items) != 1:
            raise ValueError('Woven chronicles require one chapter per request')
        if anchored_chronicle.supported(items[0]):
            context, evidence = anchored_chronicle.weave_brief(items[0])
            return PreparedWriting(strategy, STRATEGY_VERSIONS[strategy], context + '\n\n' + evidence,
                                   anchored_chronicle.weave_schema(items[0]))
        strategy = 'compact'
    if strategy == 'anchored-stream':
        if len(items) != 1:
            raise ValueError('Stream chronicles require one chapter per request')
        if anchored_chronicle.supported(items[0]):
            context, evidence = anchored_chronicle.stream_brief(items[0])
            return PreparedWriting(strategy, STRATEGY_VERSIONS[strategy], context + '\n\n' + evidence,
                                   anchored_chronicle.stream_schema(items[0]))
        strategy = 'compact'
    writing = strategy in ('personal-brief', 'personal-thread', 'compact')
    schema = prose_schema(items) if writing else json.loads(Path(__file__).with_name('codex_batch_schema.json').read_text())
    results = schema['properties']['results']
    results.update(minItems=len(items), maxItems=len(items))
    results['items']['properties']['id']['enum'] = [item['id'] for item in items]
    if strategy == 'personal-thread':
        if len(items) != 1:
            raise ValueError('Threaded personal writing requires one request per call')
        context, evidence = build_threaded_brief(items[0], settings['strategy_options'].get(kind))
        prompt = context + '\n\nSupplied game evidence:\n' + evidence
    else:
        prompt = direct_prompt(items, writing, settings['strategy_options'].get(kind))
    return PreparedWriting(strategy, STRATEGY_VERSIONS[strategy], prompt, schema)


def decode(prepared, items, response):
    diagnostics = None
    if prepared.strategy == 'anchored':
        response = anchored_chronicle.assemble(items[0], response)
        diagnostics = response.get('writing_diagnostics')
    if prepared.strategy == 'anchored-weave':
        response = anchored_chronicle.assemble_weave(items[0], response)
        diagnostics = response.get('writing_diagnostics')
    if prepared.strategy == 'anchored-stream':
        response = anchored_chronicle.assemble_stream(items[0], response)
        diagnostics = response.get('writing_diagnostics')
    if prepared.strategy in ('anchored', 'anchored-weave', 'anchored-stream', 'personal-brief', 'personal-thread', 'compact'):
        response = adapt_prose(response)
    return response, diagnostics
