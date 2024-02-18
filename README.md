[![PyPI version](https://badge.fury.io/py/brewup.svg)](https://badge.fury.io/py/brewup) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/brewup) [![Automated Tests](https://github.com/natelandau/brewup/actions/workflows/automated-tests.yml/badge.svg?branch=main)](https://github.com/natelandau/brewup/actions/workflows/automated-tests.yml) [![codecov](https://codecov.io/gh/natelandau/brewup/graph/badge.svg?token=ZTBWSEACF9)](https://codecov.io/gh/natelandau/brewup)

# brewup

A CLI that automates upgrading Homebrew and all installed packages. Brewup runs the following routines in order to keep your system up to date with the latest versions of all installed formulae and casks.

1. `brew update`
2. Upgrades installed packages based on many configuration settings
3. `brew autoremove`
4. `brew cleanup`

The settings allow for a variety of options including:

-   Excluding specific formulae/casks from being upgraded
-   Running `brew upgrade` with the `--greedy` flag
-   Opening casks after upgrading with `open -a {cask}`
-   Removing specific casks from MacOS quarantine
-   Select which available formulae/casks to upgrade

## Installation

It is recommended to use [PIPX](https://pypa.github.io/pipx/) to install this package.

```bash
pipx install brewup
```

If pipx is not an option, you can install Brewup in your Python user directory.

```bash
python -m pip install --user brewup
```

Note: brewup requires Python >= v3.10.

## Usage

Upgrade available formulae/casks:

```bash
brewup
```

Include formulae and casks that are excluded in the configuration file:

```bash
brewup --all
```

Select which formulae/casks to upgrade:

```bash
brewup --select
```

See all available upgrades but don't upgrade anything:

```bash
brewup --list
```

Only formulae/casks that are excluded in the configuration file:

```bash
brewup --excluded
```

## Configuration

On first run, an empty configuration file will be created at `~/Library/Application Support/brewup/config.toml`. This file can be edited to customize the behavior of brewup.

```toml
# Configuration for brewup

# Target location for Applications, mimics --appdir. If empty, uses default
# app_dir = ""

# List of packages to exclude from updates
exclude_updades = []

# Update all casks, even if they auto-update
greedy_casks = false

# Full path to `brew` if not in $PATH
# homebrew_command = ""

# List of casks to open after updating
no_quarantine = []
```

## Contributing

## Setup: Once per project

1. Install Python 3.10 and [Poetry](https://python-poetry.org)
2. Clone this repository. `git clone https://github.com/natelandau/brewup`
3. Install the Poetry environment with `poetry install`.
4. Activate your Poetry environment with `poetry shell`.
5. Install the pre-commit hooks with `pre-commit install --install-hooks`.

## Developing

-   This project follows the [Conventional Commits](https://www.conventionalcommits.org/) standard to automate [Semantic Versioning](https://semver.org/) and [Keep A Changelog](https://keepachangelog.com/) with [Commitizen](https://github.com/commitizen-tools/commitizen).
    -   When you're ready to commit changes run `cz c`
-   Run `poe` from within the development environment to print a list of [Poe the Poet](https://github.com/nat-n/poethepoet) tasks available to run on this project. Common commands:
    -   `poe lint` runs all linters
    -   `poe test` runs all tests with Pytest
-   Run `poetry add {package}` from within the development environment to install a run time dependency and add it to `pyproject.toml` and `poetry.lock`.
-   Run `poetry remove {package}` from within the development environment to uninstall a run time dependency and remove it from `pyproject.toml` and `poetry.lock`.
-   Run `poetry update` from within the development environment to upgrade all dependencies to the latest versions allowed by `pyproject.toml`.
