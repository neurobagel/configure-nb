from pathlib import Path
from typing import Annotated, Type

import pydantic
import typer
from pydantic import BaseModel

from . import utility as util
from .logger import VerbosityLevel, configure_logger, log_error, logger
from .models import COMPOSE_PROFILE_TO_CLASS_MAP, TestStack

configure_nb = typer.Typer()


@configure_nb.command()
def main(
    config_file: Annotated[
        Path,
        typer.Option(
            "--config-file",
            "-c",
            help="Path to a configuration file (.ini).",
            exists=False,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ] = Path("nb_config.ini"),
    output_file: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Path to the output env file.",
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ] = Path(".env"),
    verbosity: Annotated[
        VerbosityLevel,
        typer.Option(
            "--verbosity",
            "-v",
            callback=configure_logger,
            help="Set the logging verbosity level. 0 = show errors only; 1 = show errors, warnings, and informational messages; 2 = show all logs, including debug messages.",
        ),
    ] = VerbosityLevel.INFO,
    # TODO: Add option to explicitly allow overwriting?
):
    """
    Generate a valid .env file for Neurobagel deployment configuration.
    """
    if config_file.exists():
        logger.info(f"Loading configuration from file: {config_file}")
        ini_contents = util.load_ini_as_dict(config_file)
    else:
        logger.info(
            "No configuration file provided. Using default values for all settings."
        )
        ini_contents = {}

    compose_profile = ini_contents.get("compose", {}).get("COMPOSE_PROFILES")
    try:
        if not compose_profile:
            logger.info(
                "The COMPOSE_PROFILES variable was not set. Defaulting to a test deployment configuration."
            )
            config = TestStack.model_validate(ini_contents)
        else:
            config_class: Type[BaseModel] | None = (
                COMPOSE_PROFILE_TO_CLASS_MAP.get(compose_profile)
            )
            if not config_class:
                log_error(
                    logger,
                    f"Unrecognized COMPOSE_PROFILES value: {compose_profile}. "
                    f"Expected one of {list(COMPOSE_PROFILE_TO_CLASS_MAP.keys())}.",
                )
            logger.info(f"Deployment configuration: {compose_profile}")
            config = config_class.model_validate(ini_contents)
    except pydantic.ValidationError as err:
        if config_file.exists():
            # TODO: Can customize validation error from Pydantic to be more user friendly
            err_message = f"There are problems with configuration values in {config_file.name}. Please check your configuration."
        else:
            err_message = (
                "Failed to apply default configuration values. "
                "This is unexpected - please report the issue at https://github.com/neurobagel/configure-nb/issues."
            )
        log_error(logger, f"{err_message}\nValidation details:\n {err}")

    util.write_config_to_env_file(config, output_file)
    logger.info(
        f"Environment variable configuration successfully written to: {output_file}"
    )
