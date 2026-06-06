from a2a.server.tasks import TaskUpdater
from a2a.types import Message, Part, TextPart
from a2a.utils import get_message_text

from protocol import TaskEnvelope, ExecResultEnvelope, decode_inbound
from controller import Controller
from llm import decide
from config import load_settings


class Agent:
    """One instance per A2A conversation (keyed by context_id in the Executor)."""

    def __init__(self) -> None:
        s = load_settings()
        self.controller = Controller(
            model=s.model, decide=decide, max_turns=s.max_turns,
            command_timeout=s.command_timeout, max_output_chars=s.max_output_chars,
            deadline_seconds=s.deadline_seconds, critic_model=s.critic_model,
        )

    async def run(self, message: Message, updater: TaskUpdater) -> None:
        inbound = decode_inbound(get_message_text(message))
        if isinstance(inbound, TaskEnvelope):
            outbound = self.controller.on_task(inbound.instruction)
        elif isinstance(inbound, ExecResultEnvelope):
            outbound = self.controller.on_exec_result(inbound)
        else:
            outbound = "Amadeus terminal agent ready."  # non-protocol (e.g. conformance "Hello")
        await updater.add_artifact(parts=[Part(root=TextPart(text=outbound))], name="Amadeus")
