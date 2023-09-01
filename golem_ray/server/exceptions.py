from golem_ray.exceptions import GolemRayError


class GolemRayServerError(GolemRayError):
    message = None

    def __init__(self, additional_message=None):
        if additional_message:
            self.message += "\n" + additional_message

        super().__init__(self.message)


class NodeNotFound(GolemRayServerError):
    message = "Node with given id not found"


class NodesNotFound(GolemRayServerError):
    message = "Nodes with given ids not found"


class CreateActivitiesTimeout(GolemRayServerError):
    message = "Creating activities timeout reached"


class DestroyActivityError(GolemRayServerError):
    message = "Can't destroy activity"


class NodesCountExceeded(GolemRayServerError):
    message = "Can't create more nodes"


class CheckYagnaStatusError(GolemRayServerError):
    message = "Can't check yagna status"


class ManifestNotFound(GolemRayServerError):
    message = "Manifest file not found"


class RegistryRequestError(GolemRayServerError):
    pass
