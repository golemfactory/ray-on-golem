import logging
import os
from logging.config import dictConfig

import dotenv
from aiohttp import web

from golem_ray.server.consts.config import DICT_CONFIG, ROOT_DIR
from golem_ray.server.middlewares import error_middleware
from golem_ray.server.services.golem import GolemService
from golem_ray.server.services.ray import RayService
from golem_ray.server.services.yagna import YagnaManager
from golem_ray.server.views.golem_ray import routes as nodes_routes

logging.config.dictConfig(DICT_CONFIG)
logger = logging.getLogger(__name__)

dotenv.load_dotenv(ROOT_DIR.joinpath('.env'))


def get_envs():
    yagna_path = os.getenv('YAGNA_PATH', 'yagna')
    gcs_reverse_tunnel_port = os.getenv('GCS_REVERSE_TUNNEL_PORT', 3009)

    return yagna_path, gcs_reverse_tunnel_port


async def golem_engine(app):
    yagna_path, gcs_reverse_tunnel_port = get_envs()
    yagna_manager = YagnaManager(yagna_path=yagna_path)
    await yagna_manager.run()
    app['yagna'] = yagna_manager

    golem_service = GolemService(gcs_reverse_tunnel_port=gcs_reverse_tunnel_port)
    app['golem'] = golem_service

    ray_service = RayService(golem_service)
    app['ray'] = ray_service

    async with golem_service.golem:
        await golem_service.init()
        yield  # before yield called on startup, after yield called on cleanup
        await golem_service.shutdown()
        await yagna_manager.shutdown()


def main():
    app = web.Application(middlewares=[error_middleware])

    app.add_routes(nodes_routes)
    app.cleanup_ctx.append(golem_engine)
    logger.info('Server started')
    web.run_app(app)


if __name__ == '__main__':
    main()
