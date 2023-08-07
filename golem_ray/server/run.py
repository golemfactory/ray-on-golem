import logging
import os
from logging.config import dictConfig

from aiohttp import web

from config import YAGNA_PATH, GCS_REVERSE_TUNNEL_PORT, LOGGER_DICT_CONFIG, PROXY_IP
from middlewares import error_middleware
from services import GolemService, RayService, YagnaManager
from views import routes as nodes_routes

logger = logging.getLogger()


async def golem_engine(app):
    try:
        os.mkdir('/tmp/golem')
    except OSError:
        pass
    yagna_manager = YagnaManager(yagna_path=YAGNA_PATH)
    await yagna_manager.run()
    app['yagna'] = yagna_manager

    golem_service = GolemService(gcs_reverse_tunnel_port=GCS_REVERSE_TUNNEL_PORT,
                                 yagna_appkey=yagna_manager.yagna_appkey,
                                 proxy_ip=PROXY_IP)
    app['golem'] = golem_service

    ray_service = RayService(golem_service)
    app['ray'] = ray_service

    async with golem_service.golem:
        await golem_service.init()
        yield  # before yield called on startup, after yield called on cleanup
        await golem_service.shutdown()
        await yagna_manager.shutdown()


def main():
    logging.config.dictConfig(LOGGER_DICT_CONFIG)
    app = web.Application(middlewares=[error_middleware])

    app.add_routes(nodes_routes)
    app.cleanup_ctx.append(golem_engine)
    logger.info('Server started')
    web.run_app(app)


if __name__ == '__main__':
    main()
