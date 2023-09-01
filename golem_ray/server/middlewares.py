from aiohttp import web

from golem_ray.server.exceptions import GolemRayServerError


@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
    except web.HTTPException as e:
        message = e.reason
        status_code = e.status_code
    except GolemRayServerError as e:
        message = e.message
        status_code = 400
    else:
        if response.status != 404:
            return response

        message = "not found"
        status_code = 404

    return web.json_response({"error": message}, status=status_code)
