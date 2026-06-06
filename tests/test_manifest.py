from pathlib import Path


def test_amber_manifest_uses_image_entrypoint():
    manifest = Path("amber-manifest.json5").read_text()

    assert 'image: "ghcr.io/desalzes/amadeus-terminal:latest"' in manifest
    assert "entrypoint:" not in manifest
