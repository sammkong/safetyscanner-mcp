"""Rule-based listing risk scoring."""

from __future__ import annotations

import re
from typing import TypedDict

from safetyscanner.signals import HIGH, LOW, MEDIUM, SIGNALS


class MatchedSignal(TypedDict):
    id: str
    category: str
    label: str
    weight: int
    weight_label: str
    scam_type: str
    why: str


class ScoreResult(TypedDict):
    score: int
    band: str
    matched: list[MatchedSignal]
    evidence: list[str]


def score_text(text: str) -> ScoreResult:
    """Score text with simple regex signal matching."""
    matched: list[MatchedSignal] = []
    evidence: list[str] = []
    raw_matches: dict[str, list[str]] = {}

    for signal in SIGNALS:
        signal_evidence = _match_signal_patterns(text, signal["patterns"])
        if not signal_evidence:
            continue
        raw_matches[str(signal["id"])] = signal_evidence

    raw_match_ids = set(raw_matches)

    for signal in SIGNALS:
        signal_id = str(signal["id"])
        signal_evidence = raw_matches.get(signal_id)
        if not signal_evidence or not _requirements_met(signal, raw_match_ids):
            continue
        weight = int(signal["weight"])
        matched.append(
            {
                "id": signal_id,
                "category": str(signal["category"]),
                "label": str(signal["label"]),
                "weight": weight,
                "weight_label": weight_to_label(weight),
                "scam_type": str(signal["scam_type"]),
                "why": str(signal["why"]),
            }
        )
        evidence.extend(signal_evidence)

    score = min(sum(item["weight"] for item in matched), 100)
    return {
        "score": score,
        "band": score_to_band(score),
        "matched": matched,
        "evidence": _dedupe(evidence),
    }


def _requirements_met(signal: dict[str, object], raw_match_ids: set[str]) -> bool:
    required = signal.get("requires_any")
    if not required:
        return True
    return any(str(signal_id) in raw_match_ids for signal_id in required)


def score_to_band(score: int) -> str:
    if score <= 30:
        return "안전"
    if score <= 60:
        return "주의"
    return "위험"


def weight_to_label(weight: int) -> str:
    if weight == HIGH:
        return "높음"
    if weight == MEDIUM:
        return "중간"
    if weight == LOW:
        return "낮음"
    return str(weight)


def _match_signal_patterns(text: str, patterns: object) -> list[str]:
    for pattern in patterns:
        match = re.search(str(pattern), text, flags=re.IGNORECASE)
        if match:
            return [_snippet(text, match.start(), match.end())]
    return []


def _snippet(text: str, start: int, end: int) -> str:
    return text[start:end].strip()


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result
