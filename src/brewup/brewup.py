"""brewup CLI."""

from pathlib import Path
from typing import Annotated, Optional

import typer
from loguru import logger

from brewup.cli import instantiate_configuration
from brewup.constants import APP_DIR, VERSION
from brewup.models import Homebrew, Package
from brewup.utils import console, instantiate_logger, rule
from brewup.views import choose_packages, update_table

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)
typer.rich_utils.STYLE_HELPTEXT = ""


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"{__package__} version: {VERSION}")
        raise typer.Exit()


@app.command()
def main(
    all_packages: Annotated[
        bool,
        typer.Option(
            "--all",
            help="Bypass all prompts and upgrade all packages",
            show_default=True,
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-n",
            help="Run all brew commands with the --dry-run flag",
            show_default=True,
        ),
    ] = False,
    excluded_packages: Annotated[
        bool,
        typer.Option(
            "--excluded",
            help="Show updates excluded by config",
            show_default=True,
        ),
    ] = False,
    greedy: Annotated[
        Optional[bool],
        typer.Option(
            "--greedy/--not-greedy",
            help="Bypass configuration file to control passing the --greedy flag to brew outdated",
            show_default=False,
        ),
    ] = None,
    info_option: Annotated[
        Optional[str],
        typer.Option("--info", help="Find information about a formula or cask", show_default=False),
    ] = None,
    list_upgradable: Annotated[
        bool,
        typer.Option(
            "--list",
            help="Show what would be upgraded, but do not actually upgrade anything",
            show_default=True,
        ),
    ] = False,
    log_file: Annotated[
        Path,
        typer.Option(
            help="Path to log file",
            show_default=True,
            dir_okay=False,
            file_okay=True,
            exists=False,
        ),
    ] = Path(f"{APP_DIR}/brewup.log"),
    log_to_file: Annotated[
        bool,
        typer.Option(
            "--log-to-file",
            help="Log to file",
            show_default=True,
        ),
    ] = False,
    select_packages: Annotated[
        bool,
        typer.Option(
            "--select",
            help="Select which packages will be upgraded",
            show_default=True,
        ),
    ] = False,
    verbosity: Annotated[
        int,
        typer.Option(
            "-v",
            "--verbose",
            show_default=True,
            help="""Set verbosity level(0=INFO, 1=DEBUG, 2=TRACE)""",
            count=True,
        ),
    ] = 0,
    version: Annotated[  # noqa: ARG001
        Optional[bool],
        typer.Option(
            "--version",
            is_eager=True,
            callback=version_callback,
            help="Print version and exit",
        ),
    ] = None,
) -> None:
    """A CLI that automates upgrading Homebrew and all installed packages.

    \b
    Brewup runs the following routines in order to keep your system up to date with the latest versions of all installed formulae and casks.

    Note: Brewup will not upgrade packages that are pinned or excluded in the configuration file. It will also not upgrade packages that are not outdated.

        1. brew update
        2. Upgrades installed packages based on many configuration settings
        3. brew autoremove
        4. brew cleanup

    [bold]Usage Examples:[/bold]

    [dim]Upgrade available formulae/casks[/dim]
    brewup

    [dim]Include formulae and casks that are excluded in the configuration file[/dim]
    brewup --all

    [dim]Select which formulae/casks to upgrade[/dim]
    brewup --select

    [dim]See all available upgrades but don't upgrade anything[/dim]
    brewup --list

    [dim]Only formulae/casks that are excluded in the configuration file[/dim]
    brewup --excluded


    """  # noqa: D301
    # Instantiate Logging and the configuration file
    instantiate_logger(verbosity, log_file, log_to_file)
    instantiate_configuration()

    # Find information about a formula or cask
    if info_option:
        package = Package(name=info_option)
        console.print(package.info_table())
        raise typer.Exit()

    # Update Homebrew and work with outdated packages
    h = Homebrew(greedy=greedy)
    h.update()
    rule("Upgrade packages" if not list_upgradable else "Identify outdated packages")
    updates = h.available_updates()

    # Determine which packages to upgrade
    if all_packages:
        filtered_updates = updates
    elif excluded_packages:
        filtered_updates = [i for i in updates if i.excluded]
    else:
        filtered_updates = [i for i in updates if not i.excluded]

    if not filtered_updates:
        logger.success("No updates available")
        raise typer.Exit()

    if list_upgradable:
        console.print(
            update_table(
                filtered_updates, title="Updates excluded by config" if excluded_packages else None
            )
        )
        raise typer.Exit()

    for i in choose_packages(packages=filtered_updates, select_all=not select_packages):
        i.upgrade(dry_run=dry_run)

    h.cleanup(dry_run=dry_run)
    h.autoremove(dry_run=dry_run)


if __name__ == "__main__":
    app()
