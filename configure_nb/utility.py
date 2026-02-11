import configparser
from pathlib import Path

from .logger import log_error, logger
from .models import ConfigFile


def load_ini(file_path: Path) -> dict:
    config = configparser.ConfigParser()
    # Convert keys to uppercase to match the expected environment variable format
    # We need to silence an erroneous mypy error here (see https://github.com/python/mypy/issues/5062)
    config.optionxform = lambda option: option.upper()  # type: ignore

    try:
        config.read(file_path)
    except configparser.Error as err:
        log_error(logger, f"Error reading INI file: {err}")

    if not config.sections():
        return {}

    # TODO: Check if there are unrecognized section names
    return {section: dict(config[section]) for section in config.sections()}


# def flatten_config_to_dict(config: ConfigFile) -> dict:
#     flat_config = {}
#     for section_vars in config.model_dump(by_alias=True).values():
#         # if isinstance(section_vars, dict):
#         flat_config.update(section_vars)
#     return flat_config


def write_config_to_env_file(config: ConfigFile, out_file: Path) -> None:
    with open(out_file, "w", encoding="utf-8") as env_file:
        for section_num, section_vars in enumerate(
            # exclude_none useful for experimental variables that we want to omit from the .env file if unset
            config.model_dump(by_alias=True, exclude_none=True).values()
        ):
            if section_num > 0:
                # Add a newline after each section for readability
                # TODO: Can add section headers as comments
                env_file.write("\n")
            for key, value in section_vars.items():
                env_file.write(f"{key}={value}\n")
