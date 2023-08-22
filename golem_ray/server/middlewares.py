from http import HTTPStatus

from aiohttp import web

from exceptions import GolemRayServerError


@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
    except web.HTTPException as e:
        message = e.reason
        status_code = e.status_code
    except GolemRayServerError as e:
        message = e.message
        status_code = HTTPStatus.BAD_REQUEST
    else:
        if response.status != 404:
            return response
        
        message = 'not found'
        status_code = HTTPStatus.NOT_FOUND

    return web.json_response({"error": message}, status=status_code)
