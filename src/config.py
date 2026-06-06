import os
from dataclasses import dataclass


@dataclass
class Settings:
    model: str
    critic_model: str
    max_turns: int
    command_timeout: int
    max_output_chars: int


def load_settings() -> Settings:
    return Settings(
        model=os.getenv("AMADEUS_MODEL", "anthropic/claude-opus-4-8"),
        critic_model=os.getenv("AMADEUS_CRITIC_MODEL", ""),
        max_turns=int(os.getenv("AMADEUS_MAX_TURNS", "40")),
        command_timeout=int(os.getenv("AMADEUS_CMD_TIMEOUT", "60")),
        max_output_chars=int(os.getenv("AMADEUS_MAX_OUTPUT", "8000")),
    )
