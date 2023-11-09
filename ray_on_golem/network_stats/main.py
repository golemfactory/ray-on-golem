import asyncio
import logging
import logging.config
from contextlib import asynccontextmanager
from typing import Dict

import click
import yaml

from ray_on_golem.network_stats.services import NetworkStatsService
from ray_on_golem.server.services import YagnaService
from ray_on_golem.server.settings import LOGGING_CONFIG, YAGNA_PATH
from ray_on_golem.utils import prepare_tmp_dir


@click.command(
    name="network-stats",
    short_help="Run Golem Network statistics.",
    help="Run Golem Network statistics based on given cluster config file.",
)
@click.argument("cluster-config-file", type=click.Path(exists=True))
@click.option(
    "-d",
    "--duration",
    type=int,
    default=5,
    show_default=True,
    help="Set for how long gather stats, in minutes.",
)
@click.option(
    "--enable-logging",
    is_flag=True,
    default=True,
    show_default=True,
    help="Enable verbose logging.",
)
def main(cluster_config_file: str, duration: int, enable_logging: bool):
    if enable_logging:
        logging.config.dictConfig(LOGGING_CONFIG)

    with open(cluster_config_file) as file:
        config = yaml.safe_load(file.read())

    asyncio.run(_network_stats(config, duration))


async def _network_stats(config: Dict, duration: int):
    provider_config = config["provider"]

    async with golem_network_stats_service(
        provider_config["enable_registry_stats"]
    ) as stats_service:
        await stats_service.run(provider_config["parameters"], duration)


@asynccontextmanager
async def golem_network_stats_service(registry_stats: bool) -> NetworkStatsService:
    golem_network_stats_service: NetworkStatsService = NetworkStatsService(registry_stats)
    yagna_service = YagnaService(
        yagna_path=YAGNA_PATH,
    )

    await yagna_service.init()
    await golem_network_stats_service.init(yagna_appkey=yagna_service.yagna_appkey)

    yield golem_network_stats_service

    await golem_network_stats_service.shutdown()
    await yagna_service.shutdown()


if __name__ == "__main__":
    prepare_tmp_dir()
    main()
