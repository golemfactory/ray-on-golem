import asyncio
import logging
import logging.config
import pathlib
from contextlib import asynccontextmanager
from typing import Dict, Optional

import click
import yaml

from ray_on_golem.network_stats.services import NetworkStatsService
from ray_on_golem.provider.node_provider import GolemNodeProvider
from ray_on_golem.server.services import YagnaService
from ray_on_golem.server.settings import DEFAULT_DATADIR, YAGNA_PATH, get_logging_config


@click.command(
    name="network-stats",
    short_help="Run Golem Network statistics.",
    help="Run Golem Network statistics based on given cluster config file.",
    context_settings={"show_default": True},
)
@click.argument("cluster-config-file", type=click.Path(exists=True))
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
@click.option(
    "--datadir",
    type=pathlib.Path,
    help=f"Ray on Golem's data directory. [default: {DEFAULT_DATADIR}"
    " (unless `webserver_datadir` is defined in the cluster config file)]",
)
def main(
    cluster_config_file: str,
    duration: int,
    enable_logging: bool,
    datadir: Optional[pathlib.Path],
):
    with open(cluster_config_file) as file:
        config = yaml.safe_load(file.read())

    GolemNodeProvider._apply_config_defaults(config)
    provider_params = config["provider"]["parameters"]

    datadir = datadir or provider_params["webserver_datadir"]

    if enable_logging:
        logging.config.dictConfig(get_logging_config(datadir=datadir))

    asyncio.run(_network_stats(provider_params, duration, datadir))


async def _network_stats(provider_params: Dict, duration: int, datadir: Optional[pathlib.Path]):
    async with network_stats_service(
        provider_params["enable_registry_stats"],
        provider_params["payment_network"],
        provider_params["payment_driver"],
        datadir,
    ) as stats_service:
        await stats_service.run(provider_params, duration)


@asynccontextmanager
async def network_stats_service(
    registry_stats: bool,
    network: str,
    driver: str,
    datadir: Optional[pathlib.Path],
) -> NetworkStatsService:
    network_stats_service: NetworkStatsService = NetworkStatsService(registry_stats)
    yagna_service = YagnaService(
        yagna_path=YAGNA_PATH,
        datadir=datadir,
    )

    await yagna_service.init()
    await yagna_service.run_payment_fund(network, driver)

    await network_stats_service.init(yagna_appkey=yagna_service.yagna_appkey)

    yield network_stats_service

    await network_stats_service.shutdown()
    await yagna_service.shutdown()


if __name__ == "__main__":
    main()
