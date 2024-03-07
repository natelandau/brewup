"""Constants for brewup."""

from enum import Enum
from pathlib import Path

import typer
from questionary import Style


class PackageType(str, Enum):
    """Homebrew package type."""

    FORMULAE = "formulae"
    CASKS = "casks"
    UNKNOWN = "unknown"


APP_DIR = Path(typer.get_app_dir("brewup"))
CONFIG_PATH = APP_DIR / "config.toml"
SPINNER = "bouncingBall"
VERSION = "0.3.1"
CHOICE_STYLE = Style(
    [
        ("highlighted", ""),  # hover state
        ("selected", "bold noreverse"),
        ("instruction", "fg:#c5c5c5"),
        ("text", "fg:#c5c5c5"),
    ]
)
