from ray_on_golem.exceptions import RayOnGolemError


class RayOnGolemClientError(RayOnGolemError):

    def __init__(self, msg = "", error_code = None):
        super().__init__(msg)
        self.error_code = error_code

    def __str__(self):
        error_code = f"{self.error_code}: " if self.error_code else ""
        return f"{error_code}{super().__str__()}"


class RayOnGolemClientValidationError(RayOnGolemClientError):
    pass
