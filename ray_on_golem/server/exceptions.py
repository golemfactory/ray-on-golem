from ray_on_golem.exceptions import RayOnGolemError


class RayOnGolemServerError(RayOnGolemError):
    message = None

    def __init__(self, additional_message=None):
        if additional_message:
            self.message += "\n" + additional_message

        super().__init__(self.message)


class ClusterNotFound(RayOnGolemServerError):
    message = "Cluster with given name not found"


class NodeNotFound(RayOnGolemServerError):
    message = "Node with given id not found"


class RegistryRequestError(RayOnGolemServerError):
    message = "Golem Registry request failed"
