from pathlib import Path


def test_amber_manifest_and_dockerfile_have_single_startup_command():
    manifest = Path("amber-manifest.json5").read_text()
    dockerfile = Path("Dockerfile").read_text()
    workflow = Path(".github/workflows/test-and-publish.yml").read_text()

    assert 'manifest_version: "0.2.0"' in manifest
    assert 'image: "ghcr.io/desalzes/amadeus-terminal:latest"' in manifest
    assert 'entrypoint: "uv run python src/server.py --host 0.0.0.0 --port 9009"' in manifest
    assert "ENTRYPOINT" not in dockerfile
    assert 'CMD ["uv", "run", "python", "src/server.py", "--host", "0.0.0.0", "--port", "9009"]' in dockerfile
    assert "$(echo \"${{ steps.meta.outputs.tags }}\" | head -n1) --host" not in workflow


def test_optional_config_env_values_are_guarded_for_amber():
    manifest = Path("amber-manifest.json5").read_text()

    for key in [
        "anthropic_api_key",
        "openai_api_key",
        "model",
        "critic_model",
    ]:
        assert f'when: "config.{key}"' in manifest
