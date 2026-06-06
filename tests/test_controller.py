import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from controller import Controller
from protocol import ExecResultEnvelope

class StubLLM:
    """Returns scripted actions in order; records the messages it saw."""
    def __init__(self, actions): self.actions = list(actions); self.calls = []
    def __call__(self, messages, *, model, **kw):
        self.calls.append(list(messages))
        return self.actions.pop(0)

def make(actions, **kw):
    stub = StubLLM(actions)
    return Controller(model="m", decide=stub, **kw), stub

def test_task_then_run():
    c, _ = make([{"action": "run", "command": "ls", "timeout": 5}])
    out = json.loads(c.on_task("do it"))
    assert out == {"kind": "exec_request", "command": "ls", "timeout": 5}

def test_result_then_final():
    c, _ = make([{"action": "run", "command": "ls"}, {"action": "final", "summary": "ok"}], max_verify_interventions=0)
    c.on_task("do it")
    out = json.loads(c.on_exec_result(ExecResultEnvelope(0, "file.txt", "")))
    assert out == {"kind": "final", "summary": "ok"}

def test_turn_cap_forces_final():
    actions = [{"action": "run", "command": "x"}] * 5
    c, _ = make(actions, max_turns=2)
    assert json.loads(c.on_task("t"))["kind"] == "exec_request"
    assert json.loads(c.on_exec_result(ExecResultEnvelope(0, "", "")))["kind"] == "exec_request"
    assert json.loads(c.on_exec_result(ExecResultEnvelope(0, "", "")))["kind"] == "final"

def test_output_truncation():
    c, stub = make([{"action": "run", "command": "a"}, {"action": "run", "command": "b"}], max_output_chars=20)
    c.on_task("t")
    c.on_exec_result(ExecResultEnvelope(0, "X" * 1000, ""))
    assert "[truncated]" in stub.calls[1][-1]["content"]

def test_empty_command_finalizes():
    c, _ = make([{"action": "run", "command": "   "}])
    assert json.loads(c.on_task("t"))["kind"] == "final"

def test_non_numeric_timeout_uses_default():
    c, _ = make([{"action": "run", "command": "ls", "timeout": "fast"}], command_timeout=60)
    out = json.loads(c.on_task("t"))
    assert out["kind"] == "exec_request" and out["timeout"] == 60

def test_wall_clock_self_limit():
    c, _ = make([{"action": "run", "command": "x"}] * 5, deadline_seconds=0)
    out = json.loads(c.on_task("t"))
    assert out["kind"] == "final"

def test_plan_message_present():
    from controller import SYSTEM_PROMPT
    assert "PLAN" in SYSTEM_PROMPT and "VERIFY" in SYSTEM_PROMPT

def test_verify_gate_runs_check_before_final():
    actions = [
        {"action": "final", "summary": "done"},
        {"action": "run", "command": "pytest -q"},
        {"action": "final", "summary": "verified"},
    ]
    c, _ = make(actions, max_verify_interventions=1)
    out = json.loads(c.on_task("t"))
    assert out == {"kind": "exec_request", "command": "pytest -q", "timeout": 60}
    out2 = json.loads(c.on_exec_result(ExecResultEnvelope(0, "1 passed", "")))
    assert out2["kind"] == "final"

def test_verify_gate_cap():
    actions = [
        {"action": "final", "summary": "a"},
        {"action": "run", "command": "echo check"},
        {"action": "final", "summary": "b"},
    ]
    c, _ = make(actions, max_verify_interventions=1)
    c.on_task("t")  # gate fires once -> exec_request
    out = json.loads(c.on_exec_result(ExecResultEnvelope(0, "", "")))
    assert out == {"kind": "final", "summary": "b"}

def test_critic_uses_critic_model():
    seen = []
    def decide(messages, *, model, **kw):
        seen.append(model)
        return {"action": "final", "summary": "x"}
    c = Controller(model="main/m", critic_model="critic/c", decide=decide, max_verify_interventions=1)
    c.on_task("t")
    assert "main/m" in seen and "critic/c" in seen

def test_verify_gate_non_numeric_timeout_uses_default():
    actions = [
        {"action": "final", "summary": "x"},
        {"action": "run", "command": "ls", "timeout": "fast"},
    ]
    c, _ = make(actions, max_verify_interventions=1, command_timeout=60)
    out = json.loads(c.on_task("t"))
    assert out == {"kind": "exec_request", "command": "ls", "timeout": 60}

def test_verify_gate_empty_critic_command_finalizes():
    actions = [
        {"action": "final", "summary": "orig"},
        {"action": "run", "command": "   "},
    ]
    c, _ = make(actions, max_verify_interventions=1)
    out = json.loads(c.on_task("t"))
    assert out["kind"] == "final"
