import logging

import dotenv
from aiohttp import web

from golem_ray.server.logger import get_logger
from golem_ray.server.middlewares import error_middleware
from golem_ray.server.views.golem_ray import routes as nodes_routes
from golem_ray.server.services.ray import RayService
from golem_ray.server.services.yagna import YagnaManager
from golem_ray.server.services.golem import GolemService

dotenv.load_dotenv()
logger = get_logger()

# TODO: Fix logger
async def golem_engine(app):
    yagna_manager = YagnaManager()
    await yagna_manager.run()
    app['yagna'] = yagna_manager

    golem_service = GolemService()
    app['golem'] = golem_service

    ray_service = RayService(golem_service)
    app['ray'] = ray_service

    async with golem_service.golem:
        await golem_service.init()
        yield  # before yield called on startup, after yield called on cleanup
        await golem_service.shutdown()
        await yagna_manager.shutdown()


def main():
    logger = logging.getLogger('aiohttp') # add logging.config.dictConfig (search Default_config)
    app = web.Application(middlewares=[error_middleware])

    app.add_routes(nodes_routes)
    app.cleanup_ctx.append(golem_engine)
    logger.info('Server started')
    web.run_app(app)


if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR)
    main()
