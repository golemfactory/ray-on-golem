import logging
import logging.config
import os
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import click
import colorful
import psutil
from aiohttp import web
from golem.utils.asyncio import create_task_with_logging, ensure_cancelled_many

from ray_on_golem.cli import with_datadir
from ray_on_golem.reputation.updater import ReputationUpdater
from ray_on_golem.server.middlewares import error_middleware, trace_id_middleware
from ray_on_golem.server.services import GolemService, RayService, YagnaService
from ray_on_golem.server.settings import (
    RAY_ON_GOLEM_SHUTDOWN_CONNECTIONS_TIMEOUT,
    WEBSOCAT_PATH,
    YAGNA_PATH,
    get_datadir,
    get_logging_config,
)
from ray_on_golem.server.views import routes

if TYPE_CHECKING:
    from ray_on_golem.reputation.service import ReputationService


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
@with_datadir
def main(port: int, self_shutdown: bool, registry_stats: bool, datadir: Path):
    logging.config.dictConfig(get_logging_config(datadir))

    app = create_application(port, self_shutdown, registry_stats, get_datadir(datadir))

    logger.info(f"Starting server... {port=}, {self_shutdown=}, {registry_stats=}, {datadir=}")

    try:
        web.run_app(
            app,
            port=app["port"],
            print=None,
            shutdown_timeout=RAY_ON_GOLEM_SHUTDOWN_CONNECTIONS_TIMEOUT.total_seconds(),
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
    from ray_on_golem.reputation.service import ReputationService

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
        webserver_port=port,
        golem_service=app["golem_service"],
        datadir=datadir,
    )

    app["reputation_service"] = ReputationService(datadir=datadir)

    app.add_routes(routes)
    app.cleanup_ctx.append(reputation_service_ctx)
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
    logger.info(
        "Waiting up to `%s` for current connections to close...",
        RAY_ON_GOLEM_SHUTDOWN_CONNECTIONS_TIMEOUT,
    )


async def yagna_service_ctx(app: web.Application) -> None:
    yagna_service: YagnaService = app["yagna_service"]

    await yagna_service.start()

    yield

    await yagna_service.stop()


async def golem_service_ctx(app: web.Application) -> None:
    golem_service: GolemService = app["golem_service"]
    yagna_service: YagnaService = app["yagna_service"]

    await golem_service.init(yagna_appkey=yagna_service.yagna_appkey)

    yield

    await golem_service.stop()


async def ray_service_ctx(app: web.Application) -> None:
    ray_service: RayService = app["ray_service"]

    yield

    await ray_service.stop()


async def reputation_service_ctx(app: web.Application) -> None:
    reputation_service: ReputationService = app["reputation_service"]

    await reputation_service.start()

    update_tasks = [
        create_task_with_logging(
            ReputationUpdater(network).update(),
            trace_id=f"reputation_service_ctx-{network}",
        )
        for network in ["polygon", "mumbai", "goerli", "holesky"]
    ]

    yield

    await ensure_cancelled_many(update_tasks)
    await reputation_service.stop()


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
@with_datadir
def start(port: int, registry_stats: bool, datadir: Optional[Path] = None):
    from ray_on_golem.client import RayOnGolemClient
    from ray_on_golem.ctl import RayOnGolemCtl
    from ray_on_golem.ctl.log import RayOnGolemCtlConsoleLogger

    ctl = RayOnGolemCtl(
        client=RayOnGolemClient(port),
        output_logger=RayOnGolemCtlConsoleLogger(),
        datadir=datadir,
    )
    ctl.start_webserver(
        registry_stats=registry_stats,
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
    help="Port on which Ray on Golem's webserver is listening.",
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="Force the shutdown even if the webserver contains active nodes.",
)
@click.option(
    "-k",
    "--kill",
    is_flag=True,
    help="Kill the process if it fails to exit after shutdown.",
)
@with_datadir
def stop(port, force, kill, datadir):
    from ray_on_golem.client import RayOnGolemClient
    from ray_on_golem.ctl import RayOnGolemCtl
    from ray_on_golem.ctl.log import RayOnGolemCtlConsoleLogger, RayOnGolemCtlError
    from ray_on_golem.server.models import ShutdownState

    ctl = RayOnGolemCtl(
        client=RayOnGolemClient(port), output_logger=RayOnGolemCtlConsoleLogger(), datadir=datadir
    )

    shutdown_state = ctl.stop_webserver(
        ignore_self_shutdown=True, shutdown_delay=timedelta(seconds=0)
    )

    if shutdown_state == ShutdownState.CLUSTER_NOT_EMPTY:
        if force or click.confirm("Force the shutdown?"):
            ctl.stop_webserver(
                ignore_self_shutdown=True, force_shutdown=True, shutdown_delay=timedelta(seconds=0)
            )
        else:
            click.echo("Shutdown cancelled.")
            return

    try:
        ctl.wait_for_stop(starting_up=False)
    except RayOnGolemCtlError as e:
        click.echo(e)

    process = ctl.get_process_info()
    if not process:
        click.echo("Shutdown completed.")
        return

    if not (kill or click.confirm("Terminate the webserver process?")):
        click.echo("The webserver is still running...")
        return

    try:
        process.kill()
    except psutil.NoSuchProcess:
        pass
    ctl.clear_pid()
    click.echo("Process terminated.")


@click.command(
    help="Show webserver status.",
    context_settings={"show_default": True},
)
@click.option(
    "-p",
    "--port",
    type=int,
    default=4578,
    help="Port on which Ray on Golem's webserver is listening.",
)
@with_datadir
def status(port, datadir):
    from ray_on_golem.client import RayOnGolemClient
    from ray_on_golem.ctl import RayOnGolemCtl
    from ray_on_golem.ctl.log import RayOnGolemCtlConsoleLogger

    client = RayOnGolemClient(port)
    server_status = client.get_webserver_status()

    if not colorful.terminal.detect_color_support(os.environ):
        colorful.disable()

    if not server_status:
        print(f"The webserver doesn't seem to be listening on {client.base_url}.")
        ctl = RayOnGolemCtl(
            client=client, output_logger=RayOnGolemCtlConsoleLogger(), datadir=datadir
        )
        process = ctl.get_process_info()
        if process:
            print(f"However, the webserver seems to be running under pid: {process.pid}.")
            print("You may use the `ray-on-golem stop` command to terminate it.")

        return

    print(colorful.cyan(f"Ray On Golem webserver {server_status.version}"))
    print(
        "   Listening on:    {url}\n"
        "   Status:          {status}\n"
        "   Data directory:  {datadir}\n"
        "   Server warnings:\n\t{warnings}\n".format(
            url=client.base_url,
            status="Shutting down" if server_status.shutting_down else "Running",
            datadir=server_status.datadir,
            warnings=colorful.orange("\n\t".join(server_status.server_warnings)),
        )
    )


if __name__ == "__main__":
    main()
