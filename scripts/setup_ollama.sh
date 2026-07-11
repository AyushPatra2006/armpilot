#!/usr/bin/env bash
# Pulls all model/quant variants used in the demo, ahead of time, to avoid cold-load
# latency during live demo. Run this BEFORE any demo or benchmark session.
# Example:
# ollama pull qwen3:8b-int8
# ollama pull qwen3:8b-int4
