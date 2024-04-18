"""Common views for brewup."""

import questionary
import typer
from loguru import logger
from rich.table import Table

from brewup.constants import CHOICE_STYLE
from brewup.models import Package


def choose_packages(packages: list[Package], select_all: bool = False) -> list[Package]:
    """Selects packages to upgrade from a list of package objects.

    Present a checkbox selection interface to the user if `select_all` is False,
    allowing users to choose which packages they want to upgrade. If `select_all` is True, all
    packages are automatically selected for upgrade.

    Args:
        packages: A list of `Package` objects representing the available packages for upgrade.
        select_all: If True, automatically selects all packages without user interaction.
                    Defaults to False.

    Returns:
        A list of `Package` objects that were selected for upgrade.

    Raises:
        typer.Exit: If no packages are selected or if the selection process is cancelled.
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
    """Generates a table displaying available package updates or a message if there are none.

    Create a table with detailed information about each package that needs to be updated. If there
    are no packages to update, it returns a message indicating that all packages are up-to-date.

    Args:
        packages: A list of `Package` objects to be displayed in the table.
        title: An optional title for the table. If not provided, defaults to "Available Updates".

    Returns:
        A `Table` object with the package update information or a string message if there are no
        updates available.
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
