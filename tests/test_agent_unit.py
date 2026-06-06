import asyncio, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from a2a.types import Message, Part, TextPart, Role
from agent import Agent

class FakeUpdater:
    def __init__(self): self.artifacts = []
    async def add_artifact(self, parts, name=None): self.artifacts.append((parts, name))
    async def update_status(self, *a, **k): pass

def _msg(text):
    return Message(kind="message", role=Role.user, parts=[Part(TextPart(text=text))], message_id="x")

def _artifact_text(updater):
    return updater.artifacts[-1][0][0].root.text

def test_agent_handles_task_then_result():
    actions = iter([{"action": "run", "command": "ls", "timeout": 5}, {"action": "final", "summary": "ok"}])
    agent = Agent()
    agent.controller.decide = lambda *a, **k: next(actions)
    agent.controller.max_verify_interventions = 0
    u1 = FakeUpdater()
    asyncio.run(agent.run(_msg(json.dumps({"kind": "task", "instruction": "do"})), u1))
    assert json.loads(_artifact_text(u1))["kind"] == "exec_request"
    u2 = FakeUpdater()
    asyncio.run(agent.run(_msg(json.dumps({"kind": "exec_result", "exit_code": 0, "stdout": "", "stderr": ""})), u2))
    assert json.loads(_artifact_text(u2))["kind"] == "final"

def test_agent_handles_non_protocol_input():
    agent = Agent()
    u = FakeUpdater()
    asyncio.run(agent.run(_msg("Hello"), u))
    assert _artifact_text(u)  # non-empty response, did not raise
