import click

from ray_on_golem.network_stats import main as network_stats
from ray_on_golem.server import main as webserver
from ray_on_golem.server import start, status, stop
from ray_on_golem.version import version
from ray_on_golem.server.services.reputation.cli import reputation_cli


@click.group()
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
