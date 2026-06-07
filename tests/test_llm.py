import sys, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import llm

def _fake_completion(content):
    def _fn(**kwargs):
        msg = types.SimpleNamespace(content=content)
        choice = types.SimpleNamespace(message=msg)
        return types.SimpleNamespace(choices=[choice])
    return _fn

def test_decide_returns_run(monkeypatch):
    monkeypatch.setattr(llm.litellm, "completion",
                        _fake_completion('{"action":"run","command":"ls","timeout":30}'))
    action = llm.decide([{"role": "user", "content": "go"}], model="x")
    assert action["action"] == "run" and action["command"] == "ls"

def test_decide_returns_final(monkeypatch):
    monkeypatch.setattr(llm.litellm, "completion",
                        _fake_completion('{"action":"final","summary":"done"}'))
    assert llm.decide([], model="x")["action"] == "final"

def test_decide_falls_back_on_garbage(monkeypatch):
    monkeypatch.setattr(llm.litellm, "completion", _fake_completion("not json"))
    action = llm.decide([], model="x")
    assert action == {"action": "final", "summary": "Unable to produce a valid action."}


def test_anthropic_models_omit_temperature(monkeypatch):
    seen = []

    def fake_completion(**kwargs):
        seen.append(kwargs)
        msg = types.SimpleNamespace(content='{"action":"final","summary":"done"}')
        choice = types.SimpleNamespace(message=msg)
        return types.SimpleNamespace(choices=[choice])

    monkeypatch.setattr(llm.litellm, "completion", fake_completion)

    llm.decide([], model="anthropic/claude-opus-4-8", temperature=0.0)

    assert "temperature" not in seen[0]


def test_retries_without_temperature_when_provider_rejects_it(monkeypatch):
    seen = []

    def fake_completion(**kwargs):
        seen.append(kwargs)
        if len(seen) == 1:
            raise RuntimeError("`temperature` is deprecated for this model.")
        msg = types.SimpleNamespace(content='{"action":"final","summary":"done"}')
        choice = types.SimpleNamespace(message=msg)
        return types.SimpleNamespace(choices=[choice])

    monkeypatch.setattr(llm.litellm, "completion", fake_completion)

    action = llm.decide([], model="openai/new-model", temperature=0.0)

    assert action["action"] == "final"
    assert "temperature" in seen[0]
    assert "temperature" not in seen[1]
