from http import HTTPStatus

from aiohttp import web

from exceptions import GolemRayServerException


@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        if response.status != 404:
            return response
        message = 'not found'
        status_code = HTTPStatus.NOT_FOUND
    except web.HTTPException as ex:
        if ex.status != 404:
            raise
        message = ex.reason
        status_code = ex.status_code
    except GolemRayServerException as ex:
        message = ex.message
        status_code = HTTPStatus.BAD_REQUEST

    return web.json_response({"error": message}, status=status_code)
