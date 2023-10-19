from ray_on_golem.exceptions import RayOnGolemError


class RayOnGolemServerError(RayOnGolemError):
    message = None

    def __init__(self, additional_message=None):
        if additional_message:
            self.message += "\n" + additional_message

        super().__init__(self.message)


class NodeNotFound(RayOnGolemServerError):
    message = "Node with given id not found"


class NodesNotFound(RayOnGolemServerError):
    message = "Nodes with given ids not found"


class CreateActivitiesTimeout(RayOnGolemServerError):
    message = "Creating activities timeout reached"


class DestroyActivityError(RayOnGolemServerError):
    message = "Can't destroy activity"


class CheckYagnaStatusError(RayOnGolemServerError):
    message = "Can't check Yagna status"


class ManifestNotFound(RayOnGolemServerError):
    message = "Manifest file not found"


class RegistryRequestError(RayOnGolemServerError):
    message = "Golem Registry request failed"
