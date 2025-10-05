from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.config import get_settings
from app.schemas import CoachingResponse, CoachingScore


class Threshold(BaseModel):
    metric: str
    operator: str
    value: float


class StateResponse(BaseModel):
    subtitle: str
    tip: str
    tts_text: str
    state_id: str = Field(alias="id")


class StateRule(BaseModel):
    id: str
    name: str
    thresholds: List[Threshold]
    default: bool = False
    response: StateResponse

    model_config = {
        "populate_by_name": True,
    }


class StateMachine:
    def __init__(self, rules: List[StateRule]):
        self._rules = rules
        self._default = next((rule for rule in rules if rule.default), rules[-1])

    def evaluate(self, session_id: str, scores: CoachingScore, latency_ms: Optional[float] = None) -> CoachingResponse:
        rule = self._select_rule(scores)
        response = rule.response
        return CoachingResponse(
            session_id=session_id,
            state=rule.name,
            scores=scores,
            subtitle=response.subtitle,
            tip=response.tip,
            tts_text=response.tts_text,
            transcript_highlights=[],
            latency_ms=latency_ms,
        )

    def _select_rule(self, scores: CoachingScore) -> StateRule:
        for rule in self._rules:
            if self._rule_matches(rule, scores):
                return rule
        return self._default

    def _rule_matches(self, rule: StateRule, scores: CoachingScore) -> bool:
        for threshold in rule.thresholds:
            metric_value = getattr(scores, threshold.metric, None)
            if metric_value is None:
                return False
            if not self._compare(metric_value, threshold.operator, threshold.value):
                return False
        return True

    @staticmethod
    def _compare(metric: float, operator: str, expected: float) -> bool:
        if operator == ">=" or operator == "gte":
            return metric >= expected
        if operator == ">" or operator == "gt":
            return metric > expected
        if operator == "<=" or operator == "lte":
            return metric <= expected
        if operator == "<" or operator == "lt":
            return metric < expected
        if operator == "==" or operator == "eq":
            return abs(metric - expected) <= 1e-6
        if operator == "!=" or operator == "ne":
            return abs(metric - expected) > 1e-6
        raise ValueError(f"Unsupported operator: {operator}")


def load_state_machine(path: Optional[str] = None) -> StateMachine:
    settings = get_settings()
    rules_path = Path(path or settings.coaching_rules_path)
    with rules_path.open("r", encoding="utf-8") as f:
        payload: Dict[str, Any] = json.load(f)
    rules = [StateRule.model_validate(rule) for rule in payload["states"]]
    return StateMachine(rules)
