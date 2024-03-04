# type: ignore
"""Test brewup CLI."""

import pytest
from typer.testing import CliRunner

from brewup.brewup import app
from brewup.constants import VERSION
from brewup.utils import BrewupConfig
from tests.helpers import strip_ansi

runner = CliRunner()


def test_version():
    """Test printing version and then exiting."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"brewup version: {VERSION}" in strip_ansi(result.output)


@pytest.mark.parametrize(
    (
        "cli_options",
        "excluded_packages",
        "has_available_updates",
        "list_output_terms",
        "list_negative_terms",
    ),
    [
        (["--list"], [], False, ["No updates available"], []),
        (
            ["--list"],
            [],
            True,
            ["Available Updates", "arq", "fork", "dav1d", "gping", "GIT client"],
            [],
        ),
        (
            ["--list", "--all"],
            ["arq"],
            True,
            ["Available Updates", "arq", "fork", "dav1d", "gping", "GIT client"],
            [],
        ),
        (
            ["--list", "--excluded"],
            ["arq"],
            True,
            ["Updates excluded by config", "arq", "Multi-cloud"],
            ["fork", "dav1d", "gping", "GIT client"],
        ),
        (
            ["--list", "--excluded"],
            ["arq"],
            False,
            ["No updates available"],
            ["arq", "fork", "dav1d", "gping", "GIT client"],
        ),
    ],
)
def test_list(
    debug,
    mocker,
    mock_outdated_response,
    mock_arq_info,
    mock_fork_info,
    mock_dav1d_info,
    mock_gping_info,
    mock_config,
    cli_options,
    has_available_updates,
    excluded_packages,
    list_output_terms,
    list_negative_terms,
):
    """Test list command."""
    # ###############
    # Setup the test
    # ###############
    if not has_available_updates:
        mock_outdated_response = '{"casks": [], "formulae": []}'

    # Mock calls to Homebrew (first call is `brew update`, second is `brew outdated`)
    mocker.patch(
        "brewup.models.homebrew.run_homebrew",
        side_effect=[None, mock_outdated_response],
    )
    mocker.patch(
        "brewup.models.package.run_homebrew",
        side_effect=[mock_arq_info, mock_fork_info, mock_dav1d_info, mock_gping_info],
    )

    # WHEN running the command
    with BrewupConfig.change_config_sources(mock_config(exclude_updades=excluded_packages)):
        result = runner.invoke(app, cli_options)

    # debug("result", strip_ansi(result.output))

    # THEN the output should contain the expected terms
    assert result.exit_code == 0
    for term in list_output_terms:
        assert term in strip_ansi(result.output)

    for term in list_negative_terms:
        assert term not in strip_ansi(result.output)


def test_info_command_arq(debug, mock_config, mocker, mock_arq_info):
    """Test info command."""
    # GIVEN a mocked response from Homebrew
    mocker.patch(
        "brewup.models.package.run_homebrew",
        return_value=mock_arq_info,
    )
    mocker.patch("brewup.models.package.top_level_packages", return_value=["arq"])
    mocker.patch("brewup.models.package.package_used_by", return_value=[])

    # WHEN running the command

    with BrewupConfig.change_config_sources(mock_config()):
        result = runner.invoke(app, ["--info", "arq"])

    # debug("result", strip_ansi(result.output))

    # THEN the output should contain the expected terms
    assert result.exit_code == 0
    assert "arq" in strip_ansi(result.output)
    assert "Auto updates      │ True" in strip_ansi(result.output)
    assert "Version           │ 7.26.6" in strip_ansi(result.output)
    assert "Installed version │ 7.25.1" in strip_ansi(result.output)
    assert "Homepage          │" in strip_ansi(result.output)
    assert "Name              │ arq" in strip_ansi(result.output)
    assert "Desc              │ Multi-cloud backup application" in strip_ansi(result.output)


def test_info_command_gping(debug, mock_config, mocker, mock_gping_info):
    """Test info command."""
    # GIVEN a mocked response from Homebrew
    mocker.patch(
        "brewup.models.package.run_homebrew",
        return_value=mock_gping_info,
    )
    mocker.patch("brewup.models.package.top_level_packages", return_value=[])
    mocker.patch("brewup.models.package.package_used_by", return_value=[])

    # WHEN running the command
    with BrewupConfig.change_config_sources(mock_config()):
        result = runner.invoke(app, ["--info", "gping"])

    debug("result", strip_ansi(result.output))

    # THEN the output should contain the expected terms
    assert result.exit_code == 0
    assert "gping" in strip_ansi(result.output)
    assert "Installed version  │ 1.16.1" in strip_ansi(result.output)
    assert "Tap                │ homebrew/core" in strip_ansi(result.output)
    assert "Build dependencies │ pkg-config, rust " in strip_ansi(result.output)
    assert "Homepage" in strip_ansi(result.output)
    assert "Dependencies       │ libgit2" in strip_ansi(result.output)
