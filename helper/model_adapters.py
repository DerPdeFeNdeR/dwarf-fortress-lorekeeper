"""Model transports accept a prompt/schema and know no writing strategies."""
import json
import os
import signal
import subprocess
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ModelResponse:
    payload: dict
    metrics: dict


def run_process(command, *, input, timeout, encoding, **_options):
    with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, encoding=encoding,
                          start_new_session=os.name != 'nt') as process:
        try:
            stdout, stderr = process.communicate(input, timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True, timeout=10)
                process.kill()
            else:
                os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            raise RuntimeError('Model generation exceeded its time limit.')
        return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


class OllamaAdapter:
    def generate(self, prompt, schema, settings):
        options = dict(settings['model_options'])
        thinking = options.pop('think')
        payload = json.dumps(dict(model=settings['model'], prompt=prompt, format=schema,
            stream=False, think=thinking, truncate=False, shift=False, keep_alive='30m', options=options)).encode('utf-8')
        request = urllib.request.Request(
            os.environ.get('LOREKEEPER_OLLAMA_URL', 'http://127.0.0.1:11434/api/generate'),
            data=payload, headers={'Content-Type': 'application/json'}, method='POST')
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                body = json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as exc:
            detail = exc.read(2048).decode('utf-8', errors='replace')
            raise RuntimeError(f'Ollama rejected the request ({exc.code}): {detail}') from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f'Ollama generation failed: {exc}') from exc
        if not isinstance(body, dict):
            raise RuntimeError('Ollama response must be an object')
        if body.get('done') is not True or body.get('done_reason') == 'length':
            raise RuntimeError('Ollama response was incomplete; previous prose is preserved')
        try:
            result = json.loads(body['response'])
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError('Ollama did not return valid structured output') from exc
        metrics = {key: body.get(key) for key in ('model', 'prompt_eval_count', 'prompt_eval_duration',
            'eval_count', 'eval_duration', 'load_duration', 'total_duration', 'done_reason')}
        return ModelResponse(result, metrics)


class CodexAdapter:
    def __init__(self, command='codex', runner=None):
        self.command = command
        self.runner = runner or run_process

    def generate(self, prompt, schema, settings):
        with tempfile.TemporaryDirectory(prefix='lorekeeper-model-') as directory:
            schema_path = Path(directory) / 'schema.json'
            output_path = Path(directory) / 'response.json'
            schema_path.write_text(json.dumps(schema), encoding='utf-8')
            command = [self.command, 'exec', '--model', settings['model'],
                '-c', 'model_reasoning_effort=' + json.dumps(settings['reasoning_effort']),
                '--ephemeral', '--sandbox', 'read-only', '--output-schema', str(schema_path),
                '-o', str(output_path),
                'Follow the supplied writing task and return only its requested structured output.']
            completed = self.runner(command, input=prompt, text=True, capture_output=True,
                                    check=False, timeout=180, encoding='utf-8')
            if completed.returncode != 0:
                detail = (completed.stderr or completed.stdout or 'Codex exited unsuccessfully').strip()
                raise RuntimeError(f'Codex generation failed: {detail[-1000:]}')
            try:
                result = json.loads(output_path.read_text(encoding='utf-8'))
            except (FileNotFoundError, json.JSONDecodeError) as exc:
                raise RuntimeError('Codex did not produce valid structured output') from exc
            return ModelResponse(result, {})


def select_adapter(provider, *, codex_command='codex', runner=None):
    if provider == 'ollama':
        return OllamaAdapter()
    if provider == 'codex-cli':
        return CodexAdapter(codex_command, runner)
    raise ValueError(f'Unsupported model provider: {provider}')
