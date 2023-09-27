import uuid

from aiohttp import web
from golem.utils.logging import trace_id_var

from ray_on_golem.server.exceptions import RayOnGolemServerError


@web.middleware
async def trace_id_middleware(request, handler):
    trace_id_var.set(f"webserver-request-{str(uuid.uuid4())[:5]}")

    return await handler(request)


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
