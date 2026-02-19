import pytest

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
