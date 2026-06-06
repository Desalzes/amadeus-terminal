import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from config import load_settings

def test_defaults(monkeypatch):
    for k in ["AMADEUS_MODEL", "AMADEUS_CRITIC_MODEL", "AMADEUS_MAX_TURNS",
              "AMADEUS_CMD_TIMEOUT", "AMADEUS_MAX_OUTPUT", "AMADEUS_DEADLINE_SEC"]:
        monkeypatch.delenv(k, raising=False)
    s = load_settings()
    assert s.model == "anthropic/claude-opus-4-8"
    assert s.critic_model == ""
    assert s.max_turns == 40
    assert s.command_timeout == 60
    assert s.max_output_chars == 8000
    assert s.deadline_seconds == 600

def test_env_override(monkeypatch):
    monkeypatch.setenv("AMADEUS_MODEL", "openai/gpt-5.5")
    monkeypatch.setenv("AMADEUS_MAX_TURNS", "10")
    s = load_settings()
    assert s.model == "openai/gpt-5.5" and s.max_turns == 10
