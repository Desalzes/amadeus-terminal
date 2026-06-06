"""Provider-agnostic LLM via litellm; returns one structured action dict."""
from __future__ import annotations
import json
from typing import Any

import litellm

ACTION_HINT = (
    'Respond with ONE JSON object and nothing else. '
    'To run a shell command: {"action":"run","command":"<bash>","timeout":<int seconds 1-300>,"thought":"<brief why>"}. '
    'When the task is fully done AND you have verified it: {"action":"final","summary":"<what you did>"}.'
)


def decide(messages: list[dict[str, Any]], *, model: str, temperature: float = 0.0) -> dict[str, Any]:
    """Call `model` and parse a single action dict. Re-prompts once on bad output."""
    convo = list(messages)
    for _ in range(2):
        resp = litellm.completion(
            model=model, messages=convo, temperature=temperature,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "{}"
        try:
            action = json.loads(content)
        except json.JSONDecodeError:
            convo = convo + [{"role": "user", "content": "Your reply was not valid JSON. " + ACTION_HINT}]
            continue
        if isinstance(action, dict) and action.get("action") in {"run", "final"}:
            return action
        convo = convo + [{"role": "user", "content": "Invalid action. " + ACTION_HINT}]
    return {"action": "final", "summary": "Unable to produce a valid action."}
