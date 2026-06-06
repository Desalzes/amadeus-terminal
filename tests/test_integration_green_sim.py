import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from controller import Controller
from green_sim import run_episode

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="bash not on PATH")


class ScriptLLM:
    def __init__(self, actions):
        self.actions = list(actions)

    def __call__(self, messages, *, model, **kw):
        return self.actions.pop(0)


def test_agent_creates_file(tmp_path):
    # Solve "create hello.txt containing hi": write the file, verify by cat, then finish.
    actions = [
        {"action": "run", "command": "printf hi > hello.txt"},
        {"action": "run", "command": "cat hello.txt"},
        {"action": "final", "summary": "created hello.txt"},
    ]
    c = Controller(model="m", decide=ScriptLLM(actions))
    transcript = run_episode(c, "create hello.txt containing hi", str(tmp_path))
    assert transcript[-1]["kind"] == "final"
    assert (tmp_path / "hello.txt").read_text() == "hi"
