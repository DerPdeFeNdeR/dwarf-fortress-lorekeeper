#!/usr/bin/env python3
"""Run one efficient, structured translation batch through Codex CLI."""

from __future__ import annotations

import argparse
import json
import subprocess
import os
import signal
import tempfile
from pathlib import Path
from typing import Any, Callable


MAX_BATCH_SIZE = 50
PROMPT_VERSION = "1"
DEFAULT_MODEL = "gpt-5.6-luna"
DEFAULT_REASONING_EFFORT = "low"


def generation_settings() -> dict[str, str]:
    """Keep the game worker independent of interactive Codex model defaults."""
    model = os.environ.get('LOREKEEPER_MODEL', DEFAULT_MODEL).strip()
    effort = os.environ.get('LOREKEEPER_REASONING_EFFORT', DEFAULT_REASONING_EFFORT).strip()
    if not model:
        raise ValueError('LOREKEEPER_MODEL must not be empty')
    if effort not in {'none', 'low', 'medium', 'high', 'xhigh', 'max'}:
        raise ValueError('Invalid LOREKEEPER_REASONING_EFFORT')
    return dict(model=model, reasoning_effort=effort)


def run_process(command, *, input, timeout, encoding, **_options):
    with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, encoding=encoding,
                          start_new_session=True) as process:
        try:
            stdout, stderr = process.communicate(input, timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            raise RuntimeError('Model generation exceeded its time limit.')
        return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def normalize_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop duplicate work while preserving the first item's order."""
    normalized = []
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("each batch item must be an object")
        item_id = item.get("id")
        kind = item.get("kind")
        raw = item.get("raw")
        if not all(isinstance(value, str) and value for value in (item_id, kind, raw)):
            raise ValueError("each batch item needs non-empty id, kind, and raw fields")
        key = json.dumps(
            {
                "kind": kind,
                "raw": raw,
                "context": item.get("context", ""),
                "language": item.get("language", "en"),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        if key not in seen:
            seen.add(key)
            normalized.append(item)

    if len(normalized) > MAX_BATCH_SIZE:
        raise ValueError(f"batch exceeds the {MAX_BATCH_SIZE}-item limit")
    return normalized


def build_prompt(items: list[dict[str, Any]]) -> str:
    return (
        "Process the following Lorekeeper translation batch. Use only the supplied "
        "raw values and context. Do not inspect, edit, or create files. Do not invent "
        "game events or facts. Return one result for every item, preserving each id. "
        "Keep text and explanation concise.\n\n"
        + json.dumps(items, ensure_ascii=False, sort_keys=True, indent=2)
    )


def validate_results(items: list[dict[str, Any]], response: dict[str, Any]) -> dict[str, Any]:
    results = response.get("results")
    if not isinstance(results, list) or len(results) != len(items):
        raise ValueError("Codex result count does not match the request count")

    expected_ids = [item["id"] for item in items]
    actual_ids = [result.get("id") for result in results]
    if actual_ids != expected_ids:
        raise ValueError("Codex results must preserve request order and ids")

    required = ("id", "text", "explanation", "category", "confidence")
    for result in results:
        if not all(isinstance(result.get(field), str) and result[field] for field in required):
            raise ValueError("Codex returned an incomplete translation result")
        if result["confidence"] not in {"high", "medium", "low"}:
            raise ValueError("Codex returned an invalid confidence value")

    return {
        "schema_version": 1,
        "source": "codex-cli",
        "prompt_version": PROMPT_VERSION,
        "results": results,
    }


def run_batch(
    items: list[dict[str, Any]],
    codex_command: str = "codex",
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    *, settings: dict[str, str] | None = None,
) -> dict[str, Any]:
    items = normalize_items(items)
    if not items:
        return {"schema_version": 1, "source": "codex-cli", "prompt_version": PROMPT_VERSION, "results": []}

    runner = runner or run_process
    settings = settings or generation_settings()
    schema_path = Path(__file__).with_name("codex_batch_schema.json")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as output_file:
        output_path = Path(output_file.name)

    command = [
        codex_command,
        "exec",
        "--model", settings['model'],
        "-c", 'model_reasoning_effort=' + json.dumps(settings['reasoning_effort']),
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--output-schema",
        str(schema_path),
        "-o",
        str(output_path),
        "Translate the supplied Lorekeeper batch and return only the requested structured results.",
    ]
    try:
        completed = runner(
            command,
            input=build_prompt(items),
            text=True,
            capture_output=True,
            check=False,
            timeout=180,
            encoding='utf-8',
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "Codex exited unsuccessfully").strip()
            raise RuntimeError(f"codex exec failed: {detail[-1000:]}")
        try:
            response = json.loads(output_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            raise RuntimeError("codex exec did not produce valid structured output") from exc
        result = validate_results(items, response)
        result['generation'] = dict(settings)
        return result
    finally:
        output_path.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON file containing a translation array")
    parser.add_argument("output", type=Path, help="JSON file to write structured results to")
    args = parser.parse_args()

    items = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(items, list):
        raise SystemExit("input must contain a JSON array")
    result = run_batch(items)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
