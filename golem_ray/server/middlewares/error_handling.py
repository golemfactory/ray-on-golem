from http import HTTPStatus

from aiohttp import web


class GolemRayException(Exception):
    message = None

    def __init__(self, additional_message=None):
        if additional_message:
            self.message += "\n" + additional_message
        super().__init__(self.message)


class NodeNotFound(GolemRayException):
    message = "Node with given id not found"


class NodesNotFound(GolemRayException):
    message = "Nodes with given ids not found"

    def __init__(self, additional_message):
        super().__init__(additional_message=additional_message)


class CreateActivitiesTimeout(GolemRayException):
    message = "Creating activities timeout reached"


class DestroyActivityError(GolemRayException):
    message = "Can't destroy activity"


class NodesCountExceeded(GolemRayException):
    message = "Can't create more nodes"


class CheckYagnaStatusError(GolemRayException):
    message = "Can't check yagna status"


class ManifestNotFound(GolemRayException):
    message = "Manifest file not found"


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
    except GolemRayException as ex:
        message = ex.message
        status_code = HTTPStatus.BAD_REQUEST

    return web.json_response({"error": message}, status=status_code)
