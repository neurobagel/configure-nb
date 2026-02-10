from pathlib import Path
from typing import Annotated

import pydantic
import typer

from . import utility as util
from .logger import VerbosityLevel, configure_logger, log_error, logger
from .models import ConfigFile

configure_nb = typer.Typer()


@configure_nb.command()
def main(
    config_file: Annotated[
        Path | None,
        typer.Option(
            "--config-file",
            "-c",
            help="Path to a configuration file (.ini).",
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ] = None,
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
    # TODO: Add overwrite option?
    verbosity: Annotated[
        VerbosityLevel,
        typer.Option(
            "--verbosity",
            "-v",
            callback=configure_logger,
            help="Set the logging verbosity level. 0 = show errors only; 1 = show errors, warnings, and informational messages; 2 = show all logs, including debug messages.",
        ),
    ] = VerbosityLevel.INFO,
):
    """
    Generate a valid .env file for Neurobagel deployment configuration.
    """
    if config_file:
        logger.info(f"Loading configuration from file: {config_file}")
        ini_contents = util.load_ini(config_file)
    else:
        logger.info(
            "No configuration file provided. Using default values for all settings."
        )
        ini_contents = {}

    try:
        config = ConfigFile.model_validate(ini_contents)
    except pydantic.ValidationError as err:
        if config_file:
            err_message = f"{config_file.name} is not a valid Neurobagel configuration file."
        else:
            err_message = (
                "Failed to apply default configuration values. "
                "This is unexpected - please report the issue at https://github.com/neurobagel/configure-nb/issues."
            )
        log_error(logger, f"{err_message}\nValidation details:\n {err}")

    # TODO: Remove for debugging
    print(config)

    # env_vars = util.flatten_config_to_dict(config)
    util.write_config_to_env_file(config, output_file)
    logger.info(
        f"Environment variable configuration successfully written to: {output_file}"
    )
