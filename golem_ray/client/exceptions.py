from typing import Type

import requests
from pydantic.main import BaseModel


class GolemRayClientException(Exception):
    def __init__(self, message: str,
                 response: requests.Response):
        error_message = f"{message}: \n" \
                        f"request url: {response.url}\n" \
                        f"response status_code: {response.status_code}, text: {response.text}"

        super().__init__(error_message)


class GolemRayClientValidationException(Exception):
    def __init__(self, message: str, response: requests.Response, expected: Type[BaseModel]):
        error_message = f"{message}: \n" \
                        f"{response.json() = }\n" \
                        f"expected {expected}"
        super().__init__(error_message)