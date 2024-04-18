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
    """Executes a given Homebrew command with specified arguments.

    This function runs a Homebrew command based on the given list of arguments. It can optionally
    run in a quiet mode, suppressing the output to the standard output and only returning the
    result. If the command execution fails, it raises an exception.

    Args:
        args: A list of strings representing the arguments to pass to the Homebrew command. The
              first element should be the Homebrew command (e.g., 'update', 'install').
        quiet: If True, suppresses the command's output. If False, the command's output is printed
               to the console. Defaults to False.

    Returns:
        A string containing the output of the Homebrew command if `quiet` is True, otherwise an
        empty string.

    Raises:
        typer.Exit: An error is raised with exit code 1 if the Homebrew command fails to execute
                    properly, providing error details in the console.
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
    """Runs a specified command with arguments, controlling output and exit behavior.

    This function allows for the execution of any command with a list of arguments. It provides
    control over whether the program should exit on a command failure and whether the output
    should be suppressed.

    Args:
        cmd: The command to be executed, as a string.
        args: A list of strings representing the arguments for the command.
        exit_on_fail: If True, the program will exit if the command fails to execute successfully.
                      Defaults to False.
        quiet: If True, suppresses the output of the command, only showing errors. Defaults to False.

    Returns:
        If quiet is False and the command executes successfully, returns True.
        If the command fails and exit_on_fail is False, returns False.
        Otherwise, the output of the command as a string if quiet is True and the command executes successfully.

    Raises:
        typer.Exit: If exit_on_fail is True and the command fails to execute, it will raise a
                    typer.Exit exception to halt the program.
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
    """Prints a horizontal rule with a message.

    This function prints a styled horizontal rule followed by a given message. The message is
    converted to uppercase and displayed with the rule.

    Args:
        msg: The message to display alongside the rule.

    Note:
        The rule and message are styled in bold cyan.
    """
    rule_style = "bold cyan"
    msg_style = "bold cyan"
    console.print()
    console.rule(f"[{msg_style}]── {msg.upper()}[/{msg_style}]", align="left", style=rule_style)


@cache
def top_level_packages() -> list[str]:
    """Retrieves a list of all top-level installed packages using Homebrew.

    This function executes the Homebrew command to list all top-level (not dependencies of another)
    packages that are currently installed. It utilizes caching to avoid repeated executions for the
    same information.

    Returns:
        A list of strings, where each string is the name of a top-level installed package.
    """
    packages = run_homebrew(["leaves", "-r"], quiet=True).splitlines()
    return [pkg for pkg in packages if pkg]


def package_used_by(package: str) -> list[str]:
    """Finds all installed Homebrew packages that depend on a specified package.

    This function queries Homebrew to find all installed packages that have the specified package
    as a dependency.

    Args:
        package: The name of the package to check for dependents.

    Returns:
        A list of package names that depend on the specified package.
    """
    response = run_homebrew(["uses", "--installed", package], quiet=True)

    return [x for x in re.split(r"\s+", response.strip()) if x]
