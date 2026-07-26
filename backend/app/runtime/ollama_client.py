"""
Wraps the Ollama API: model pull, load, switch, generate.
Owner: Member 3 (secondary: Member 1)
RISK: cold model switches cause latency spikes. Pre-warm/pre-pull all demo models
before any live demo. See docs/SCHEDULE.md Day 2 validation task.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx


@dataclass
class OllamaGenerationResult:
    response: str
    tokens_generated: int
    latency: float
    tokens_per_second: float
    time_to_first_token: float
    model: str
    raw: Dict[str, Any]


class OllamaClientError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, base_url: Optional[str] = None, timeout: float = 120.0) -> None:
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=self.timeout) as client:
            response = client.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    def list_tags(self) -> Dict[str, Any]:
        return self._request("GET", "/api/tags").json()

    def pull_model(self, model: str) -> Dict[str, Any]:
        return self._request("POST", "/api/pull", json={"name": model, "stream": False}).json()

    def show_model(self, model: str) -> Dict[str, Any]:
        return self._request("POST", "/api/show", json={"name": model}).json()

    def generate_response(self, model: str, prompt: str, settings: Optional[Dict[str, Any]] = None) -> OllamaGenerationResult:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": settings or {},
        }
        started = time.perf_counter()
        try:
            response = self._request("POST", "/api/generate", json=payload)
        except httpx.HTTPError as exc:
            raise OllamaClientError(f"Ollama request failed: {exc}") from exc

        elapsed = time.perf_counter() - started
        data = response.json()
        response_text = data.get("response", "")
        eval_count = int(data.get("eval_count") or 0)
        eval_duration_ns = float(data.get("eval_duration") or 0.0)
        load_duration_ns = float(data.get("load_duration") or 0.0)
        prompt_eval_duration_ns = float(data.get("prompt_eval_duration") or 0.0)
        prompt_eval_count = int(data.get("prompt_eval_count") or 0)
        total_duration_s = float(data.get("total_duration") or (elapsed * 1e9)) / 1e9

        tokens_generated = eval_count or max(0, len(response_text.split()))
        inference_duration_s = max(total_duration_s - (load_duration_ns / 1e9) - (prompt_eval_duration_ns / 1e9), 1e-9)
        tokens_per_second = tokens_generated / inference_duration_s if tokens_generated else 0.0
        time_to_first_token = float(data.get("time_to_first_token") or (prompt_eval_duration_ns / 1e9 if prompt_eval_count else 0.0))

        return OllamaGenerationResult(
            response=response_text,
            tokens_generated=tokens_generated,
            latency=total_duration_s,
            tokens_per_second=tokens_per_second,
            time_to_first_token=time_to_first_token,
            model=model,
            raw=data,
        )
