from configure_nb import utility as util

from .helpers import write_test_ini_file


def test_load_ini_as_dict(tmp_ini_path):
    # Create a temporary INI file for testing
    ini_content = """
[service:first-service]
KEY1=value1
KEY2=123

[other-section]
KEYA=/path/to/something
KEYB=true
"""
    expected_loaded_ini = {
        "service:first-service": {"KEY1": "value1", "KEY2": "123"},
        "other-section": {"KEYA": "/path/to/something", "KEYB": "true"},
    }

    write_test_ini_file(ini_content, tmp_ini_path)

    loaded_ini = util.load_ini_as_dict(tmp_ini_path)

    assert loaded_ini == expected_loaded_ini
