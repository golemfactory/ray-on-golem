from enum import Enum


class StatusCode(Enum):
    OK = 200
    CREATED = 201
    NOT_FOUND = 404
    BAD_REQUEST = 400
    SERVER_ERROR = 500
    DELETED = 204


def is_valid_status_code(status_code: int):
    return status_code in StatusCode.__members__.values()
