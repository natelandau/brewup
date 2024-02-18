"""Instantiate BrewupConfig class and set default values."""

from typing import ClassVar

import sh
import typer
from confz import BaseConfig, ConfigSources, FileSource
from loguru import logger
from pydantic import field_validator

from brewup.constants import CONFIG_PATH


class BrewupConfig(BaseConfig):  # type: ignore [misc]
    """brewup Configuration."""

    # Default values
    app_dir: str | None = None  # Target location for Applications, mimics --appdir
    exclude_updades: tuple[str, ...] = ()
    greedy_casks: bool = False
    homebrew_command: str = "brew"
    reopen_casks: tuple[str, ...] = ()
    no_quarantine: tuple[str, ...] = ()

    CONFIG_SOURCES: ClassVar[ConfigSources | None] = [
        FileSource(file=CONFIG_PATH),
    ]

    @field_validator("homebrew_command")
    @classmethod
    def brew_command_must_be_valid(cls, command: str) -> str:
        """Validate that the nomad address is a valid URL."""
        try:
            # Attempt to find the command in the PATH
            sh.which(command)
        except sh.ErrorReturnCode as e:
            logger.error(f"{command} is not available in the PATH")
            raise typer.Exit(code=1) from e
        else:
            return command
