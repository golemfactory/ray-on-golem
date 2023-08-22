from golem_ray.exceptions import GolemRayError


class GolemRayClientError(GolemRayError):
    pass

class GolemRayClientValidationError(GolemRayClientError):
    pass
