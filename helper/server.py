#!/usr/bin/env python3
"""Local, optional Lorekeeper translation helper.

The DFHack scripts do not call OpenAI directly. This process owns the API key,
keeps a small persistent cache, and exposes only localhost HTTP endpoints.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from collections import deque
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib import error, request


MODEL = os.environ.get("LOREKEEPER_MODEL", "gpt-5-mini")
PROMPT_VERSION = "1"
SCHEMA_VERSION = 1
MAX_RAW_LENGTH = 512
MAX_CONTEXT_LENGTH = 4000
MAX_OUTPUT_TOKENS = 300
MAX_REQUESTS_PER_MINUTE = 30
OPENAI_URL = "https://api.openai.com/v1/responses"

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "explanation": {"type": "string"},
        "category": {"type": "string"},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
    },
    "required": ["text", "explanation", "category", "confidence"],
    "additionalProperties": False,
}


def default_cache_path() -> Path:
    configured = os.environ.get("LOREKEEPER_CACHE_PATH")
    if configured:
        return Path(configured)
    return Path.home() / ".lorekeeper" / "translation-cache.json"


def _bounded_string(value: Any, field: str, limit: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    if len(value) > limit:
        raise ValueError(f"{field} exceeds the {limit}-character limit")
    return value


def _cache_key(payload: dict[str, Any], model: str) -> str:
    key_data = {
        "schema_version": SCHEMA_VERSION,
        "prompt_version": PROMPT_VERSION,
        "model": model,
        "language": payload.get("language", "en"),
        "kind": payload["kind"],
        "raw": payload["raw"],
        "context": payload.get("context", ""),
    }
    encoded = json.dumps(key_data, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _response_text(response: dict[str, Any]) -> str:
    output_text = response.get("output_text")
    if isinstance(output_text, str) and output_text:
        return output_text

    for item in response.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                return content["text"]
    raise ValueError("OpenAI response did not contain output text")


def call_openai(api_key: str, model: str, prompt: str, timeout: float = 20.0) -> dict[str, Any]:
    body = {
        "model": model,
        "instructions": (
            "You explain Dwarf Fortress tokens for a player. Stay grounded in the "
            "provided raw token and context. Do not invent events, diagnoses, or "
            "facts. Keep text and explanation concise."
        ),
        "input": prompt,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "lorekeeper_translation",
                "strict": True,
                "schema": OUTPUT_SCHEMA,
            }
        },
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "store": False,
    }
    api_request = request.Request(
        OPENAI_URL,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(api_request, timeout=timeout) as response:
            decoded = json.loads(response.read().decode())
    except error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:500]
        raise RuntimeError(f"OpenAI request failed with HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"OpenAI request failed: {exc.reason}") from exc

    try:
        result = json.loads(_response_text(decoded))
    except json.JSONDecodeError as exc:
        raise RuntimeError("OpenAI returned invalid structured JSON") from exc

    if not all(isinstance(result.get(field), str) for field in ("text", "explanation", "category")):
        raise RuntimeError("OpenAI response was missing required translation fields")
    if result.get("confidence") not in {"high", "medium", "low"}:
        raise RuntimeError("OpenAI response contained an invalid confidence value")
    return result


class TranslationService:
    def __init__(
        self,
        cache_path: Path | str | None = None,
        api_key: str | None = None,
        model: str = MODEL,
        request_fn: Callable[[str, str, str], dict[str, Any]] = call_openai,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.cache_path = Path(cache_path) if cache_path else default_cache_path()
        self.api_key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.request_fn = request_fn
        self.clock = clock
        self.request_times: deque[float] = deque()
        self.cache = self._load_cache()

    def _load_cache(self) -> dict[str, Any]:
        try:
            with self.cache_path.open(encoding="utf-8") as cache_file:
                data = json.load(cache_file)
            return data if isinstance(data, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}

    def _save_cache(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=self.cache_path.parent, delete=False
        ) as cache_file:
            json.dump(self.cache, cache_file, sort_keys=True, indent=2)
            cache_file.write("\n")
            temporary_path = cache_file.name
        os.replace(temporary_path, self.cache_path)

    def _check_rate_limit(self) -> None:
        now = self.clock()
        while self.request_times and now - self.request_times[0] >= 60:
            self.request_times.popleft()
        if len(self.request_times) >= MAX_REQUESTS_PER_MINUTE:
            raise RuntimeError("local helper rate limit reached; try again later")
        self.request_times.append(now)

    def translate(self, payload: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        kind = _bounded_string(payload.get("kind"), "kind", 64)
        raw = _bounded_string(payload.get("raw"), "raw", MAX_RAW_LENGTH)
        context = payload.get("context", "")
        if not isinstance(context, str):
            raise ValueError("context must be a string")
        if len(context) > MAX_CONTEXT_LENGTH:
            raise ValueError(f"context exceeds the {MAX_CONTEXT_LENGTH}-character limit")

        normalized = {"kind": kind, "raw": raw, "context": context}
        if "language" in payload:
            normalized["language"] = _bounded_string(payload["language"], "language", 32)
        key = _cache_key(normalized, self.model)
        cached = self.cache.get(key)
        if isinstance(cached, dict):
            return cached | {"cache": "hit"}, True

        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        self._check_rate_limit()
        prompt = json.dumps(normalized, ensure_ascii=False, sort_keys=True)
        model_result = self.request_fn(self.api_key, self.model, prompt)
        result = {
            "schema_version": SCHEMA_VERSION,
            "kind": kind,
            "known": True,
            "raw": raw,
            "text": model_result["text"],
            "explanation": model_result["explanation"],
            "category": model_result["category"],
            "source": "model",
            "confidence": model_result["confidence"],
            "model": self.model,
            "prompt_version": PROMPT_VERSION,
        }
        self.cache[key] = result
        self._save_cache()
        return result | {"cache": "miss"}, False


class Handler(BaseHTTPRequestHandler):
    service: TranslationService

    def _send_json(self, status: HTTPStatus, body: dict[str, Any]) -> None:
        encoded = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json(HTTPStatus.OK, {"ok": True, "model": self.service.model})
        else:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/translate":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 8192:
                raise ValueError("request body exceeds the 8192-byte limit")
            payload = json.loads(self.rfile.read(length))
            result, _ = self.service.translate(payload)
            self._send_json(HTTPStatus.OK, result)
        except (ValueError, json.JSONDecodeError) as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except RuntimeError as exc:
            self._send_json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": str(exc)})

    def log_message(self, format: str, *args: Any) -> None:
        return


def main() -> None:
    host = os.environ.get("LOREKEEPER_HOST", "127.0.0.1")
    port = int(os.environ.get("LOREKEEPER_PORT", "8765"))
    service = TranslationService()
    Handler.service = service
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Lorekeeper helper listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
