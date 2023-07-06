import base64
import logging

from aiohttp import web
from aiohttp_session import setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from cryptography import fernet

from app.middlewares import error_middleware
from app.routes.golem import routes as nodes_routes
from app.utils.yagna import YagnaManager
from app.views.golem import GolemNodeProvider


async def golem_engine(app):
    yagna_manager = YagnaManager()
    golem_provider = GolemNodeProvider()
    app['golem'] = golem_provider
    app['yagna'] = yagna_manager

    async with golem_provider.golem:
        await golem_provider.init()
        yield  # before yield called on startup, after yield called on cleanup
        await golem_provider.shutdown()
        yagna_manager.shutdown()


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
