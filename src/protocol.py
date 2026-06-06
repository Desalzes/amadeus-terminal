"""terminal-bench-shell-v1 protocol envelopes. Pure functions, no I/O."""
from __future__ import annotations
import json
from dataclasses import dataclass

PROTOCOL = "terminal-bench-shell-v1"


@dataclass
class TaskEnvelope:
    instruction: str


@dataclass
class ExecResultEnvelope:
    exit_code: int
    stdout: str
    stderr: str


@dataclass
class UnknownInbound:
    raw: str


def decode_inbound(text: str) -> TaskEnvelope | ExecResultEnvelope | UnknownInbound:
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return UnknownInbound(raw=text)
    if not isinstance(payload, dict):
        return UnknownInbound(raw=text)
    kind = payload.get("kind")
    if kind == "task":
        return TaskEnvelope(instruction=str(payload.get("instruction", "")))
    if kind == "exec_result":
        return ExecResultEnvelope(
            exit_code=int(payload.get("exit_code", -1)),
            stdout=str(payload.get("stdout", "")),
            stderr=str(payload.get("stderr", "")),
        )
    return UnknownInbound(raw=text)


def encode_exec_request(command: str, timeout: int = 30) -> str:
    timeout = max(1, min(int(timeout), 300))
    return json.dumps({"kind": "exec_request", "command": command, "timeout": timeout})


def encode_final(summary: str = "") -> str:
    return json.dumps({"kind": "final", "summary": summary})
