import argparse
import logging
import logging.config

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
        help="port for Ray on Golem's webserver to listen on, default: %(default)s",
        default=4578,
    )
    return parser.parse_args()


def prepare_tmp_dir():
    try:
        TMP_PATH.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass


async def print_hello(app: web.Application) -> None:
    logger.info("Server started")


def create_application() -> web.Application:
    app = web.Application(middlewares=[error_middleware])

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
    app.cleanup_ctx.append(ray_on_golem_ctx)
    app.on_startup.append(print_hello)

    return app


async def ray_on_golem_ctx(app: web.Application):
    yagna_service: YagnaService = app["yagna_service"]
    golem_service: GolemService = app["golem_service"]
    ray_service: RayService = app["ray_service"]

    await yagna_service.init()
    await golem_service.init(yagna_appkey=yagna_service.yagna_appkey)

    yield  # before yield called on startup, after yield called on cleanup

    await ray_service.shutdown()
    await golem_service.shutdown()
    await yagna_service.shutdown()


def main():
    logging.config.dictConfig(LOGGING_CONFIG)

    args = parse_sys_args()
    prepare_tmp_dir()

    app = create_application()
    web.run_app(app, port=args.port)


if __name__ == "__main__":
    main()
