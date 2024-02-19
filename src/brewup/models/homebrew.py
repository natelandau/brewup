"""Homebrew model."""

import json

from loguru import logger
from rich.progress import Progress

from brewup.constants import PackageType
from brewup.utils import BrewupConfig, console, rule, run_homebrew

from .package import Package


class Homebrew:
    """Homebrew model."""

    def __init__(self, greedy: bool | None = None) -> None:
        self.excludes = BrewupConfig().exclude_updades
        self.greedy = greedy

    @staticmethod
    def update() -> None:
        """Update Homebrew."""
        rule("brew update")
        run_homebrew(["update"])

    def available_updates(self) -> list[Package]:
        """Get a list of available updates.

        Returns:
            list[Package]: A list of Package objects representing available updates.
        """
        with Progress(console=console, transient=True) as progress:
            progress.add_task("Identify outdated packages", total=None)

            # Build args for `brew outdated`
            args = ["outdated", "--json=v2"]

            if (self.greedy or BrewupConfig().greedy_casks) and self.greedy is not False:
                args.append("--greedy")

            # Run `brew outdated` and parse JSON response
            response = json.loads(run_homebrew(args, quiet=True))

            logger.trace(f"brew outdated response: {response}")

            upgrades = []
            for category, items in response.items():
                for item in items:
                    package = Package(
                        name=item["name"],
                        package_type=PackageType(category),
                        installed=item["installed_versions"],
                        current=item["current_version"],
                        pinned_version=item.get("pinned_version", None),
                        excluded=item["name"].lower() in (x.lower() for x in self.excludes),
                    )
                    logger.trace(f"Found update for {package.name}")
                    upgrades.append(package)

        progress.stop()
        logger.success("Identify outdated packages")
        return upgrades

    @staticmethod
    def autoremove(dry_run: bool = False) -> None:
        """Autoremove packages."""
        rule("brew autoremove")
        if dry_run:
            run_homebrew(["autoremove", "--dry-run"])
        else:
            run_homebrew(["autoremove"])

        logger.success("Autoremove packages")

    @staticmethod
    def cleanup(dry_run: bool = False) -> None:
        """Cleanup Homebrew."""
        rule("brew cleanup")
        if dry_run:
            run_homebrew(["cleanup", "--dry-run"])
        else:
            run_homebrew(["cleanup"])

        logger.success("Cleanup Homebrew")
