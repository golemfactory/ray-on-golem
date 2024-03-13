from pathlib import Path

import click


def with_datadir(cli_func):
    from ray_on_golem.server.settings import DEFAULT_DATADIR

    return click.option(
        "--datadir",
        type=Path,
        help=f"Ray on Golem's data directory. By default, uses a system data directory: {DEFAULT_DATADIR}",
    )(cli_func)
