from __future__ import annotations
import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from protocol import ExecResultEnvelope, encode_exec_request, encode_final

SYSTEM_PROMPT = (
    "You are Amadeus, an elite autonomous terminal engineer competing on Terminal-Bench. "
    "You control a real Linux shell ONE command per turn; after each command you receive its "
    "exit_code, stdout, and stderr. Work methodically: (1) EXPLORE the environment and read the "
    "relevant files before changing anything; (2) form a short PLAN; (3) EXECUTE one command at a "
    "time; (4) VERIFY by running the project's own tests/build or checking expected files/state; "
    "(5) only then finish. Prefer non-interactive commands; never run commands that block on input. "
    "Your work is graded by a hidden test against the final environment state, so make the state "
    "correct — do not just describe a solution."
)

DecideFn = Callable[..., dict[str, Any]]


@dataclass
class Controller:
    model: str
    decide: DecideFn
    max_turns: int = 40
    command_timeout: int = 60
    max_output_chars: int = 8000
    messages: list[dict[str, Any]] = field(default_factory=list)
    turns: int = 0
    deadline_seconds: float | None = None
    critic_model: str = ""
    max_verify_interventions: int = 2
    _start: float = field(default=0.0, repr=False)
    _verify_used: int = field(default=0, repr=False)

    def on_task(self, instruction: str) -> str:
        self._start = time.monotonic()
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"TASK:\n{instruction}\n\nBegin by exploring."},
        ]
        return self._next_action()

    def on_exec_result(self, r: ExecResultEnvelope) -> str:
        obs = (f"exit_code={r.exit_code}\n"
               f"stdout:\n{self._truncate(r.stdout)}\n"
               f"stderr:\n{self._truncate(r.stderr)}")
        self.messages.append({"role": "user", "content": obs})
        return self._next_action()

    def _next_action(self) -> str:
        if self.turns >= self.max_turns:
            return encode_final("Turn budget exhausted.")
        if self.deadline_seconds is not None and (time.monotonic() - self._start) >= self.deadline_seconds:
            return encode_final("Wall-clock budget exhausted.")
        self.turns += 1
        action = self.decide(self.messages, model=self.model)
        self.messages.append({"role": "assistant", "content": json.dumps(action)})
        if action.get("action") == "run":
            command = str(action.get("command", "")).strip()
            if not command:
                return encode_final("No command produced.")
            try:
                timeout = int(action.get("timeout", self.command_timeout))
            except (TypeError, ValueError):
                timeout = self.command_timeout
            return encode_exec_request(command, timeout=timeout)
        # action == "final": run a verify/critic gate before actually finishing.
        if self._verify_used < self.max_verify_interventions:
            if self.deadline_seconds is not None and (time.monotonic() - self._start) >= self.deadline_seconds:
                return encode_final(str(action.get("summary", "")))
            self._verify_used += 1
            self.messages.append({
                "role": "user",
                "content": (
                    "Before finishing, VERIFY the task is truly complete: run the project's "
                    "tests/build or inspect the expected files/state. If anything is unverified or "
                    "wrong, return a run action to check or fix it; only return final once you have "
                    "positive evidence."
                ),
            })
            check = self.decide(self.messages, model=self.critic_model or self.model)
            self.messages.append({"role": "assistant", "content": json.dumps(check)})
            if check.get("action") == "run":
                command = str(check.get("command", "")).strip()
                if command:
                    try:
                        timeout = int(check.get("timeout", self.command_timeout))
                    except (TypeError, ValueError):
                        timeout = self.command_timeout
                    return encode_exec_request(command, timeout=timeout)
            return encode_final(str(check.get("summary", action.get("summary", ""))))
        return encode_final(str(action.get("summary", "")))

    def _truncate(self, text: str) -> str:
        if len(text) <= self.max_output_chars:
            return text
        head = self.max_output_chars // 2
        return text[:head] + "\n...[truncated]...\n" + text[-head:]
