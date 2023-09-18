from aiohttp import web

from ray_on_golem.server.exceptions import RayOnGolemServerError


@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
    except web.HTTPException as e:
        message = e.reason
        status_code = e.status_code
    except RayOnGolemServerError as e:
        message = e.message
        status_code = 400
    else:
        if response.status != 404:
            return response

        message = "not found"
        status_code = 404

    return web.json_response({"error": message}, status=status_code)
