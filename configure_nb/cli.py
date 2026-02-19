import textwrap
from pathlib import Path
from typing import Annotated

import pydantic
import typer

from . import utility as util
from .federation_nodes_model import (
    InternalFederationNode,
    InternalFederationNodes,
)
from .logger import VerbosityLevel, configure_logger, log_error, logger
from .models import COMPOSE_PROFILE_TO_CLASS_MAP, BaseProfile, Quickstart

FEDERATION_NODE_SECTION_PREFIX = "node:"

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
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            "-o",
            help="Path to the directory where the generated .env file should be saved.",
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = Path("."),
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
    out_dotenv_path = output_dir / ".env"

    if config_file.exists():
        logger.info(f"Loading configuration from file: {config_file}")
        ini_contents = util.load_ini_as_dict(config_file)
    else:
        logger.info(
            "No configuration file provided. Using default values for all settings."
        )
        ini_contents = {}

    compose_profile = ini_contents.get("compose", {}).get("COMPOSE_PROFILES")
    if not compose_profile:
        logger.info(
            "The COMPOSE_PROFILES variable was not set. Defaulting to a test deployment configuration."
        )
        config_class: type[BaseProfile] = Quickstart
    elif compose_profile not in COMPOSE_PROFILE_TO_CLASS_MAP:
        log_error(
            logger,
            f"Invalid COMPOSE_PROFILES value: {compose_profile}. "
            f"Expected one of {list(COMPOSE_PROFILE_TO_CLASS_MAP.keys())}.",
        )
    else:
        config_class = COMPOSE_PROFILE_TO_CLASS_MAP[compose_profile]
        logger.info(f"Deployment configuration: {compose_profile}")

    ini_contents_to_validate = ini_contents.copy()
    in_federation_nodes = {}
    if compose_profile != "node":
        for node_validation_err in ini_contents:
            if node_validation_err.startswith(FEDERATION_NODE_SECTION_PREFIX):
                in_federation_nodes[node_validation_err] = (
                    ini_contents_to_validate.pop(node_validation_err)
                )

    try:
        config = config_class.model_validate(ini_contents_to_validate)
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

    if compose_profile != "node":
        out_nodes_json_path = output_dir / "local_nb_nodes.json"

        out_federation_nodes = []
        if not in_federation_nodes:
            if compose_profile == "portal":
                log_error(
                    logger,
                    "No internal nodes to federate were defined in the configuration INI file. "
                    "For a 'portal' deployment, you must define at least one internal node to federate over "
                    f"using a section header in the form \\[{FEDERATION_NODE_SECTION_PREFIX}<id>].",
                )
            else:
                out_federation_nodes.append(
                    InternalFederationNode(
                        name="Local graph 1",
                        api_url="http://api:8000",
                    )
                )
        else:
            # TODO: Can refactor out this section into a util
            node_validation_errs = []
            for node_id, node_definition in in_federation_nodes.items():
                try:
                    out_federation_nodes.append(
                        InternalFederationNode.model_validate(node_definition)
                    )
                except pydantic.ValidationError as err:
                    node_validation_err = (
                        f"- \\[{node_id}]\n"
                        f"{textwrap.indent(str(err), '  ')}"
                    )
                    node_validation_errs.append(node_validation_err)
            if node_validation_errs:
                log_error(
                    logger,
                    f"The configuration contains {len(node_validation_errs)} invalid definition(s) of internal federation nodes:\n"
                    + "\n\n".join(node_validation_errs),
                )

        out_federation_nodes = InternalFederationNodes(
            out_federation_nodes
        ).model_dump(by_alias=True, mode="json")
        util.write_json(out_nodes_json_path, out_federation_nodes)
        logger.info(
            f"Internal federation nodes configuration successfully written to: {out_nodes_json_path}"
        )

    util.write_text_file(out_dotenv_path, util.config_to_env_str(config))
    logger.info(
        f"Environment variable configuration successfully written to: {out_dotenv_path}"
    )
