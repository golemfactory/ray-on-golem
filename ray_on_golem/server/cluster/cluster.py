import asyncio
import logging
from collections import defaultdict
from functools import partial
from typing import (
    Callable,
    DefaultDict,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
)

from golem.managers import PaymentManager
from golem.utils.asyncio import create_task_with_logging
from golem.utils.asyncio.tasks import resolve_maybe_awaitable
from golem.utils.logging import get_trace_id_name
from golem.utils.typing import MaybeAwaitable
from ray.autoscaler.tags import NODE_KIND_HEAD, TAG_RAY_NODE_KIND, TAG_RAY_USER_NODE_TYPE

from ray_on_golem.server import utils
from ray_on_golem.server.cluster.nodes import ClusterNode, HeadClusterNode, WorkerClusterNode
from ray_on_golem.server.mixins import WarningMessagesMixin
from ray_on_golem.server.models import (
    NodeConfigData,
    NodeId,
    NodeState,
    ProviderParametersData,
    Tags,
)
from ray_on_golem.server.services import (
    DriverListAllocationPaymentManager,
    GolemService,
    ManagerStack,
)
from ray_on_golem.server.settings import RAY_ON_GOLEM_PRIORITY_AGREEMENT_TIMEOUT

StackHash = str

logger = logging.getLogger(__name__)


class Cluster(WarningMessagesMixin):
    """Top-level element that is responsible for maintaining all components for single Ray \
    cluster."""

    def __init__(
        self,
        golem_service: GolemService,
        webserver_port: int,
        name: str,
        provider_parameters: ProviderParametersData,
        on_stop: Optional[Callable[["Cluster"], MaybeAwaitable[None]]] = None,
    ) -> None:
        super().__init__()

        self._golem_service = golem_service
        self._name = name
        self._provider_parameters = provider_parameters
        self._webserver_port = webserver_port
        self._on_stop = on_stop

        self._manager_stacks: Dict[StackHash, ManagerStack] = {}
        self._manager_stacks_locks: DefaultDict[StackHash, asyncio.Semaphore] = defaultdict(
            asyncio.Semaphore
        )
        self._nodes: Dict[NodeId, ClusterNode] = {}
        self._nodes_id_counter = 0
        self._payment_manager: PaymentManager = DriverListAllocationPaymentManager(
            self._golem_service.golem,
            budget=self._provider_parameters.total_budget,
            network=self._provider_parameters.payment_network,
            driver=self._provider_parameters.payment_driver,
        )

        self._state: NodeState = NodeState.terminated

    def __str__(self) -> str:
        return self._name

    @property
    def nodes(self) -> Mapping[str, ClusterNode]:
        """Read-only map of named nodes.

        Nodes will persist in the collection even after they are terminated."""
        return self._nodes

    def get_warning_messages(self) -> List[str]:
        """Get read-only collection of warnings both from the cluster and its nodes."""

        warnings = list(super().get_warning_messages())

        for node in self._nodes.values():
            warnings.extend(node.get_warning_messages())

        return warnings

    async def start(self) -> None:
        """Start the cluster and its internal state."""

        if self._state in (NodeState.pending, NodeState.running):
            logger.info("Not starting `%s` cluster as it's already running or starting", self)
            return

        logger.info("Starting `%s` cluster...", self)

        self._state = NodeState.pending

        await self._payment_manager.start()

        self._state = NodeState.running

        logger.info("Starting `%s` cluster done", self)

    async def stop(self, call_events: bool = True) -> None:
        """Stop the cluster."""

        if self._state in (NodeState.terminating, NodeState.terminated):
            logger.info("Not stopping `%s` cluster as it's already stopped or stopping", self)
            return

        logger.info("Stopping `%s` cluster...", self)

        self._state = NodeState.terminating

        await asyncio.gather(*[node.stop(call_events=False) for node in self._nodes.values()])

        await asyncio.gather(*[stack.stop() for stack in self._manager_stacks.values()])

        await self._payment_manager.stop()

        self._state = NodeState.terminated
        self._nodes.clear()
        self._nodes_id_counter = 0
        self._manager_stacks.clear()
        self._manager_stacks_locks.clear()

        if self._on_stop and call_events:
            create_task_with_logging(
                resolve_maybe_awaitable(self._on_stop(self)),
                trace_id=get_trace_id_name(self, "on-stop"),
            )

        logger.info("Stopping `%s` cluster done", self)

    def is_running(self) -> bool:
        return self._state != NodeState.terminated

    def get_non_terminated_nodes(self) -> Sequence["ClusterNode"]:
        """Return cluster nodes that are running on the cluster."""

        return [
            node
            for node in self._nodes.values()
            if node.state not in [NodeState.terminating, NodeState.terminated]
        ]

    async def request_nodes(
        self, node_config: NodeConfigData, count: int, tags: Tags
    ) -> Iterable[NodeId]:
        """Create new nodes and schedule their start."""

        is_head_node = utils.is_head_node(tags)
        worker_type = "head" if is_head_node else "worker"
        node_type = self._get_node_type(tags)

        logger.info(
            "Requesting `%s` %s node(s) of type `%s`...",
            count,
            worker_type,
            node_type,
        )

        manager_stack, priority_manager_stack = await self._prepare_manager_stacks(node_config)
        cluster_node_class = self._get_cluster_node_class(is_head_node)

        created_node_ids = []
        for _ in range(count):
            node_id = self._get_new_node_id()
            created_node_ids.append(node_id)

            self._nodes[node_id] = node = cluster_node_class(
                cluster=self,
                golem_service=self._golem_service,
                manager_stack=manager_stack,
                priority_manager_stack=priority_manager_stack,
                priority_agreement_timeout=RAY_ON_GOLEM_PRIORITY_AGREEMENT_TIMEOUT,
                on_stop=self._on_node_stop,
                node_id=node_id,
                tags=tags,
                node_config=node_config,
                ssh_private_key_path=self._provider_parameters.ssh_private_key,
                ssh_public_key_path=self._provider_parameters.ssh_private_key.with_suffix(".pub"),
                ssh_user=self._provider_parameters.ssh_user,
            )

            node.schedule_start()

        logger.info(
            "Requesting `%s` %s node(s) of type `%s` done",
            count,
            worker_type,
            node_type,
        )
        logger.debug(f"{node_config=}")

        return created_node_ids

    def _get_new_node_id(self) -> NodeId:
        node_id = f"node{self._nodes_id_counter}"
        self._nodes_id_counter += 1
        return node_id

    def _get_cluster_node_class(self, is_head_node: bool) -> Type[ClusterNode]:
        return (
            partial(
                HeadClusterNode,
                webserver_port=self._webserver_port,
                ray_gcs_expose_port=self._provider_parameters.ray_gcs_expose_port,
            )
            if is_head_node
            else WorkerClusterNode
        )

    @staticmethod
    def _is_head_node(tags: Tags) -> bool:
        return tags.get(TAG_RAY_NODE_KIND) == NODE_KIND_HEAD

    @staticmethod
    def _get_node_type(tags: Tags) -> str:
        return tags.get(TAG_RAY_USER_NODE_TYPE)

    async def _prepare_manager_stacks(
        self, node_config: NodeConfigData
    ) -> Tuple[ManagerStack, Optional[ManagerStack]]:
        priority_manager_stack = (
            await self._get_or_create_manager_stack(node_config, node_config.priority_subnet_tag)
            if node_config.priority_subnet_tag
            else None
        )
        manager_stack = await self._get_or_create_manager_stack(node_config, node_config.subnet_tag)

        return manager_stack, priority_manager_stack

    async def _get_or_create_manager_stack(
        self,
        node_config: NodeConfigData,
        subnet_tag: str,
    ) -> ManagerStack:
        stack_hash = node_config.get_hash()

        async with self._manager_stacks_locks[stack_hash]:
            stack = self._manager_stacks.get(stack_hash)

            if not stack:
                logger.info("Creating manager stack `%s`...", stack_hash)

                self._manager_stacks[stack_hash] = stack = await ManagerStack.create(
                    node_config=node_config,
                    subnet_tag=subnet_tag,
                    payment_network=self._provider_parameters.payment_network,
                    payment_manager=self._payment_manager,
                    demand_config_helper=self._golem_service.demand_config_helper,
                    golem=self._golem_service.golem,
                )
                await stack.start()

                logger.info("Creating new manager stack `%s` done", stack_hash)

            return stack

    async def _remove_manager_stack(self, stack_hash: StackHash) -> None:
        logger.info("Removing stack `%s`...", stack_hash)

        async with self._manager_stacks_locks[stack_hash]:
            await self._manager_stacks[stack_hash].stop()

            del self._manager_stacks[stack_hash]

        # remove lock only if no one else is waiting for it
        if not self._manager_stacks_locks[stack_hash].locked():
            del self._manager_stacks_locks[stack_hash]

        logger.info("Removing stack `%s` done", stack_hash)

    async def _on_node_stop(self, node: ClusterNode) -> None:
        non_terminated_nodes = self.get_non_terminated_nodes()
        if not non_terminated_nodes:
            logger.debug("No more nodes running on the cluster, cluster will stop")

            await self.stop()

            return

        if isinstance(node, HeadClusterNode):
            logger.debug("Head node is not running, cluster will stop")

            await self.stop()

            return

        manager_stack_stop_coros = []

        # TODO: Consider moving this logic directly to manager stack with more event-based approach
        for manager_stack in node.manager_stacks:
            if any(manager_stack in n.manager_stacks for n in self.get_non_terminated_nodes()):
                continue

            logger.debug(
                "No more nodes running on the `%s` manager stack, manager stack will stop",
                manager_stack,
            )

            manager_stack_stop_coros.append(manager_stack.stop())

        if manager_stack_stop_coros:
            await asyncio.gather(*manager_stack_stop_coros)
        else:
            logger.debug(
                "Cluster and its manager stacks have some nodes still running, nothing to stop"
            )
