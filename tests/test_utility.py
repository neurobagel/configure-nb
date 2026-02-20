import pytest
import typer

from configure_nb import utility as util


@pytest.mark.parametrize(
    "ini_content, expected_dict",
    [
        (
            """
            [service:first-service]
            KEY1=value1
            KEY2=123

            [other-section]
            KEYA=/path/to/something
            KEYB=true
            """,
            {
                "service:first-service": {"KEY1": "value1", "KEY2": "123"},
                "other-section": {
                    "KEYA": "/path/to/something",
                    "KEYB": "true",
                },
            },
        ),
        ("", {}),
    ],
)
def test_load_ini_as_dict(tmp_ini_path, ini_content, expected_dict):
    util.write_text_file(tmp_ini_path, ini_content)
    ini_dict = util.load_ini_as_dict(tmp_ini_path)

    assert ini_dict == expected_dict


@pytest.mark.parametrize(
    "ini_content, expected_err",
    [
        (
            """
            [service:graph]
            LOCAL_GRAPH_DATA=/data/test_data

            [service:graph]
            LOCAL_GRAPH_DATA=/test_data
            """,
            ["duplicate section", "service:graph"],
        ),
        (
            """
            [service:graph]
            LOCAL_GRAPH_DATA=/data/test_data
            LOCAL_GRAPH_DATA=/test_data
            """,
            ["duplicate variable", "LOCAL_GRAPH_DATA", "service:graph"],
        ),
    ],
)
def test_duplicate_section_or_option_in_ini_raises_err(
    tmp_ini_path, propagate_errors, caplog, ini_content, expected_err
):
    util.write_text_file(tmp_ini_path, ini_content)

    with pytest.raises(typer.Exit):
        util.load_ini_as_dict(tmp_ini_path)

    assert len(caplog.records) == 1
    for part in expected_err:
        assert part in caplog.text
