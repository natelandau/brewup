"""Model for a Homebrew formulae or cask."""
import json

from loguru import logger

from brewup.constants import PackageType
from brewup.utils import BrewupConfig, run_command, run_homebrew


class Package:
    """Model for a Homebrew formulae or cask."""

    def __init__(
        self,
        name: str,
        package_type: PackageType,
        installed: list[str],
        current: str,
        pinned_version: str | None,
        skip_upgrade: bool = False,
    ) -> None:
        self.name = name
        self.installed = installed
        self.current = current
        self.type = package_type
        self.pinned_version = pinned_version
        self._info: dict = {}
        self.skip_upgrade = skip_upgrade

    def __str__(self) -> str:
        """Return string representation of Package."""
        return f"{self.name} ({self.type}) - {self.installed[0]} -> {self.current}"

    @property
    def info(self) -> dict:
        """Return package info."""
        if not self._info:
            brew_info_output = json.loads(
                run_homebrew(["info", "--json=v2", f"--{self.type.value}", self.name], quiet=True)
            )
            self._info = brew_info_output[self.type.value][0]

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

    def _open_cask(self) -> None:
        """Reopen cask if it was closed."""
        if (
            self.type == PackageType.CASKS
            and self.name.lower() in [x.lower for x in BrewupConfig().reopen_casks]
            and run_command("open", ["-a", self.app_path])
        ):
            logger.success(f"Reopen {self.name}")

    def _unquarantine_cask(self) -> None:
        """Unquarantine cask."""
        if (
            self.type == PackageType.CASKS
            and self.name.lower() in [x.lower for x in BrewupConfig().no_quarantine]
            and run_command("xattr", ["-d", "com.apple.quarantine", self.app_path])
        ):
            logger.success(f"Unquarantined {self.name}")

    def upgrade(self, dry_run: bool = False) -> None:
        """Upgrade package."""
        if self.skip_upgrade:
            logger.trace(f"Skipping upgrade for {self.name}")
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
