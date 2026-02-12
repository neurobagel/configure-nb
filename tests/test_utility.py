from configure_nb import utility as util


def test_load_ini_as_dict(tmp_path):
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

    ini_path = tmp_path / "test_config.ini"
    with open(ini_path, "w") as f:
        f.write(ini_content.strip())

    loaded_ini = util.load_ini_as_dict(ini_path)

    assert loaded_ini == expected_loaded_ini
