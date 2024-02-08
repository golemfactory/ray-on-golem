import logging
import logging.config
from pathlib import Path
from typing import Optional

import click
from aiohttp import web

from ray_on_golem.server.middlewares import error_middleware, trace_id_middleware
from ray_on_golem.server.services import GolemService, RayService, YagnaService
from ray_on_golem.server.settings import (
    DEFAULT_DATADIR,
    RAY_ON_GOLEM_SHUTDOWN_DEADLINE,
    WEBSOCAT_PATH,
    YAGNA_PATH,
    get_datadir,
    get_logging_config,
)
from ray_on_golem.server.views import routes

logger = logging.getLogger(__name__)


@click.command(
    name="webserver",
    help="Run Ray on Golem's webserver.",
    context_settings={"show_default": True},
)
@click.option(
    "-p",
    "--port",
    type=int,
    default=4578,
    help="Port for Ray on Golem's webserver to listen on.",
)
@click.option(
    "--self-shutdown/--no-self-shutdown",
    is_flag=True,
    help="Enable self-shutdown after last node termination.",
)
@click.option(
    "--registry-stats/--no-registry-stats",
    default=True,
    help="Enable collection of Golem Registry stats about resolved images.",
)
@click.option(
    "--datadir",
    type=Path,
    default=DEFAULT_DATADIR,
    help="Ray on Golem's data directory.",
)
def main(port: int, self_shutdown: bool, registry_stats: bool, datadir: Path):
    logging.config.dictConfig(get_logging_config(datadir))

    app = create_application(port, self_shutdown, registry_stats, get_datadir(datadir))

    logger.info(f"Starting server... {port=}, {self_shutdown=}, {registry_stats=}")

    try:
        web.run_app(
            app,
            port=app["port"],
            print=None,
            shutdown_timeout=RAY_ON_GOLEM_SHUTDOWN_DEADLINE.total_seconds(),
        )
    except Exception:
        logger.info("Server unexpectedly died, bye!")
    else:
        logger.info("Stopping server done, bye!")


def create_application(
    port: int,
    self_shutdown: bool,
    registry_stats: bool,
    datadir: Path,
) -> web.Application:
    app = web.Application(
        middlewares=[
            trace_id_middleware,
            error_middleware,
        ]
    )

    app["port"] = port
    app["self_shutdown"] = self_shutdown
    app["registry_stats"] = registry_stats

    app["yagna_service"] = YagnaService(
        yagna_path=YAGNA_PATH,
        datadir=datadir,
    )

    app["golem_service"] = GolemService(
        websocat_path=WEBSOCAT_PATH,
        registry_stats=app["registry_stats"],
    )

    app["ray_service"] = RayService(
        ray_on_golem_port=port,
        golem_service=app["golem_service"],
        yagna_service=app["yagna_service"],
        datadir=datadir,
    )

    app.add_routes(routes)
    app.cleanup_ctx.append(yagna_service_ctx)
    app.cleanup_ctx.append(golem_service_ctx)
    app.cleanup_ctx.append(ray_service_ctx)
    app.on_startup.append(startup_print)
    app.on_shutdown.append(shutdown_print)

    return app


async def startup_print(app: web.Application) -> None:
    logger.info("Starting server done, listening on port {}".format(app["port"]))


async def shutdown_print(app: web.Application) -> None:
    print("")  # explicit new line to console to visually better handle ^C
    logger.info("Stopping server gracefully, forcing after `%s`...", RAY_ON_GOLEM_SHUTDOWN_DEADLINE)


async def yagna_service_ctx(app: web.Application) -> None:
    yagna_service: YagnaService = app["yagna_service"]

    await yagna_service.init()

    yield

    await yagna_service.shutdown()


async def golem_service_ctx(app: web.Application) -> None:
    golem_service: GolemService = app["golem_service"]
    yagna_service: YagnaService = app["yagna_service"]

    await golem_service.init(yagna_appkey=yagna_service.yagna_appkey)

    yield

    await golem_service.shutdown()


async def ray_service_ctx(app: web.Application) -> None:
    ray_service: RayService = app["ray_service"]

    yield

    await ray_service.shutdown()


@click.command(
    help="Start Ray on Golem's webserver and the yagna daemon.",
    context_settings={"show_default": True},
)
@click.option(
    "-p",
    "--port",
    type=int,
    default=4578,
    help="Port for Ray on Golem's webserver to listen on.",
)
@click.option(
    "--registry-stats/--no-registry-stats",
    default=True,
    help="Enable collection of Golem Registry stats about resolved images.",
)
@click.option(
    "--datadir",
    type=Path,
    help=f"Ray on Golem's data directory. By default, uses a system data directory: {DEFAULT_DATADIR}",
)
def start(port: int, registry_stats: bool, datadir: Optional[Path] = None):
    from ray_on_golem.client import RayOnGolemClient

    client = RayOnGolemClient(port)
    client.start_webserver(
        registry_stats=registry_stats,
        datadir=datadir,
        self_shutdown=False,
    )


@click.command(
    help="Stop Ray on Golem's webserver and the yagna daemon.",
    context_settings={"show_default": True},
)
@click.option(
    "-p",
    "--port",
    type=int,
    default=4578,
    help="Port for Ray on Golem's webserver to listen on.",
)
def stop(port):
    from ray_on_golem.client import RayOnGolemClient

    client = RayOnGolemClient(port)
    client.stop_webserver()


if __name__ == "__main__":
    main()
