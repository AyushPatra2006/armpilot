"""
Tracks which models/quantizations are currently loaded/warm, manages switching,
and exposes load-time metrics back to benchmarking.
Owner: Member 3 (secondary: Member 1)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .ollama_client import OllamaClient, OllamaClientError, OllamaGenerationResult


@dataclass
class RuntimeConfiguration:
    model: str
    quantization: str
    threads: int
    context_window: int
    profile: str = "automatic"
    extra_flag: Optional[str] = None


class ModelManager:
    def __init__(self, client: Optional[OllamaClient] = None) -> None:
        self.client = client or OllamaClient()
        self._warm_models: set[str] = set()
        self._active_model: Optional[str] = None

    def select_model(self, recommendation: Dict[str, Any]) -> str:
        model = recommendation.get("model")
        if not model:
            raise ValueError("Recommendation missing model")
        return model

    def load_model(self, model: str) -> Dict[str, Any]:
        result = self.client.pull_model(model)
        self._warm_models.add(model)
        self._active_model = model
        return result

    def apply_configuration(self, recommendation: Dict[str, Any]) -> RuntimeConfiguration:
        model = self.select_model(recommendation)
        quantization = recommendation.get("quantization") or recommendation.get("quant") or "Q4_K_M"
        threads = int(recommendation.get("threads", 8))
        context_window = int(recommendation.get("context_window") or recommendation.get("context_length") or 8192)
        profile = str(recommendation.get("profile") or "automatic")
        extra_flag = recommendation.get("extra_flag")

        if model not in self._warm_models:
            self.load_model(model)

        return RuntimeConfiguration(
            model=model,
            quantization=quantization,
            threads=threads,
            context_window=context_window,
            profile=profile,
            extra_flag=extra_flag,
        )

    def run_inference(self, prompt: str, recommendation: Dict[str, Any]) -> OllamaGenerationResult:
        config = self.apply_configuration(recommendation)
        options = {
            "num_thread": config.threads,
            "num_ctx": config.context_window,
        }
        if config.extra_flag:
            options["extra_flag"] = config.extra_flag
        try:
            return self.client.generate_response(model=config.model, prompt=prompt, settings=options)
        except OllamaClientError:
            raise
