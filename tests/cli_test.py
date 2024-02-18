# type: ignore
"""Test brewup CLI."""


import pytest
from typer.testing import CliRunner

from brewup.__version__ import __version__
from brewup.cli import app
from brewup.utils import BrewupConfig
from tests.helpers import strip_ansi

runner = CliRunner()


def test_version():
    """Test printing version and then exiting."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"brewup version: {__version__}" in strip_ansi(result.output)


@pytest.mark.parametrize(
    ("has_updates", "terms_in_output"),
    [
        (False, ["No updates available"]),
        (
            True,
            ["Available Updates", "arq", "fork", "dav1d", "gping", "GIT client", "2.39", "2.40"],
        ),
    ],
)
def test_dry_run(
    debug,
    mocker,
    mock_outdated_response,
    mock_arq_info,
    mock_fork_info,
    mock_dav1d_info,
    mock_gping_info,
    mock_config,
    has_updates,
    terms_in_output,
):
    """Test dry run."""
    if not has_updates:
        mock_outdated_response = '{"casks": [], "formulae": []}'

    # Mock calls to Homebrew (first call is `brew update`, second is `brew outdated`)
    mocker.patch(
        "brewup.models.homebrew.run_homebrew",
        side_effect=[None, mock_outdated_response],
    )

    # Mock calls to Homebrew when packages get info
    mocker.patch(
        "brewup.models.package.run_homebrew",
        side_effect=[mock_arq_info, mock_fork_info, mock_dav1d_info, mock_gping_info],
    )

    with BrewupConfig.change_config_sources(mock_config()):
        result = runner.invoke(app, ["--dry-run"])

    # debug("result", strip_ansi(result.output))

    assert result.exit_code == 0
    for term in terms_in_output:
        assert term in strip_ansi(result.output)


@pytest.mark.parametrize(
    ("has_updates", "has_excludes", "terms_in_output"),
    [
        (False, False, ["No updates available"]),
        (True, False, ["No excluded updates"]),
        (True, True, ["Updates excluded by config ", "arq"]),
    ],
)
def test_excluded(
    debug,
    mocker,
    mock_outdated_response,
    mock_arq_info,
    mock_fork_info,
    mock_dav1d_info,
    mock_gping_info,
    mock_config,
    has_updates,
    has_excludes,
    terms_in_output,
):
    """Test dry run."""
    if not has_updates:
        mock_outdated_response = '{"casks": [], "formulae": []}'

    # Mock calls to Homebrew (first call is `brew update`, second is `brew outdated`)
    mocker.patch(
        "brewup.models.homebrew.run_homebrew",
        side_effect=[None, mock_outdated_response],
    )

    # Mock calls to Homebrew when packages get info
    mocker.patch(
        "brewup.models.package.run_homebrew",
        side_effect=[mock_arq_info, mock_fork_info, mock_dav1d_info, mock_gping_info],
    )

    if not has_excludes:
        with BrewupConfig.change_config_sources(mock_config()):
            result = runner.invoke(app, ["--excluded"])
    if has_excludes:
        with BrewupConfig.change_config_sources(mock_config(exclude_updades=["arq"])):
            result = runner.invoke(app, ["--excluded"])

    debug("result", strip_ansi(result.output))

    assert result.exit_code == 0
    for term in terms_in_output:
        assert term in strip_ansi(result.output)
