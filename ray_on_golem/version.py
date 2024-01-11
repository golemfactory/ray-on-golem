from pathlib import Path

import click
from pkg_resources import get_distribution

PACKAGE_NAME = "ray-on-golem"


def get_version() -> str:
    """Return the version of the package."""
    pyproject_path = Path(__file__).parents[1] / "pyproject.toml"
    if pyproject_path.exists():
        import toml  # noqa  # we don't want to require `toml` for packaged releases

        with open(pyproject_path) as f:
            pyproject = toml.loads(f.read())

        return pyproject["tool"]["poetry"]["version"]

    return get_distribution(PACKAGE_NAME).version


@click.command(
    short_help=f"Show `{PACKAGE_NAME}` version.",
)
def version():
    print(f"{PACKAGE_NAME} {get_version()}")
