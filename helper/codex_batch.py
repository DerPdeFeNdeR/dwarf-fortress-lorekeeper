#!/usr/bin/env python3
"""Compatibility entry point: prepare a strategy, call a model, validate the envelope."""
import argparse
import json
from pathlib import Path

from model_adapters import select_adapter, run_process
from writer_settings import generation_settings, resolve_settings
from writing_strategies import prepare, decode, literary_prompt

MAX_BATCH_SIZE = 50
PROMPT_VERSION = '1'


def normalize_items(items):
    normalized, seen = [], set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError('each batch item must be an object')
        if not all(isinstance(item.get(key), str) and item[key] for key in ('id', 'kind', 'raw')):
            raise ValueError('each batch item needs non-empty id, kind, and raw fields')
        key = json.dumps({key: item.get(key, 'en' if key == 'language' else '')
                          for key in ('kind', 'raw', 'context', 'language')}, sort_keys=True)
        if key not in seen:
            seen.add(key); normalized.append(item)
    if len(normalized) > MAX_BATCH_SIZE:
        raise ValueError(f'batch exceeds the {MAX_BATCH_SIZE}-item limit')
    return normalized


def build_prompt(items):
    return literary_prompt(items)


def build_ollama_prompt(items):
    """Compatibility for old diagnostics; new callers should use prepare_batch."""
    return prepare_batch(items, resolve_settings({'provider': 'ollama'})).prompt


def prepare_batch(items, settings=None):
    return prepare(normalize_items(items), resolve_settings(settings) if settings is not None else generation_settings())


def validate_results(items, response):
    if not isinstance(response, dict):
        raise ValueError('Model response must be an object')
    results = response.get('results')
    if not isinstance(results, list) or len(results) != len(items):
        raise ValueError('Model result count does not match the request count')
    if not all(isinstance(result, dict) for result in results):
        raise ValueError('Model results must be objects')
    if [result.get('id') for result in results] != [item['id'] for item in items]:
        raise ValueError('Model results must preserve request order and ids')
    for result in results:
        if not all(isinstance(result.get(field), str) and result[field]
                   for field in ('id', 'text', 'explanation', 'category', 'confidence')):
            raise ValueError('Model returned an incomplete translation result')
        if result['confidence'] not in {'high', 'medium', 'low'}:
            raise ValueError('Model returned an invalid confidence value')
    return dict(schema_version=1, source='codex-cli', prompt_version=PROMPT_VERSION, results=results)


def run_batch(items, codex_command='codex', runner=None, *, settings=None, adapter=None):
    items = normalize_items(items)
    if not items:
        return dict(schema_version=1, source='codex-cli', prompt_version=PROMPT_VERSION, results=[])
    settings = resolve_settings(settings) if settings is not None else generation_settings()
    prepared = prepare(items, settings)
    adapter = adapter or select_adapter(settings['provider'], codex_command=codex_command, runner=runner)
    generated = adapter.generate(prompt=prepared.prompt, schema=prepared.schema, settings=settings)
    response, diagnostics = decode(prepared, items, generated.payload)
    result = validate_results(items, response)
    result.update(source=settings['provider'], generation=settings,
                  writing=prepared.provenance(), model_metrics=generated.metrics)
    if diagnostics is not None:
        result['writing_diagnostics'] = diagnostics
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    items = json.loads(args.input.read_text(encoding='utf-8'))
    if not isinstance(items, list):
        raise SystemExit('input must contain a JSON array')
    args.output.write_text(json.dumps(run_batch(items), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
