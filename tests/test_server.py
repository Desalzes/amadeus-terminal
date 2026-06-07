import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from server import _default_card_url


def test_default_card_url_does_not_advertise_wildcard_host():
    assert _default_card_url("0.0.0.0", 9009) == "http://127.0.0.1:9009/"


def test_default_card_url_preserves_specific_host():
    assert _default_card_url("localhost", 9009) == "http://localhost:9009/"
