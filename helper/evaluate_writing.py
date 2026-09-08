"""Opt-in model/strategy comparison; never publishes stories into a save.

Input is one captured batch item (or a one-item array). Reports contain private
game evidence/prose: put --output under the ignored .lorekeeper directory.
"""
import argparse
import copy
import json
import time
from pathlib import Path

from codex_batch import prepare_batch, generation_settings, run_batch
from fortress_calendar import MONTH_TICKS
from story_coverage import validate, CoverageError


def annual_sections(item):
    """Experimental seasonal partition; every event and coverage row stays assigned."""
    raw = json.loads(item['raw'])
    buckets, assignments = {}, {}
    for field, identity in [('events', 'id'), ('cultural_events', 'source_key')]:
        for event in raw.get(field, []):
            tick = (event.get('time') or {}).get('tick')
            season = tick // (3 * MONTH_TICKS) if type(tick) is int and 0 <= tick < 12 * MONTH_TICKS else -1
            bucket = buckets.setdefault(season, dict(events=[], cultural_events=[], required_event_coverage=[]))
            bucket[field].append(event)
            assignments[event[identity]] = season
    for row in raw.get('required_event_coverage', []):
        if row['event_id'] not in assignments:
            raise ValueError('Required fact has no section assignment')
        buckets[assignments[row['event_id']]]['required_event_coverage'].append(row)
    result = []
    for index, season in enumerate(sorted(buckets)):
        section = dict(raw, **buckets[season], section_index=index + 1, section_count=len(buckets))
        result.append(dict(item, id=item['id'] + f':section:{index}', raw=json.dumps(section, ensure_ascii=False)))
    return result


def evaluate(item, sections=False, settings=None):
    settings = settings if settings is not None else generation_settings()
    metrics, writing, errors = [], [], []
    tasks = annual_sections(item) if sections else [item]
    prose, failures = [], []
    started = time.perf_counter()
    for task in tasks:
        writing.append(prepare_batch([task],settings).provenance())
        try:
            result = run_batch([task], settings=settings)
            metrics.append(result.get('model_metrics', {}))
            text = result['results'][0]['text']
            prose.append(text)
            try:
                validate(text, json.loads(task['raw']).get('required_event_coverage', []))
            except CoverageError as error:
                failures.extend(error.missing_event_ids)
        except Exception as error:
            errors.append(str(error))
    return dict(seconds=time.perf_counter()-started, calls=len(tasks), metrics=metrics,
                prompt_bytes=[len(prepare_batch([task],settings).prompt.encode()) for task in tasks],
                missing_event_ids=failures, errors=errors, writing=writing,
                text='\n\n'.join(prose), generation=settings)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--sections', action='store_true', help='Compare experimental annual sections')
    parser.add_argument('--profile', action='append', help='Repeat to compare named profiles on identical evidence')
    parser.add_argument('--provider', choices=['ollama'])
    parser.add_argument('--model')
    parser.add_argument('--memoire-strategy', choices=['personal-thread'])
    parser.add_argument('--chronicle-strategy', choices=['anchored-stream'])
    parser.add_argument('--model-options', type=json.loads, help='Ollama tuning as a JSON object')
    parser.add_argument('--strategy-options', type=json.loads, help='Writing tuning by content type as JSON')
    parser.add_argument('--reasoning-effort')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Use a new output path to preserve earlier evaluations')
    value = json.loads(args.input.read_text(encoding='utf-8'))
    item = value[0] if isinstance(value, list) and len(value) == 1 else value
    if not isinstance(item, dict):
        parser.error('Input must contain exactly one captured batch item')
    if args.sections and item.get('kind') != 'fortress_year':
        parser.error('Section comparison supports annual chronicles only')
    overrides = {key: getattr(args,key) for key in ('provider','model','model_options','strategy_options','reasoning_effort')
                 if getattr(args,key) is not None}
    overrides['strategies'] = {kind: getattr(args,kind+'_strategy') for kind in ('memoire','chronicle')
                               if getattr(args,kind+'_strategy') is not None}
    reports = []
    for profile in args.profile or [None]:
        report = evaluate(copy.deepcopy(item), args.sections, generation_settings(profile=profile, overrides=overrides))
        report['profile'] = profile
        reports.append(report)
        print(json.dumps({key: value for key,value in report.items() if key != 'text'}), flush=True)
    report = reports[0] if len(reports)==1 else {'comparisons': reports}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
