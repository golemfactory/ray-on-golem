import asyncio
import logging
import logging.config
import pathlib
from typing import Dict, Optional

import click
import yaml
from golem.utils.asyncio import ensure_cancelled

from ray_on_golem.cli import with_datadir
from ray_on_golem.network_stats.services import NetworkStatsService
from ray_on_golem.provider.node_provider import GolemNodeProvider
from ray_on_golem.reputation.service import ReputationService
from ray_on_golem.server.services import YagnaService
from ray_on_golem.server.settings import YAGNA_PATH, get_logging_config


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
def main(
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

    yagna_service = YagnaService(
        yagna_path=YAGNA_PATH,
        datadir=datadir,
    )
    reputation_service = ReputationService(datadir)
    stats_service = NetworkStatsService(provider_params["enable_registry_stats"])

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        _start_services(
            yagna_service,
            reputation_service,
            stats_service,
            provider_params["payment_network"],
            provider_params["payment_driver"],
        )
    )

    run_task = loop.create_task(stats_service.run(cluster_config_file, node_type, duration))

    try:
        loop.run_until_complete(run_task)
    except KeyboardInterrupt:
        print("Received CTRL-C, exiting...")
        loop.run_until_complete(ensure_cancelled(run_task))

    loop.run_until_complete(
        _stop_services(
            stats_service,
            reputation_service,
            yagna_service,
        )
    )


async def _start_services(
    yagna_service: YagnaService,
    reputation_service: ReputationService,
    stats_service: NetworkStatsService,
    network: str,
    driver: str,
) -> None:
    await yagna_service.start()
    await yagna_service.prepare_funds(network, driver)

    await reputation_service.start()

    await stats_service.start(yagna_appkey=yagna_service.yagna_appkey)


async def _stop_services(
    stats_service: NetworkStatsService,
    reputation_service: ReputationService,
    yagna_service: YagnaService,
) -> None:
    await stats_service.stop()

    await reputation_service.stop()

    await yagna_service.stop()


if __name__ == "__main__":
    main()
