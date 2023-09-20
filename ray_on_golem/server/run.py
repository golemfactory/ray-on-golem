import argparse
import logging
import logging.config
from functools import partial

from aiohttp import web

from ray_on_golem.server.middlewares import error_middleware
from ray_on_golem.server.services import GolemService, RayService, YagnaService
from ray_on_golem.server.settings import (
    LOGGING_CONFIG,
    RAY_ON_GOLEM_SERVER_PORT,
    TMP_PATH,
    WEBSOCAT_PATH,
    YAGNA_PATH,
)
from ray_on_golem.server.views import routes

logger = logging.getLogger(__name__)


def parse_sys_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ray on Golem's webserver.")
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=4578,
        help="port for Ray on Golem's webserver to listen on, default: %(default)s",
    )
    parser.add_argument(
        "--self-shutdown",
        action="store_true",
        default=False,
        help="flag to enable self shutdown after last node termination, default: %(default)s",
    )
    return parser.parse_args()


def prepare_tmp_dir():
    try:
        TMP_PATH.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass


async def print_hello(app: web.Application, port: int) -> None:
    logger.info(f"Server started on port {port}")


def create_application(port: int, self_shutdown: bool) -> web.Application:
    app = web.Application(middlewares=[error_middleware])

    app["self_shutdown"] = self_shutdown

    app["yagna_service"] = YagnaService(
        yagna_path=YAGNA_PATH,
    )

    app["golem_service"] = GolemService(
        ray_on_golem_port=RAY_ON_GOLEM_SERVER_PORT,
        websocat_path=WEBSOCAT_PATH,
    )

    app["ray_service"] = RayService(
        golem_service=app["golem_service"],
        tmp_path=TMP_PATH,
    )

    app.add_routes(routes)
    app.cleanup_ctx.append(yagna_service_ctx)
    app.cleanup_ctx.append(golem_service_ctx)
    app.cleanup_ctx.append(ray_service_ctx)
    app.on_startup.append(partial(print_hello, port=port))

    return app


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


def main():
    logging.config.dictConfig(LOGGING_CONFIG)

    args = parse_sys_args()
    prepare_tmp_dir()

    app = create_application(args.port, args.self_shutdown)
    web.run_app(app, port=args.port, print=None)

    logger.info(f"Server stopped, bye!")


if __name__ == "__main__":
    main()
