import click

from ray_on_golem.network_stats import main as network_stats
from ray_on_golem.reputation.cli import reputation_cli
from ray_on_golem.server.main import main as webserver
from ray_on_golem.server.main import start, status, stop
from ray_on_golem.version import get_version, version


@click.group()
@click.version_option(get_version(), "--version", "-V")
def cli():
    pass


cli.add_command(network_stats)
cli.add_command(version)
cli.add_command(webserver)
cli.add_command(start)
cli.add_command(stop)
cli.add_command(status)
cli.add_command(reputation_cli)


def main():
    cli()


if __name__ == "__main__":
    main()
