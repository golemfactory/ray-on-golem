import base64
import logging

import dotenv
from aiohttp import web
from aiohttp_session import setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from cryptography import fernet

from golem_ray.server.logger import get_logger
from golem_ray.server.middlewares import error_middleware
from golem_ray.server.routes.golem import routes as nodes_routes
from golem_ray.server.utils.yagna import YagnaManager
from golem_ray.server.views.golem import GolemManager

dotenv.load_dotenv()
logger = get_logger()


async def golem_engine(app):
    yagna_manager = YagnaManager()
    await yagna_manager.run()
    app['yagna'] = yagna_manager

    golem_manager = GolemManager()
    app['golem'] = golem_manager

    async with golem_manager.golem:
        await golem_manager.init()
        yield  # before yield called on startup, after yield called on cleanup
        await golem_manager.shutdown()
        await yagna_manager.shutdown()


def main():
    logger = logging.getLogger('aiohttp')
    app = web.Application(middlewares=[error_middleware])

    fernet_key = fernet.Fernet.generate_key()
    secret_key = base64.urlsafe_b64decode(fernet_key)
    setup(app, EncryptedCookieStorage(secret_key))

    nodes_sub_app = web.Application(middlewares=[error_middleware])
    nodes_sub_app.router.add_routes(nodes_routes)
    nodes_sub_app.cleanup_ctx.append(golem_engine)
    app.add_subapp('/golem/', nodes_sub_app)

    logger.info('Server started')
    web.run_app(app)


if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR)
    main()
