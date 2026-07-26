"""
FR-3: Workload Classification.
V1: keyword/heuristic based (fast to ship, easy to explain to judges).
Categories: chat, coding, summarization, long-context analysis, document QA, creative writing.
Owner: Member 2 (secondary: Member 3)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict


@dataclass
class WorkloadClassification:
    label: str
    confidence: float
    reason: str


def classify_workload(prompt: str) -> WorkloadClassification:
    text = prompt.lower().strip()
    if not text:
        return WorkloadClassification(label="chat", confidence=0.3, reason="Empty prompt defaults to chat")

    rules = [
        ("coding", [r"\bbug\b", r"\berror\b", r"\btraceback\b", r"\bfix\b", r"\bcode\b", r"\bpython\b", r"\bjavascript\b", r"\btypescript\b", r"\bcompile\b"]),
        ("summarization", [r"\bsummar", r"\btl;dr\b", r"\brecap\b", r"\bbrief\b"]),
        ("long_context", [r"\bchapter\b", r"\bpaper\b", r"\bdocument\b", r"\b250-page\b", r"\blong context\b", r"\banalyze.*document\b"]),
        ("document_qa", [r"\bwhat does\b", r"\baccording to\b", r"\bfind in\b", r"\bquestion-answer\b"]),
        ("creative_writing", [r"\bstory\b", r"\bpoem\b", r"\bwrite a scene\b", r"\bfiction\b"]),
    ]
    for label, patterns in rules:
        if any(re.search(pattern, text) for pattern in patterns):
            return WorkloadClassification(label=label, confidence=0.85, reason=f"Matched {label} keywords")
    return WorkloadClassification(label="chat", confidence=0.55, reason="No strong heuristic match")
