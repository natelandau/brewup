"""Common views for brewup."""

from rich.table import Table

from brewup.models import Package


def update_table(packages: list[Package]) -> Table | str:
    """Display a table of available updates.

    Args:
        packages (list[Package]): List of packages.

    Returns:
        Table | str: Table of packages or message.
    """
    if not [x for x in packages if not x.skip_upgrade]:
        return "✅ No available updates"

    table = Table(title="Available Updates", show_lines=True)
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Current version", style="magenta")
    table.add_column("New version", style="green")

    for package in [x for x in packages if not x.skip_upgrade]:
        table.add_row(
            package.name,
            package.description,
            package.type,
            package.installed[0],
            package.current,
        )

    return table


def skip_update_table(packages: list[Package]) -> Table | str:
    """Display a table of available updates.

    Args:
        packages (list[Package]): List of packages.

    Returns:
        Table | str: Table of packages or message.
    """
    if not [x for x in packages if x.skip_upgrade]:
        return "✅ No excluded updates"

    table = Table(
        title="Updates excluded by config",
        show_lines=True,
        caption="To upgrade these packages run [code]brew upgrade <package>[/code].",
    )
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Current version", style="magenta")
    table.add_column("New version", style="green")

    for package in [x for x in packages if x.skip_upgrade]:
        table.add_row(
            package.name,
            package.description,
            package.type,
            package.installed[0],
            package.current,
        )

    return table
