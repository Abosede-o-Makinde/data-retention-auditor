from src import __version__


def test_version_is_set() -> None:
    assert __version__ == "1.0.0"
