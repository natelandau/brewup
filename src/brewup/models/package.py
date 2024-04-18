"""Model for a Homebrew formulae or cask."""

import json
import re

from loguru import logger
from rich.table import Table

from brewup.constants import PackageType
from brewup.utils import (
    BrewupConfig,
    package_used_by,
    run_command,
    run_homebrew,
    top_level_packages,
)


class Package:
    """Represents a Homebrew package, either a formula or a cask.

    This class models a Homebrew package, encapsulating information such as its name, type,
    installed versions, current version, pinned version, and exclusion status from upgrade
    operations.
    """

    def __init__(
        self,
        name: str,
        package_type: PackageType = PackageType.UNKNOWN,
        installed: list[str | dict] = [],
        current: str | None = None,
        pinned_version: str | None = None,
        excluded: bool = False,
    ) -> None:
        self._info: dict = {}
        self.name = name
        self._type = package_type

        self.installed = self._get_installed_version(installed)
        self.current = current

        self.pinned_version = pinned_version
        self.excluded = excluded

    def __str__(self) -> str:
        """Return string representation of Package."""
        return f"{self.name} ({self.type.value}): {self.installed[0]} -> {self.current}"

    def _get_installed_version(self, user_input: str | list[str | dict] | None = None) -> str:
        """Return list of installed version."""
        if user_input:
            if isinstance(user_input, list):
                if isinstance(user_input[0], dict):
                    return user_input[0]["version"]
                return user_input[0]

            return user_input

        if not (installed := self.info.get("installed")):
            return ""

        if isinstance(installed, list):
            return installed[0]["version"]

        return installed

    @property
    def info(self) -> dict:
        """Return package info and set self.type if not already set."""
        args = ["info", "--json=v2"]
        if self._type != PackageType.UNKNOWN:
            args.append(f"--{self._type.value}")
        args.append(self.name)

        if not self._info:
            brew_info_output = json.loads(run_homebrew(args, quiet=True))
            if self._type != PackageType.UNKNOWN:
                self._info = brew_info_output[self.type.value][0]
            elif len(brew_info_output["formulae"]) > 0:
                self._info = brew_info_output["formulae"][0]
                self._type = PackageType.FORMULAE
            elif len(brew_info_output["casks"]) > 0:
                self._info = brew_info_output["casks"][0]
                self._type = PackageType.CASKS

        return self._info

    @property
    def app_path(self) -> str:
        """Return the application name for a cask."""
        # Find the application name in the cask info
        artifacts = self.info.get("artifacts", [])
        if not artifacts:
            return ""
        app_name = next(artifact.get("app", [""])[0] for artifact in artifacts if "app" in artifact)
        if not app_name:
            return ""

        app_dir = BrewupConfig().app_dir or "/Applications"
        return f"{app_dir}/{app_name}"

    @property
    def description(self) -> str:
        """Return package description."""
        return self.info.get("desc", "")

    @property
    def homepage(self) -> str:
        """Return package homepage."""
        return self.info.get("homepage", "")

    @property
    def type(self) -> PackageType:
        """Return package type."""
        if self._type == PackageType.UNKNOWN:
            info = self.info
            logger.trace(f"identifying package type from info: {info}")

        return self._type

    @property
    def is_top_level(self) -> bool:
        """Return True if package is top level."""
        return self.name in top_level_packages()

    def _open_cask(self) -> None:
        """Reopens the application associated with a cask, if applicable.

        This method is used to automatically reopen a cask's application if it was closed during
        an update process. It checks if the package is a cask and matches any entries in a list
        of casks configured to be reopened. If so, it attempts to reopen the application by its path.
        """
        if (
            self.type == PackageType.CASKS
            and self.name.lower() in [x.lower for x in BrewupConfig().reopen_casks]
            and run_command("open", ["-a", self.app_path])
        ):
            logger.success(f"Reopen {self.name}")

    def _unquarantine_cask(self) -> None:
        """Removes the quarantine attribute from a cask application.

        This method checks if the package is a cask and if its name matches any entries in a
        predefined list of casks to be unquarantined. If both conditions are met, it executes
        a command to remove the quarantine attribute from the application's path, effectively
        unquarantining the cask.
        """
        if (
            self.type == PackageType.CASKS
            and self.name.lower() in [x.lower for x in BrewupConfig().no_quarantine]
            and run_command("xattr", ["-d", "com.apple.quarantine", self.app_path])
        ):
            logger.success(f"Unquarantined {self.name}")

    def info_table(self) -> Table:
        """Generates a detailed information table for the package.

        This method compiles detailed information about the package into a visually appealing table.
        It filters out certain keys that are not relevant for display and organizes the remaining
        information in a key-value format. The table includes the package's name, its description,
        installation status, type, dependencies, and more, depending on available data.

        Returns:
            A `Table` object containing the formatted information about the package.
        """
        table = Table(
            title=f"[bold]{self.name}[/bold]\n[italic]{self.description}[/italic]",
            title_style="",
            show_lines=True,
            show_header=False,
        )
        table.add_column("Key", style="cyan")
        table.add_column("Value")

        for key, value in self.info.items():
            if key in {
                "aliases",
                "artifacts",
                "bottle",
                "depends_on",
                "head_dependencies",
                "installed_time",
                "installed",
                "license",
                "link_overwrite",
                "linked_keg",
                "name",
                "oldname",
                "post_install_defined",
                "pour_bottle_only_if",
                "revision",
                "ruby_source_checksum",
                "ruby_source_path",
                "sha256",
                "tap_git_head",
                "token",
                "url_specs",
                "url",
                "urls",
                "uses_from_macos_bounds",
                "versions",
            }:
                continue

            if value:
                # Top of the table
                if key in {"full_name", "full_token"}:
                    table.add_row("Name", str(value))
                    table.add_row("Installed version", self.installed)
                    table.add_row("Top Level Install", str(self.is_top_level))
                    table.add_row("type", self.type.value)
                    used_by = package_used_by(self.name)
                    if used_by:
                        table.add_row("Used by", ", ".join(package_used_by(self.name)))
                    continue

                # Add roes based on key
                if key == "homepage":
                    table.add_row("Homepage", f"[link={value}]{value}[/link]")
                    continue

                if key == "keg_only_reason":
                    table.add_row("Keg only reason", str(value["reason"].lstrip(":")))
                    continue

                if re.search(
                    r"conflicts_with|dependencies|requirements|uses_from_macos|oldnames|versioned_formulae",
                    key,
                ):
                    v = (
                        ", ".join([x for x in value if isinstance(x, str)])
                        if isinstance(value, list)
                        else value
                    )
                    table.add_row(str(key).replace("_", " ").capitalize(), str(v))
                    continue

                table.add_row(str(key).replace("_", " ").capitalize(), str(value))

        return table

    def upgrade(self, dry_run: bool = False) -> None:
        """Upgrades the package to its latest version, with optional dry run mode.

        Initiates the upgrade process for the package using Homebrew commands, constructing the
        command based on the package's type (formula or cask) and additional configuration such
        as no quarantine for casks or specifying an app directory. It supports a dry run option
        for testing purposes.

        Args:
            dry_run: If True, performs a dry run of the upgrade process without actually updating
                 the package. Defaults to False.
        """
        # Skip if no current version to upgrade to
        if not self.current:
            logger.warning(f"Skipping {self.name} - no current version")
            return

        # Build args for `brew upgrade`
        args = ["upgrade", f"--{self.type.value}"]

        if dry_run:
            args.append("--dry-run")

        if self.type == PackageType.CASKS and self.name.lower() in [
            x.lower for x in BrewupConfig().no_quarantine
        ]:
            args.append("--no-quarantine")

        if self.type == PackageType.CASKS and BrewupConfig().app_dir:
            args.extend(["--appdir", BrewupConfig().app_dir])  # type: ignore [list-item]

        args.append(self.name)

        # Run `brew upgrade` and parse response
        run_homebrew(args)

        # Reopen cask if it was closed
        if not dry_run:
            self._open_cask()
            self._unquarantine_cask()
