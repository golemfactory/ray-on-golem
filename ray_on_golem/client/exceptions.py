from ray_on_golem.exceptions import RayOnGolemError


class RayOnGolemClientError(RayOnGolemError):
    pass


class RayOnGolemClientValidationError(RayOnGolemClientError):
    pass
