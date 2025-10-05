from app.schemas import CoachingScore
from app.services.state_machine import load_state_machine


def test_high_anxiety_state(tmp_path):
    rules = {
        "states": [
            {
                "id": "anxious",
                "name": "Anxious",
                "default": False,
                "thresholds": [{"metric": "anxiety", "operator": ">=", "value": 0.6}],
                "response": {
                    "id": "anxious",
                    "subtitle": "Breathe",
                    "tip": "Slow down",
                    "tts_text": "Breathe"
                }
            },
            {
                "id": "default",
                "name": "Default",
                "default": True,
                "thresholds": [],
                "response": {
                    "id": "default",
                    "subtitle": "Keep going",
                    "tip": "Stay steady",
                    "tts_text": "Keep"
                }
            }
        ]
    }
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(__import__("json").dumps(rules))

    machine = load_state_machine(str(rules_path))
    scores = CoachingScore(confidence=0.7, anxiety=0.65)
    result = machine.evaluate("abc", scores)

    assert result.state == "Anxious"
    assert result.tip == "Slow down"


def test_default_rule(tmp_path):
    rules = {
        "states": [
            {
                "id": "default",
                "name": "Default",
                "default": True,
                "thresholds": [],
                "response": {
                    "id": "default",
                    "subtitle": "Keep going",
                    "tip": "Stay steady",
                    "tts_text": "Keep"
                }
            }
        ]
    }
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(__import__("json").dumps(rules))

    machine = load_state_machine(str(rules_path))
    scores = CoachingScore(confidence=0.4, anxiety=0.3)
    result = machine.evaluate("abc", scores)

    assert result.state == "Default"
    assert result.tip == "Stay steady"
