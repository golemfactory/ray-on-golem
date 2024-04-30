from golem.resources import Activity
from ray.autoscaler.tags import NODE_KIND_HEAD, TAG_RAY_NODE_KIND

from ray_on_golem.server.models import Tags


def is_head_node(tags: Tags) -> bool:
    """Check if given Ray tags are related to Ray head node."""

    return tags.get(TAG_RAY_NODE_KIND) == NODE_KIND_HEAD


async def get_provider_desc(activity: Activity) -> str:
    """Return the provider description for given activity."""

    proposal = activity.agreement.proposal
    return f"{await proposal.get_provider_name()} ({await proposal.get_provider_id()})"
