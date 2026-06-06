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
