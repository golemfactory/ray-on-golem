from aiohttp import web

from golem_ray.server.consts import StatusCode


class ExceptionMessages:
    NODE_NOT_FOUND = 'Node with given id not found'


class GolemRayException(Exception):
    def __init__(self, message: str, status_code: StatusCode):
        self.message = message
        self.status_code: int = status_code.value
        super().__init__(self.message, self.status_code)


class RayException(Exception):
    NODE_NOT_FOUND = 'Node with given id not found'
    NODES_NOT_FOUND = 'Nodes with given ids not found'
    DESTROY_ACTIVITY_ERROR = "Can't destroy activity"
    NODES_COUNT_EXCEEDED = "Can't create more nodes"

    def __init__(self, message="An error occured", additional_message=None):
        if additional_message:
            message += "\n" + additional_message
        super().__init__(message)
        self.message = message


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
