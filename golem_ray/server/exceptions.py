class GolemRayServerException(Exception):
    message = None

    def __init__(self, additional_message=None):
        if additional_message:
            self.message += "\n" + additional_message
        super().__init__(self.message)


class NodeNotFound(GolemRayServerException):
    message = "Node with given id not found"


class NodesNotFound(GolemRayServerException):
    message = "Nodes with given ids not found"

    def __init__(self, additional_message):
        super().__init__(additional_message=additional_message)


class CreateActivitiesTimeout(GolemRayServerException):
    message = "Creating activities timeout reached"


class DestroyActivityError(GolemRayServerException):
    message = "Can't destroy activity"


class NodesCountExceeded(GolemRayServerException):
    message = "Can't create more nodes"


class CheckYagnaStatusError(GolemRayServerException):
    message = "Can't check yagna status"


class ManifestNotFound(GolemRayServerException):
    message = "Manifest file not found"
