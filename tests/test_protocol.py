import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from protocol import (
    decode_inbound, encode_exec_request, encode_final,
    TaskEnvelope, ExecResultEnvelope, UnknownInbound,
)

def test_decode_task():
    text = json.dumps({"kind": "task", "protocol": "terminal-bench-shell-v1", "instruction": "fix the repo"})
    env = decode_inbound(text)
    assert isinstance(env, TaskEnvelope) and env.instruction == "fix the repo"

def test_decode_exec_result():
    text = json.dumps({"kind": "exec_result", "exit_code": 1, "stdout": "out", "stderr": "err"})
    env = decode_inbound(text)
    assert isinstance(env, ExecResultEnvelope)
    assert (env.exit_code, env.stdout, env.stderr) == (1, "out", "err")

def test_decode_non_json_is_unknown():
    env = decode_inbound("Hello")
    assert isinstance(env, UnknownInbound) and env.raw == "Hello"

def test_decode_unknown_kind_is_unknown():
    env = decode_inbound(json.dumps({"kind": "weird"}))
    assert isinstance(env, UnknownInbound)

def test_encode_exec_request_clamps_timeout():
    payload = json.loads(encode_exec_request("ls -la", timeout=9999))
    assert payload == {"kind": "exec_request", "command": "ls -la", "timeout": 300}

def test_encode_final():
    assert json.loads(encode_final("done")) == {"kind": "final", "summary": "done"}
