"""Helpers for the CLI."""

import shutil
from pathlib import Path

import typer
from confz import validate_all_configs
from loguru import logger
from pydantic import ValidationError

from brewup.constants import CONFIG_PATH
from brewup.utils import console


def instantiate_configuration() -> None:
    """Instantiate the configuration file."""
    # Create a default configuration file if one does not exist
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        default_config_file = Path(__file__).parent.parent.resolve() / "default_config.toml"
        shutil.copy(default_config_file, CONFIG_PATH)
        logger.info(f"Created default configuration file: {CONFIG_PATH}")

    # Load and validate configuration
    try:
        validate_all_configs()
    except ValidationError as e:
        logger.error(f"Invalid configuration file: {CONFIG_PATH}")
        for error in e.errors():
            console.print(f"           [red]{error['loc'][0]}: {error['msg']}[/red]")
        raise typer.Exit(code=1) from e
