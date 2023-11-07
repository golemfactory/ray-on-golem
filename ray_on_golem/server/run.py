import argparse
import asyncio
import logging
import logging.config
from contextlib import asynccontextmanager

import yaml
from aiohttp import web

from ray_on_golem.server.middlewares import error_middleware, trace_id_middleware
from ray_on_golem.server.services import GolemService, RayService, YagnaService
from ray_on_golem.server.services.golem.network_stats import GolemNetworkStatsService
from ray_on_golem.server.settings import (
    LOGGING_CONFIG,
    RAY_ON_GOLEM_SHUTDOWN_DEADLINE,
    TMP_PATH,
    WEBSOCAT_PATH,
    YAGNA_PATH,
)
from ray_on_golem.server.views import routes

logger = logging.getLogger(__name__)


def parse_sys_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ray on Golem's webserver.")
    subparsers = parser.add_subparsers(dest="command")

    webserver_parser = subparsers.add_parser("webserver")
    webserver_parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=4578,
        help="port for Ray on Golem's webserver to listen on, default: %(default)s",
    )
    webserver_parser.add_argument(
        "--self-shutdown",
        action="store_true",
        help="flag to enable self-shutdown after last node termination, default: %(default)s",
    )
    webserver_parser.add_argument(
        "--registry-stats",
        action="store_true",
        help="flag to enable collection of Golem Registry stats about resolved images, default: %(default)s",
    )
    webserver_parser.add_argument(
        "--no-registry-stats",
        action="store_false",
        dest="registry_stats",
    )
    webserver_parser.add_argument("--no-self-shutdown", action="store_false", dest="self_shutdown")
    webserver_parser.set_defaults(self_shutdown=False, registry_stats=True)

    stats_parser = subparsers.add_parser("stats")
    stats_parser.add_argument(
        "CLUSTER_CONFIG_FILE",
        type=argparse.FileType("r"),
        help="Cluster config yaml",
    )
    stats_parser.add_argument(
        "-t",
        "--run-time",
        type=int,
        dest="run_time",
        default=5,
        help="For how long in minutes to gather stats, default: %(default)s",
    )
    stats_parser.add_argument(
        "--enable-logging",
        action="store_true",
        dest="enable_logging",
        help="flag to enable logging, default: %(default)s",
    )

    return parser.parse_args()


def prepare_tmp_dir():
    try:
        TMP_PATH.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass


def create_application(port: int, self_shutdown: bool, registry_stats: bool) -> web.Application:
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
    )

    app["golem_service"] = GolemService(
        websocat_path=WEBSOCAT_PATH,
        registry_stats=app["registry_stats"],
    )

    app["ray_service"] = RayService(
        ray_on_golem_port=port,
        golem_service=app["golem_service"],
        tmp_path=TMP_PATH,
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


@asynccontextmanager
async def golem_network_stats_service(registry_stats: bool) -> GolemNetworkStatsService:
    golem_network_stats_service: GolemNetworkStatsService = GolemNetworkStatsService(registry_stats)
    yagna_service = YagnaService(
        yagna_path=YAGNA_PATH,
    )

    await yagna_service.init()
    await golem_network_stats_service.init(yagna_appkey=yagna_service.yagna_appkey)

    yield golem_network_stats_service

    await golem_network_stats_service.shutdown()
    await yagna_service.shutdown()


async def stats_main(args: argparse.Namespace):
    with args.CLUSTER_CONFIG_FILE as file:
        config = yaml.safe_load(file.read())
    provider_config = config["provider"]
    async with golem_network_stats_service(
        provider_config["enable_registry_stats"]
    ) as stats_service:
        await stats_service.run(provider_config["parameters"], args.run_time)


def main():
    prepare_tmp_dir()
    args = parse_sys_args()

    if args.command == "webserver":
        logging.config.dictConfig(LOGGING_CONFIG)
        app = create_application(args.port, args.self_shutdown, args.registry_stats)

        logger.info(
            "Starting server... {}".format(", ".join(f"{k}={v}" for k, v in args.__dict__.items()))
        )

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

    elif args.command == "stats":
        if args.enable_logging:
            logging.config.dictConfig(LOGGING_CONFIG)
        asyncio.run(stats_main(args))


if __name__ == "__main__":
    main()
