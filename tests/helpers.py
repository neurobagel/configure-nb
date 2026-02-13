from pathlib import Path


def write_test_ini_file(content: str, ini_path: Path) -> None:
    """Helper function to write test INI content to a file."""
    with open(ini_path, "w") as f:
        f.write(content.strip())
