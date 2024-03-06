"""Common views for brewup."""

import questionary
import typer
from loguru import logger
from rich.table import Table

from brewup.constants import CHOICE_STYLE
from brewup.models import Package


def choose_packages(packages: list[Package], select_all: bool = False) -> list[Package]:
    """Select packages to upgrade.

    Args:
        packages (list[Package]): List of packages.
        select_all (bool, optional): Select all packages. Defaults to False.

    Returns:
        list[Package]: List of selected packages.
    """
    if select_all:
        return packages

    selected_packages = questionary.checkbox(
        "Select packages for upgrade\n",
        choices=[questionary.Choice(title=i.name, value=i) for i in packages],
        style=CHOICE_STYLE,
        qmark="",
    ).ask()
    if selected_packages is None:
        raise typer.Exit()
    if not selected_packages:
        logger.info("No packages selected")
        raise typer.Exit()

    return selected_packages


def update_table(packages: list[Package], title: str | None = None) -> Table | str:
    """Display a table of available updates.

    Args:
        packages (list[Package]): List of packages.
        title (str): T

    Returns:
        Table | str: Table of packages or message.
    """
    if not title:
        title = "Available Updates"

    if not packages:
        return "✅ No available updates"

    table = Table(title=title, show_lines=True)
    table.add_column("#", style="cyan")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Current version", style="magenta")
    table.add_column("New version", style="green")

    for n, package in enumerate(packages, start=1):
        table.add_row(
            str(n),
            package.name,
            package.description,
            package.type,
            package.installed,
            package.current,
        )

    return table
