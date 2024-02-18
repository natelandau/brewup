# type: ignore
"""Shared fixtures for tests."""

from pathlib import Path

import pytest
from confz import DataSource, FileSource

from brewup.utils import BrewupConfig, console

FIXTURE_CONFIG = Path(__file__).resolve().parent / "fixtures/fixture_config.toml"


@pytest.fixture()
def mock_outdated_response():
    """Mock outdated response from Homebrew."""
    fixture = Path(__file__).resolve().parent / "fixtures/brew_outdated_response.json"
    return fixture.read_text()


@pytest.fixture()
def mock_arq_info():
    """Mock outdated response from Homebrew."""
    fixture = Path(__file__).resolve().parent / "fixtures/brew_info_arq.json"
    return fixture.read_text()


@pytest.fixture()
def mock_dav1d_info():
    """Mock outdated response from Homebrew."""
    fixture = Path(__file__).resolve().parent / "fixtures/brew_info_dav1d.json"
    return fixture.read_text()


@pytest.fixture()
def mock_fork_info():
    """Mock outdated response from Homebrew."""
    fixture = Path(__file__).resolve().parent / "fixtures/brew_info_fork.json"
    return fixture.read_text()


@pytest.fixture()
def mock_gping_info():
    """Mock outdated response from Homebrew."""
    fixture = Path(__file__).resolve().parent / "fixtures/brew_info_gping.json"
    return fixture.read_text()


@pytest.fixture()
def debug():
    """Print debug information to the console. This is used to debug tests while writing them."""

    def _debug_inner(label: str, value: str | Path, breakpoint: bool = False):
        """Print debug information to the console. This is used to debug tests while writing them.

        Args:
            label (str): The label to print above the debug information.
            value (str | Path): The value to print. When this is a path, prints all files in the path.
            breakpoint (bool, optional): Whether to break after printing. Defaults to False.

        Returns:
            bool: Whether to break after printing.
        """
        console.rule(label)
        if not isinstance(value, Path) or not value.is_dir():
            console.print(value)
        else:
            for p in value.rglob("*"):
                console.print(p)

        console.rule()

        if breakpoint:
            return pytest.fail("Breakpoint")

        return True

    return _debug_inner


@pytest.fixture()
def config_data():
    """Mock specific configuration data for use in tests."""

    def _inner(
        key_one: str | None = None,
        key_two: list[int] | None = None,
        key_three: tuple[str, ...] | None = None,
    ):
        override_data = {}
        if key_one:
            override_data["key_one"] = key_one
        if key_two:
            override_data["key_two"] = key_two
        if key_three:
            override_data["key_three"] = key_three

        mock_config_file = Path(__file__).resolve().parent / "fixtures/fixture_config.toml"

        return [
            FileSource(mock_config_file),
            DataSource(data=override_data),
        ]

    return _inner


@pytest.fixture()
def mock_config():
    """Mock specific configuration data for use in tests."""

    def _inner(
        exclude_updades: list[str] | None = None,
        greedy_casks: bool | None = None,
        homebrew_command: str | None = None,
        reopen_casks: list[str] | None = None,
        no_quarantine: list[str] | None = None,
    ):
        override_data = {}
        if exclude_updades:
            override_data["exclude_updades"] = exclude_updades
        if greedy_casks:
            override_data["greedy_casks"] = greedy_casks
        if homebrew_command:
            override_data["homebrew_command"] = homebrew_command
        if reopen_casks:
            override_data["reopen_casks"] = reopen_casks
        if no_quarantine:
            override_data["no_quarantine"] = no_quarantine

        return [FileSource(FIXTURE_CONFIG), DataSource(data=override_data)]

    return _inner
