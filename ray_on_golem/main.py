import click

from ray_on_golem.network_stats import main as network_stats
from ray_on_golem.server import main as webserver
from ray_on_golem.utils import prepare_tmp_dir


@click.group()
def cli():
    pass


cli.add_command(network_stats)
cli.add_command(webserver)


def main():
    prepare_tmp_dir()

    cli()


if __name__ == "__main__":
    main()
