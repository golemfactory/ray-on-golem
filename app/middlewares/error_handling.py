from aiohttp import web

from app.consts import StatusCode


class GolemRayException(Exception):
    def __init__(self, message: str, status_code: StatusCode):
        self.message = message
        self.status_code: int = status_code.value
        super().__init__(self.message, self.status_code)


@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        if response.status != 404:
            return response
        message = response.message
        status_code = StatusCode.OK.value
    except web.HTTPException as ex:
        if ex.status != 404:
            raise
        message = ex.reason
        status_code = ex.status_code
    except GolemRayException as ex:
        message = ex.message
        status_code = ex.status_code

    return web.json_response({"error": message}, status=status_code)
