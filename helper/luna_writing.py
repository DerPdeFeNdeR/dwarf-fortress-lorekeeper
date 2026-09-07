"""Luna's full-context, whole-passage writing policy."""
import json
from pathlib import Path


def build_prompt(items):
    return ('Process the following Lorekeeper translation batch. Use only the supplied '
            'raw values and context. Do not inspect, edit, or create files. Do not invent '
            'game events or facts. Return one result for every item, preserving each id. '
            'Follow each item\'s requested text length and coverage; keep explanation concise.\n\n'
            + json.dumps(items, ensure_ascii=False, sort_keys=True, indent=2))


def prepare(items):
    schema = json.loads(Path(__file__).with_name('codex_batch_schema.json').read_text())
    results = schema['properties']['results']
    results.update(minItems=len(items), maxItems=len(items))
    results['items']['properties']['id']['enum'] = [item['id'] for item in items]
    return build_prompt(items), schema
