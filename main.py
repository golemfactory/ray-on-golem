import asyncio
import base64
import logging

from aiohttp import web
from aiohttp_session import setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from cryptography import fernet
from app.routes.golem import routes as nodes_routes
from app.routes.yagna import routes as yagna_routes
from app.middlewares import error_middleware


def main():
    logger = logging.getLogger('aiohttp')
    app = web.Application(middlewares=[error_middleware])

    fernet_key = fernet.Fernet.generate_key()
    secret_key = base64.urlsafe_b64decode(fernet_key)
    setup(app, EncryptedCookieStorage(secret_key))

    nodes_sub_app = web.Application()
    nodes_sub_app.router.add_routes(nodes_routes)
    app.add_subapp('/golem/', nodes_sub_app)

    yagna_sub_app = web.Application()
    yagna_sub_app.router.add_routes(yagna_routes)
    app.add_subapp('/yagna/', yagna_sub_app)

    logger.info('Server started')
    web.run_app(app)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main())
    # task = loop.create_task(main())
    # try:
    #     loop.run_until_complete(task)
    # except KeyboardInterrupt:
    #     task.cancel()
    #     try:
    #         loop.run_until_complete(task)
    #     except asyncio.CancelledError:
    #         pass
