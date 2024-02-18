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
            ["Available Updates", "arq", "fork", "dav1d", "gping", "GIT client", "2.39", "2.40"],
            [],
        ),
        (
            ["--list", "--all"],
            ["arq"],
            True,
            ["Available Updates", "arq", "fork", "dav1d", "gping", "GIT client", "2.39", "2.40"],
            [],
        ),
        (
            ["--list", "--excluded"],
            ["arq"],
            True,
            ["Updates excluded by config", "arq", "Multi-cloud"],
            ["fork", "dav1d", "gping", "GIT client", "2.39", "2.40"],
        ),
        (
            ["--list", "--excluded"],
            ["arq"],
            False,
            ["No updates available"],
            ["arq", "fork", "dav1d", "gping", "GIT client", "2.39", "2.40"],
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

    # Mock calls to Homebrew when packages call brew info <name>
    mocker.patch(
        "brewup.models.package.run_homebrew",
        side_effect=[mock_arq_info, mock_fork_info, mock_dav1d_info, mock_gping_info],
    )

    # WHEN running the command
    with BrewupConfig.change_config_sources(mock_config(exclude_updades=excluded_packages)):
        result = runner.invoke(app, cli_options)

    debug("result", strip_ansi(result.output))

    # THEN the output should contain the expected terms
    assert result.exit_code == 0
    for term in list_output_terms:
        assert term in strip_ansi(result.output)

    for term in list_negative_terms:
        assert term not in strip_ansi(result.output)


# ###########################################
