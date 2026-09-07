"""Resolve model-owned writing strategies and their transport/tuning."""
import copy
import json
import os
from pathlib import Path

STRATEGY_VERSIONS = {'luna-literary': '1', 'personal-brief': '1', 'personal-thread': '1', 'compact': '1',
                     'anchored': '1', 'anchored-weave': '1', 'anchored-stream': '1', 'translation': '1'}
OLLAMA_OPTIONS = dict(temperature=0.7, top_p=0.8, top_k=20, min_p=0,
                      num_ctx=20480, num_predict=2048, think=False)
FAST = {'memoire': 'personal-brief', 'chronicle': 'anchored'}
LITERARY = {'memoire': 'luna-literary', 'chronicle': 'luna-literary'}
PERSONAL_OPTIONS = {'quiet_words': [60, 100], 'busy_words': [100, 180], 'intro_words': [80, 140]}
PROFILES = {
    'qwen-fast': dict(provider='ollama', model='qwen3:8b', strategies=FAST),
    'qwen-weave': dict(provider='ollama', model='qwen3:8b',
                       strategies={'memoire': 'personal-brief', 'chronicle': 'anchored-weave'},
                       model_options={'temperature': 0.5}),
    'qwen-stream': dict(provider='ollama', model='qwen3:8b',
                        strategies={'memoire': 'personal-brief', 'chronicle': 'anchored-stream'},
                        model_options={'temperature': 0.6}),
    'qwen-thread': dict(provider='ollama', model='qwen3:8b',
                        strategies={'memoire': 'personal-thread', 'chronicle': 'anchored-stream'},
                        model_options={'temperature': 0.6}),
    'qwen-compact': dict(provider='ollama', model='qwen3:8b',
                         strategies={'memoire': 'personal-brief', 'chronicle': 'compact'}),
    'luna-literary': dict(provider='codex-cli', model='gpt-5.6-luna', strategies=LITERARY),
}
MODEL_POLICIES = {
    'qwen3:8b': dict(provider='ollama', profile='qwen-fast',
                    allowed={'memoire': {'personal-brief', 'personal-thread'}, 'chronicle': {'anchored', 'anchored-weave', 'anchored-stream', 'compact'}}),
    'gpt-5.6-luna': dict(provider='codex-cli', profile='luna-literary',
                        allowed={'memoire': {'luna-literary'}, 'chronicle': {'luna-literary'}}),
}


def validate_options(options):
    if set(options) - OLLAMA_OPTIONS.keys():
        raise ValueError('Unknown Ollama tuning option: ' + ', '.join(sorted(set(options) - OLLAMA_OPTIONS.keys())))
    for key, value in options.items():
        if key == 'think':
            valid = type(value) is bool
        elif key in ('num_ctx', 'num_predict', 'top_k'):
            valid = type(value) is int and value > 0
        else:
            upper = 2 if key == 'temperature' else 1
            valid = type(value) in (int, float) and 0 <= value <= upper
        if not valid:
            raise ValueError(f'Invalid model option: {key}')


def resolve_settings(settings):
    """Canonical cache identity, including effective defaults and strategy versions.

Partial older callers default to Codex, as before. Persisted requested settings
are snapshots: this function never merges the current process environment.
"""
    settings = copy.deepcopy(settings)
    provider = settings.get('provider', 'codex-cli')
    if provider not in ('ollama', 'codex-cli'):
        raise ValueError('LOREKEEPER_PROVIDER must be ollama or codex-cli')
    defaults = PROFILES['qwen-fast' if provider == 'ollama' else 'luna-literary']
    model = settings.get('model', defaults['model'])
    effort = settings.get('reasoning_effort', 'low')
    if not isinstance(model, str) or not model.strip():
        raise ValueError('LOREKEEPER_MODEL must not be empty')
    model = model.strip()
    if model not in MODEL_POLICIES:
        raise ValueError(f'No model-specific writing policy registered for {model}')
    policy = MODEL_POLICIES[model]
    if provider != policy['provider']:
        raise ValueError(f'{model} requires provider {policy["provider"]}')
    defaults = PROFILES[policy['profile']]
    if effort not in ('none', 'low', 'medium', 'high', 'xhigh', 'max'):
        raise ValueError('Invalid LOREKEEPER_REASONING_EFFORT')
    for key in ('strategies', 'model_options', 'strategy_options'):
        if key in settings and not isinstance(settings[key], dict):
            raise ValueError(f'{key} must be an object')
    strategies = dict(defaults['strategies'], **settings.get('strategies', {}))
    allowed = policy['allowed']
    if set(strategies) != set(allowed) or any(value not in allowed[key] for key, value in strategies.items()):
        raise ValueError(f'Writing strategy is not registered for {model} and content type')
    options = dict(OLLAMA_OPTIONS, **settings.get('model_options', {})) if provider == 'ollama' else settings.get('model_options', {})
    if provider == 'codex-cli' and options:
        raise ValueError('Codex CLI uses reasoning_effort; Ollama model_options are not supported')
    validate_options(options)
    strategy_options = {'memoire': dict(PERSONAL_OPTIONS) if strategies['memoire'] in ('personal-brief', 'personal-thread') else {}, 'chronicle': {}}
    for kind, tuning in settings.get('strategy_options', {}).items():
        if kind not in strategy_options or not isinstance(tuning, dict) or set(tuning) - strategy_options[kind].keys():
            raise ValueError('Unsupported options for the selected writing strategy')
        strategy_options[kind].update(tuning)
    for bounds in strategy_options['memoire'].values():
        if not isinstance(bounds, list) or len(bounds)!=2 or any(type(n) is not int for n in bounds) or not 1 <= bounds[0] <= bounds[1] <= 300:
            raise ValueError('Word targets require [minimum, maximum] within 1–300; mandatory facts take priority')
    return dict(provider=provider, model=model.strip(), reasoning_effort=effort,
                model_options=options, strategies=strategies,
                strategy_options=strategy_options,
                strategy_versions={key: STRATEGY_VERSIONS[value] for key, value in strategies.items()},
                translation_version=STRATEGY_VERSIONS['translation'], writer_protocol=1)


def generation_settings(*, profile=None, overrides=None):
    profiles = copy.deepcopy(PROFILES)
    config = os.environ.get('LOREKEEPER_WRITER_CONFIG')
    if config:
        custom = json.loads(Path(config).read_text(encoding='utf-8'))
        if not isinstance(custom, dict) or not isinstance(custom.get('profiles'), dict):
            raise ValueError('Writer config must contain a profiles object')
        profiles.update(custom['profiles'])
    profile = profile or os.environ.get('LOREKEEPER_WRITER_PROFILE') or (
        'luna-literary' if os.environ.get('LOREKEEPER_PROVIDER', '').strip().lower() == 'codex-cli' else 'qwen-fast')
    if profile not in profiles or not isinstance(profiles[profile], dict):
        raise ValueError(f'Unknown writer profile: {profile}')
    value = copy.deepcopy(profiles[profile])
    for key, env in [('provider', 'LOREKEEPER_PROVIDER'), ('model', 'LOREKEEPER_MODEL'),
                     ('reasoning_effort', 'LOREKEEPER_REASONING_EFFORT')]:
        if env in os.environ:
            value[key] = os.environ[env].strip()
    value['provider'] = value.get('provider', 'ollama').lower()
    strategies = dict(value.get('strategies', {}))
    for kind in ('memoire', 'chronicle'):
        env = 'LOREKEEPER_' + kind.upper() + '_STRATEGY'
        if env in os.environ:
            strategies[kind] = os.environ[env].strip()
    value['strategies'] = strategies
    if 'LOREKEEPER_MODEL_OPTIONS' in os.environ:
        value['model_options'] = json.loads(os.environ['LOREKEEPER_MODEL_OPTIONS'])
    if 'LOREKEEPER_STRATEGY_OPTIONS' in os.environ:
        value['strategy_options'] = json.loads(os.environ['LOREKEEPER_STRATEGY_OPTIONS'])
    for key, item in (overrides or {}).items():
        if key in ('strategies', 'model_options', 'strategy_options'):
            value[key] = dict(value.get(key, {}), **item)
        else:
            value[key] = item
    return resolve_settings(value)
