from typing import Any

from ray.autoscaler._private.aws.node_provider import (
    AWSNodeProvider,
)  # testing purposes
from ray.autoscaler.node_provider import NodeProvider


class GolemNodeProvider(NodeProvider):
    def create_node(
        self,
        node_config: dict[str, Any],
        tags: dict[str, str],
        count: int,
    ) -> dict[str, Any] | None:
        """Creates a number of nodes within the namespace.

        Optionally returns a mapping from created node ids to node metadata.

        Optionally may throw a
        ray.autoscaler.node_launch_exception.NodeLaunchException which the
        autoscaler may use to provide additional functionality such as
        observability.

        """
        raise NotImplementedError
