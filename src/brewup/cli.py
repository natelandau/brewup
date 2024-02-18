"""brewup CLI."""

import shutil
from pathlib import Path
from typing import Annotated, Optional

import questionary
import typer
from confz import validate_all_configs
from loguru import logger
from pydantic import ValidationError

from brewup.__version__ import __version__
from brewup.constants import APP_DIR, CHOICE_STYLE, CONFIG_PATH
from brewup.models import Homebrew
from brewup.utils import console, instantiate_logger, rule
from brewup.views import skip_update_table, update_table

app = typer.Typer(add_completion=False, no_args_is_help=True, rich_markup_mode="rich")
app_dir = typer.get_app_dir("brewup")
typer.rich_utils.STYLE_HELPTEXT = ""


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"{__package__} version: {__version__}")
        raise typer.Exit()


@app.command()
def main(
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-n",
            help="Show what would be upgraded, but do not actually upgrade anything",
            show_default=True,
        ),
    ] = False,
    excluded_updates: Annotated[
        bool,
        typer.Option(
            "--excluded",
            help="Show updates excluded by config",
            show_default=True,
        ),
    ] = False,
    no_interaction: Annotated[
        bool,
        typer.Option(
            "--no-interaction",
            "-y",
            help="Bypass all prompts and upgrade all packages",
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
    """Add application documentation here."""
    # Instantiate Logging
    instantiate_logger(verbosity, log_file, log_to_file)

    # Create a default configuration file if one does not exist
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        default_config_file = Path(__file__).parent.resolve() / "default_config.toml"
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

    h = Homebrew()
    h.update()
    rule("Upgrade packages" if not dry_run else "Identify outdated packages")
    updates = h.available_updates()

    if not updates:
        logger.success("No updates available")
        raise typer.Exit()
    if dry_run:
        console.print(update_table(updates))
        raise typer.Exit()
    if excluded_updates:
        console.print(skip_update_table(updates))
        raise typer.Exit()
    if no_interaction:
        packages_to_update = [i for i in updates if not i.skip_upgrade]
    else:
        packages_to_update = questionary.checkbox(
            "Unselect packages for upgrade\n",
            choices=[
                questionary.Choice(title=i.name, checked=True, value=i)
                for i in updates
                if not i.skip_upgrade
            ],
            style=CHOICE_STYLE,
            qmark="",
        ).ask()
        if not packages_to_update:
            raise typer.Exit()

    for i in packages_to_update:
        i.upgrade(dry_run=dry_run)

    h.autoremove(dry_run=dry_run)
    h.cleanup(dry_run=dry_run)


if __name__ == "__main__":
    app()
