import click

from ray_on_golem.network_stats import main as network_stats
from ray_on_golem.server import main as webserver, start, stop
from ray_on_golem.version import version


@click.group()
def cli():
    pass


cli.add_command(network_stats)
cli.add_command(version)
cli.add_command(webserver)
cli.add_command(start)
cli.add_command(stop)


def main():
    cli()


if __name__ == "__main__":
    main()
