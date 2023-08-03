from http import HTTPStatus

from aiohttp import web


class RayException(Exception):
    def __init__(self, message: str, additional_message=None):
        if additional_message:
            message += "\n" + additional_message
        super().__init__(message)
        self.message = message


class NodeNotFound(RayException):
    def __init__(self, additional_message):
        super().__init__(message="Node with given id not found",
                         additional_message=additional_message)


class NodesNotFound(RayException):
    def __init__(self, additional_message):
        super().__init__(message="Nodes with given ids not found",
                         additional_message=additional_message)


class CreateActivitiesTimeout(RayException):
    def __init__(self):
        super().__init__(message="Creating activities timeout reached")


class DestroyActivityError(RayException):
    def __init__(self, additional_message=None):
        super().__init__(message="Can't destroy activity",
                         additional_message=additional_message)


class NodesCountExceeded(RayException):

    def __init__(self):
        super().__init__(message="Can't create more nodes")


class CheckYagnaStatusError(RayException):
    def __init__(self):
        super().__init__(message="Can't check yagna status")


class ManifestNotFound(RayException):
    def __init__(self):
        super().__init__(message="Manifest file not found")


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
    except RayException as ex:
        message = ex.message
        status_code = HTTPStatus.BAD_REQUEST

    return web.json_response({"error": message}, status=status_code)
