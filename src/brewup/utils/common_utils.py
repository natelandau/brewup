"""Common utility functions for brewup."""

import re
import sys
from functools import cache

import sh
import typer
from loguru import logger
from rich.text import Text

from .config import BrewupConfig
from .console import console


def run_homebrew(args: list[str], quiet: bool = False) -> str:
    """Run a Homebrew command.

    Args:
        args (list[str]): List of arguments for the Homebrew command.
        quiet (bool, optional): Whether to suppress output. Defaults to False.

    Returns:
        str: Output of the Homebrew command.

    Raises:
        typer.Exit: If the command fails.
    """
    homebrew = sh.Command(BrewupConfig().homebrew_command)
    command_as_string = f"{BrewupConfig().homebrew_command} {' '.join(args)}"
    logger.debug(f"Running: [code]{command_as_string}[/code]")

    if quiet:
        try:
            return homebrew(*args)
        except sh.ErrorReturnCode as e:
            if args[0] == "info":
                logger.error(e.stderr.decode("utf-8").removeprefix("Error: "))
            else:
                logger.error(f"Could not run `{e.full_cmd}`")
                console.print(e.stderr.decode("utf-8"))

            raise typer.Exit(1) from e

    try:
        for line in homebrew(*args, _iter=True, _err=sys.stderr):
            console.print(Text.from_ansi(line))
    except sh.ErrorReturnCode as e:
        logger.error(f"Could not run `{e.full_cmd}`")
        console.print(e.stderr.decode("utf-8"))
        raise typer.Exit(1) from e

    return ""


def run_command(
    cmd: str, args: list[str], exit_on_fail: bool = False, quiet: bool = False
) -> str | bool:
    """Run a command.

    Args:
        cmd (str): The command to run.
        args (list[str]): List of arguments for the command.
        exit_on_fail (bool, optional): Whether to exit the program if the command fails. Defaults to False.
        quiet (bool, optional): Whether to suppress output. Defaults to False.

    Returns:
        str | bool: Output of the command or False if the command fails.
    """
    command = sh.Command(cmd)
    command_as_string = f"{cmd} {' '.join(args)}"
    logger.debug(f"Running: [code]{command_as_string}[/code]")

    if quiet:
        try:
            return command(*args)
        except sh.ErrorReturnCode as e:
            if exit_on_fail:
                logger.error(f"Could not run `{e.full_cmd}`")
                console.print(e.stderr.decode("utf-8"))
                raise typer.Exit(1) from e
            logger.error(e.stderr.decode("utf-8"))
            return False

    try:
        for line in command(*args, _iter=True, _err=sys.stderr):
            console.print(Text.from_ansi(line))
    except sh.ErrorReturnCode as e:
        if exit_on_fail:
            logger.error(f"Could not run `{e.full_cmd}`")
            console.print(e.stderr.decode("utf-8"))
            raise typer.Exit(1) from e
        logger.error(e.stderr.decode("utf-8"))
        return False

    return True


def rule(msg: str) -> None:
    """Print a rule."""
    rule_style = "bold cyan"
    msg_style = "bold cyan"
    console.print()
    console.rule(f"[{msg_style}]{msg.upper()}[/{msg_style}]", align="left", style=rule_style)


@cache
def top_level_packages() -> list[str]:
    """List all top-level installed packages.

    Returns:
        list[str]: List of top-level installed packages.
    """
    packages = run_homebrew(["leaves", "-r"], quiet=True).splitlines()
    return [pkg for pkg in packages if pkg]


def package_used_by(package: str) -> list[str]:
    """List all packages that depend on a given package.

    Args:
        package (str): The package to check.

    Returns:
        list[str]: List of packages that depend on the given package.
    """
    response = run_homebrew(["uses", "--installed", package], quiet=True)

    return [x for x in re.split(r"\s+", response.strip()) if x]
