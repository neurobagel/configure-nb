from pathlib import Path

import pytest
from dotenv import dotenv_values

from configure_nb.cli import configure_nb
from configure_nb.utility import write_text_file


@pytest.fixture()
def example_data_path():
    return Path(__file__).parent / "data"


@pytest.fixture()
def expected_quickstart_env_vars():
    """
    Return all environment variables expected to be defined in the .env file
    for a test deployment configuration.
    """
    return [
        # Compose
        "COMPOSE_PROJECT_NAME",
        # Graph
        "NB_GRAPH_USERNAME",
        "NB_GRAPH_SECRETS_PATH",
        "NB_GRAPH_DB",
        "NB_GRAPH_MEMORY",
        "LOCAL_GRAPH_DATA",
        "NB_GRAPH_PORT_HOST",
        # Node API
        "NB_RETURN_AGG",
        "NB_MIN_CELL_SIZE",
        "NB_NAPI_TAG",
        "NB_NAPI_PORT_HOST",
        "NB_NAPI_BASE_PATH",
        "NB_NAPI_DOMAIN",
        "NB_CONFIG",
        # Federation API
        "NB_FAPI_TAG",
        "NB_FAPI_PORT_HOST",
        "NB_FEDERATE_REMOTE_PUBLIC_NODES",
        "NB_FAPI_BASE_PATH",
        "NB_FAPI_DOMAIN",
        # Query tool
        "NB_QUERY_TAG",
        "NB_QUERY_PORT_HOST",
        "NB_API_QUERY_URL",
        "NB_QUERY_APP_BASE_PATH",
        "NB_QUERY_DOMAIN",
        # Experimental
        "NB_ENABLE_AUTH",
    ]


def test_quickstart_dotenv_created_when_ini_missing(
    runner, tmp_path, tmp_dotenv_path, expected_quickstart_env_vars, caplog
):
    runner.invoke(
        configure_nb,
        [
            "--output-dir",
            tmp_path,
        ],
    )

    env = dotenv_values(tmp_dotenv_path)

    assert "No configuration file provided" in caplog.text
    assert "Defaulting to a test deployment configuration" in caplog.text
    assert set(env.keys()) == set(expected_quickstart_env_vars)
    assert env["COMPOSE_PROJECT_NAME"] == "neurobagel_quickstart"


def test_quickstart_dotenv_created_when_profile_not_specified(
    runner,
    tmp_ini_path,
    tmp_path,
    tmp_dotenv_path,
    expected_quickstart_env_vars,
    caplog,
):
    ini_content = """
[service:graph]
LOCAL_GRAPH_DATA=/data/my_first_jsonlds
"""
    write_text_file(tmp_ini_path, ini_content)

    runner.invoke(
        configure_nb,
        [
            "--config-file",
            tmp_ini_path,
            "--output-dir",
            tmp_path,
        ],
    )

    env = dotenv_values(tmp_dotenv_path)

    assert "Defaulting to a test deployment configuration" in caplog.text
    assert set(env.keys()) == set(expected_quickstart_env_vars)
    assert env["COMPOSE_PROJECT_NAME"] == "neurobagel_quickstart"


def test_quickstart_dotenv_created_when_ini_sections_empty(
    runner,
    tmp_ini_path,
    tmp_path,
    tmp_dotenv_path,
    expected_quickstart_env_vars,
    caplog,
):
    """
    Test that when an INI file contains valid sections but has no variables defined (i.e., sections are empty),
    a .env with all expected variables for a test deployment is created.
    """
    ini_content = """
[service:node-api]

[service:graph]

"""

    write_text_file(tmp_ini_path, ini_content)

    runner.invoke(
        configure_nb,
        [
            "--config-file",
            tmp_ini_path,
            "--output-dir",
            tmp_path,
        ],
    )

    env = dotenv_values(tmp_dotenv_path)

    assert "Defaulting to a test deployment configuration" in caplog.text
    assert set(env.keys()) == set(expected_quickstart_env_vars)
    assert env["COMPOSE_PROJECT_NAME"] == "neurobagel_quickstart"


def test_invalid_profile_raises_error(
    runner, tmp_ini_path, tmp_path, tmp_dotenv_path, caplog, propagate_errors
):
    ini_content = """
[service:node-api]
NB_RETURN_AGG=false

[compose]
COMPOSE_PROFILES=not_a_profile
"""

    write_text_file(tmp_ini_path, ini_content)

    result = runner.invoke(
        configure_nb,
        [
            "--config-file",
            tmp_ini_path,
            "--output-dir",
            tmp_path,
        ],
    )

    errors = list(caplog.records)

    assert result.exit_code != 0
    assert not tmp_dotenv_path.exists()
    assert len(errors) == 1
    assert "Invalid COMPOSE_PROFILES value: not_a_profile" in errors[0].message


def test_all_node_vars_defined_when_node_profile_specified(
    runner, tmp_ini_path, tmp_path, tmp_dotenv_path, caplog
):
    ini_content = """
[service:node-api]
NB_RETURN_AGG=true
NB_MIN_CELL_SIZE=5
NB_NAPI_DOMAIN=node.testdomain.org

[service:graph]
NB_GRAPH_USERNAME=testuser
LOCAL_GRAPH_DATA=/data/test_data

[compose]
COMPOSE_PROFILES=node
"""
    expected_env = {
        # --- Node API --- #
        # Explicitly set
        "NB_RETURN_AGG": "True",
        "NB_MIN_CELL_SIZE": "5",
        "NB_NAPI_DOMAIN": "node.testdomain.org",
        # Defaults
        "NB_NAPI_BASE_PATH": "",
        "NB_NAPI_TAG": "latest",
        "NB_NAPI_PORT_HOST": "8000",
        "NB_CONFIG": "Neurobagel",
        # --- Graph --- #
        # Explicitly set
        "NB_GRAPH_USERNAME": "testuser",
        "LOCAL_GRAPH_DATA": "/data/test_data",
        # Defaults
        "NB_GRAPH_DB": "repositories/my_db",
        "NB_GRAPH_SECRETS_PATH": "./secrets",
        "NB_GRAPH_PORT_HOST": "7200",
        "NB_GRAPH_MEMORY": "2G",
        # --- Experimental --- #
        # Defaults
        "NB_ENABLE_AUTH": "False",
        # --- Compose --- #
        # Explicitly set
        "COMPOSE_PROFILES": "node",
        # Defaults
        "COMPOSE_PROJECT_NAME": "neurobagel_node",
    }

    write_text_file(tmp_ini_path, ini_content)

    runner.invoke(
        configure_nb,
        [
            "--config-file",
            tmp_ini_path,
            "--output-dir",
            tmp_path,
        ],
    )

    # Use dict to remove ordering from dotenv values for less brittle assertion
    env = dict(dotenv_values(tmp_dotenv_path))
    warnings = [
        record for record in caplog.records if record.levelname == "WARNING"
    ]

    assert env == expected_env
    assert len(warnings) == 0
    assert "configuration: node" in caplog.text


def test_all_portal_vars_defined_when_portal_profile_specified(
    runner, tmp_ini_path, tmp_path, tmp_dotenv_path, caplog
):
    ini_content = """
[service:federation-api]
NB_FAPI_DOMAIN=myinstitute.org
NB_FAPI_BASE_PATH=/federate

[service:query]
NB_QUERY_DOMAIN=myinstitute.org

[compose]
COMPOSE_PROFILES=portal

[node:1]
NAME=Local node
API_URL=https://myinstitute.org/node
"""

    expected_env = {
        # --- Federation API --- #
        # Explicitly set
        "NB_FAPI_DOMAIN": "myinstitute.org",
        "NB_FAPI_BASE_PATH": "/federate",
        # Defaults
        "NB_FAPI_TAG": "latest",
        "NB_FAPI_PORT_HOST": "8080",
        "NB_FEDERATE_REMOTE_PUBLIC_NODES": "True",
        # --- Query tool --- #
        # Explicitly set
        "NB_QUERY_DOMAIN": "myinstitute.org",
        # Defaults
        "NB_QUERY_APP_BASE_PATH": "/",
        "NB_QUERY_TAG": "latest",
        "NB_QUERY_PORT_HOST": "3000",
        "NB_API_QUERY_URL": "http://localhost:8080",
        # --- Experimental --- #
        # Defaults
        "NB_ENABLE_AUTH": "False",
        # --- Compose --- #
        # Explicitly set
        "COMPOSE_PROFILES": "portal",
        # Defaults
        "COMPOSE_PROJECT_NAME": "neurobagel_portal",
    }

    write_text_file(tmp_ini_path, ini_content)

    runner.invoke(
        configure_nb,
        [
            "--config-file",
            tmp_ini_path,
            "--output-dir",
            tmp_path,
        ],
    )

    env = dict(dotenv_values(tmp_dotenv_path))
    warnings = [
        record for record in caplog.records if record.levelname == "WARNING"
    ]

    assert env == expected_env
    assert len(warnings) == 0
    assert "configuration: portal" in caplog.text


@pytest.mark.parametrize(
    "ini_content, expected_warning",
    [
        (
            """
            [service:node-api]
            NB_NAPI_DOMAIN=node.testdomain.org

            [wrong-section-name]
            LOCAL_GRAPH_DATA=/data/test_data

            [compose]
            COMPOSE_PROFILES=node
            """,
            [
                "sections that are not recognized or used for the Node deployment profile",
                "wrong-section-name",
            ],
        ),
        (
            """
            [service:node-api]
            NB_NAPI_DOMAIN=node.testdomain.org

            [service:federation-api]
            NB_FAPI_DOMAIN=federate.testdomain.org

            [compose]
            COMPOSE_PROFILES=node
            """,
            [
                "sections that are not recognized or used for the Node deployment profile",
                "service:federation-api",
            ],
        ),
    ],
)
def test_unrecognized_ini_section_ignored_with_warning(
    runner,
    tmp_ini_path,
    tmp_path,
    tmp_dotenv_path,
    caplog,
    propagate_warnings,
    ini_content,
    expected_warning,
):
    write_text_file(tmp_ini_path, ini_content)

    result = runner.invoke(
        configure_nb,
        [
            "--config-file",
            tmp_ini_path,
            "--output-dir",
            tmp_path,
        ],
    )

    warnings = list(caplog.records)

    assert result.exit_code == 0
    assert tmp_dotenv_path.exists()
    assert len(warnings) == 1
    for part in expected_warning:
        assert part in warnings[0].message


@pytest.mark.parametrize(
    "ini_content, expected_warnings",
    [
        (
            """
            [service:node-api]
            NB_NAPI_DOMAIN=node.testdomain.org
            EXTRA1=value1

            [service:graph]
            EXTRA2=value2

            [compose]
            COMPOSE_PROFILES=node
            """,
            [
                [
                    "[service:node-api] contains variables that are not recognized",
                    "EXTRA1",
                ],
                [
                    "[service:graph] contains variables that are not recognized",
                    "EXTRA2",
                ],
            ],
        ),
        (
            """
            [service:node-api]
            NB_NAPI_DOMAIN=node.testdomain.org
            LOCAL_GRAPH_DATA=/data/test_data

            [compose]
            COMPOSE_PROFILES=node
            """,
            [
                [
                    "[service:node-api] contains variables that are not recognized",
                    "LOCAL_GRAPH_DATA",
                ],
            ],
        ),
    ],
)
def test_unrecognized_variables_ignored_with_warning(
    runner,
    tmp_ini_path,
    tmp_path,
    tmp_dotenv_path,
    caplog,
    propagate_warnings,
    ini_content,
    expected_warnings,
):
    write_text_file(tmp_ini_path, ini_content)

    result = runner.invoke(
        configure_nb,
        [
            "--config-file",
            tmp_ini_path,
            "--output-dir",
            tmp_path,
        ],
    )

    warnings = list(caplog.records)

    assert result.exit_code == 0
    assert tmp_dotenv_path.exists()
    assert len(warnings) == len(expected_warnings)

    for expected_warning in expected_warnings:
        assert any(
            all(part in warning.message for part in expected_warning)
            for warning in warnings
        ), f"Expected warning not fully found: {expected_warning}"


def test_invalid_variable_value_raises_error(
    runner, tmp_ini_path, tmp_path, tmp_dotenv_path, caplog, propagate_errors
):
    ini_content = """
[service:node-api]
NB_NAPI_DOMAIN=https://testdomain.org
NB_NAPI_BASE_PATH=node

[compose]
COMPOSE_PROFILES=node
"""
    expected_warning = [
        "problems with configuration values",
        "NB_NAPI_BASE_PATH",
        "must start with a leading slash",
        "NB_NAPI_DOMAIN",
        "must not include a URL scheme",
    ]

    write_text_file(tmp_ini_path, ini_content)

    result = runner.invoke(
        configure_nb,
        [
            "--config-file",
            tmp_ini_path,
            "--output-dir",
            tmp_path,
        ],
    )

    errors = list(caplog.records)

    assert result.exit_code != 0
    assert not tmp_dotenv_path.exists()
    assert len(errors) == 1

    for part in expected_warning:
        assert part in errors[0].message


def test_created_dotenv_matches_expected_output(
    runner, tmp_path, tmp_dotenv_path, caplog, example_data_path
):
    """Smoke test that the .env created from a sample INI file matches the expected output in format and values."""
    ini_file = example_data_path / "1_valid_node_config.ini"
    expected_env_file = example_data_path / "1_valid_node.env"

    result = runner.invoke(
        configure_nb,
        [
            "--config-file",
            ini_file,
            "--output-dir",
            tmp_path,
        ],
    )

    assert result.exit_code == 0
    assert "Loading configuration from file" in caplog.text
    assert tmp_dotenv_path.exists()
    assert tmp_dotenv_path.read_text() == expected_env_file.read_text()
