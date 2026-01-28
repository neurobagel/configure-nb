from pathlib import Path

import pytest
from typer.testing import CliRunner

from configure_nb.cli import configure_nb


@pytest.fixture(scope="session")
def runner():
    return CliRunner()


@pytest.fixture()
def example_data_path():
    return Path(__file__).parent / "data"


def test_configure_nb_runs_successfully(runner):
    result = runner.invoke(configure_nb)
    assert result.exit_code == 0
