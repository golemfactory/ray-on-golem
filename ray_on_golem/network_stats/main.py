import asyncio
import logging
import logging.config
import pathlib
from contextlib import asynccontextmanager
from typing import Dict, Optional

import click
import yaml

from ray_on_golem.cli import with_datadir
from ray_on_golem.network_stats.services import NetworkStatsService
from ray_on_golem.provider.node_provider import GolemNodeProvider
from ray_on_golem.server.services import YagnaService
from ray_on_golem.server.settings import YAGNA_PATH, get_logging_config
from ray_on_golem.server.services.reputation.service import ReputationService


def validate_config_file(ctx, param, value):
    with open(value) as file:
        config = yaml.safe_load(file.read())

    GolemNodeProvider._apply_config_defaults(config)

    return config


def validate_node_type(ctx, param, value):
    node_types = ctx.params["cluster_config_file"]["available_node_types"]
    if value not in node_types:
        raise click.BadParameter(
            f"Given node type `{value}` is not found in the config file! Available node types: `{'`, `'.join(node_types.keys())}`",
        )

    return value


@click.command(
    name="network-stats",
    short_help="Run Golem Network statistics.",
    help="Run Golem Network statistics based on given cluster config file and node type.",
    context_settings={"show_default": True},
)
@click.argument("cluster-config-file", type=click.Path(exists=True), callback=validate_config_file)
@click.argument("node-type", default="ray.head.default", callback=validate_node_type)
@click.option(
    "-d",
    "--duration",
    type=int,
    default=5,
    help="Set the duration of the statistics gathering process, in minutes.",
)
@click.option(
    "--enable-logging",
    is_flag=True,
    default=False,
    help="Enable verbose logging.",
)
@with_datadir
def main(*args, **kwargs):
    asyncio.run(_network_stats(*args, **kwargs))


async def _network_stats(
    cluster_config_file: Dict,
    node_type: str,
    duration: int,
    enable_logging: bool,
    datadir: Optional[pathlib.Path],
):
    provider_params = cluster_config_file["provider"]["parameters"]

    datadir = datadir or provider_params["webserver_datadir"]

    if enable_logging:
        logging.config.dictConfig(get_logging_config(datadir=datadir))

    async with network_stats_service(
        provider_params["enable_registry_stats"],
        provider_params["payment_network"],
        provider_params["payment_driver"],
        datadir,
    ) as stats_service:
        await stats_service.run(cluster_config_file, node_type, duration)


@asynccontextmanager
async def network_stats_service(
    registry_stats: bool,
    network: str,
    driver: str,
    datadir: Optional[pathlib.Path],
) -> NetworkStatsService:
    service = NetworkStatsService(registry_stats)
    yagna_service = YagnaService(
        yagna_path=YAGNA_PATH,
        datadir=datadir,
    )

    async with ReputationService(datadir):
        await yagna_service.init()
        await yagna_service.run_payment_fund(network, driver)

        await service.init(yagna_appkey=yagna_service.yagna_appkey)

        yield service

        await service.shutdown()
        await yagna_service.shutdown()


if __name__ == "__main__":
    main()
