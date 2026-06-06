"""In-process mock green: speaks terminal-bench-shell-v1 against a real temp dir via bash."""
import json
import subprocess

from protocol import ExecResultEnvelope


def run_episode(controller, instruction: str, workdir: str, max_steps: int = 50) -> list[dict]:
    """Drive `controller` to completion; execute its commands in `workdir` via bash.

    Returns the list of envelopes the controller emitted (the transcript).
    """
    transcript = []
    out = controller.on_task(instruction)
    for _ in range(max_steps):
        env = json.loads(out)
        transcript.append(env)
        if env["kind"] == "final":
            return transcript
        proc = subprocess.run(
            ["bash", "-c", env["command"]],
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=env.get("timeout", 60),
        )
        out = controller.on_exec_result(
            ExecResultEnvelope(proc.returncode, proc.stdout, proc.stderr)
        )
    raise AssertionError("episode did not finalize within max_steps")
