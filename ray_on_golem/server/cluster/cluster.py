import asyncio
import logging
from collections import defaultdict
from functools import partial
from typing import DefaultDict, Dict, Iterable, List, Mapping, Tuple, Type, Union

from golem.managers import PaymentManager
from ray.autoscaler.tags import NODE_KIND_HEAD, TAG_RAY_NODE_KIND, TAG_RAY_USER_NODE_TYPE

from ray_on_golem.server.cluster.nodes import ClusterNode, HeadClusterNode, WorkerClusterNode
from ray_on_golem.server.mixins import WarningMessagesMixin
from ray_on_golem.server.models import (
    NodeConfigData,
    NodeId,
    NodeState,
    ProviderParametersData,
    Tags,
)
from ray_on_golem.server.services.golem.golem import DeviceListAllocationPaymentManager
from ray_on_golem.server.services.golem.helpers.demand_config import DemandConfigHelper
from ray_on_golem.server.services.golem.manager_stack import ManagerStack
from ray_on_golem.server.services.new_golem import GolemService

IsHeadNode = bool
NodeType = str
StackKey = Tuple[NodeType, IsHeadNode]

logger = logging.getLogger(__name__)


class Cluster(WarningMessagesMixin):
    def __init__(
        self,
        golem_service: GolemService,
        name: str,
        provider_parameters: ProviderParametersData,
        webserver_port: int,
        demand_config_helper: DemandConfigHelper,
    ) -> None:
        super().__init__()

        self._golem_service = golem_service
        self._name = name
        self._provider_parameters = provider_parameters
        self._webserver_port = webserver_port
        self._demand_config_helper = demand_config_helper

        self._manager_stacks: Dict[StackKey, ManagerStack] = {}
        self._manager_stacks_locks: DefaultDict[StackKey, asyncio.Semaphore] = defaultdict(
            asyncio.Semaphore
        )
        self._nodes: Dict[NodeId, ClusterNode] = {}
        self._nodes_id_counter = 0
        self._payment_manager: PaymentManager = DeviceListAllocationPaymentManager(
            self._golem_service.golem,
            budget=self._provider_parameters.total_budget,
            network=self._provider_parameters.payment_network,
            driver=self._provider_parameters.payment_driver,
        )

        self._state: NodeState = NodeState.terminated

    @property
    def nodes(self) -> Mapping[str, ClusterNode]:
        return self._nodes

    def get_warning_messages(self) -> List[str]:
        warnings = super().get_warning_messages()

        for node in self._nodes.values():
            warnings.extend(node.get_warning_messages())

        return warnings

    async def start(self) -> None:
        if self._state in (NodeState.pending, NodeState.running):
            logger.info("Not starting `%s` cluster as it's already running or starting", self._name)
            return

        logger.info("Starting `%s` cluster...", self._name)

        self._state = NodeState.pending

        await self._payment_manager.start()

        self._state = NodeState.running

        logger.info("Starting `%s` cluster done", self._name)

    async def stop(self) -> None:
        if self._state in (NodeState.terminating, NodeState.terminated):
            logger.info("Not stopping `%s` cluster as it's already stopped or stopping", self._name)
            return

        logger.info("Stopping `%s` cluster...", self._name)

        self._state = NodeState.terminating

        for node in self._nodes.values():
            await node.stop()

        self._nodes.clear()
        self._nodes_id_counter = 0

        for stack in self._manager_stacks.values():
            await stack.stop()

        self._manager_stacks.clear()
        self._manager_stacks_locks.clear()

        await self._payment_manager.stop()

        self._state = NodeState.terminated

        logger.info("Stopping `%s` cluster done", self._name)

    async def request_nodes(
        self, node_config: NodeConfigData, count: int, tags: Tags
    ) -> Iterable[NodeId]:
        is_head_node = self._is_head_node(tags)
        worker_type = "head" if is_head_node else "worker"
        node_type = self._get_node_type(tags)

        logger.info(
            "Requesting `%s` nodes of `%s` type as %s node...", count, node_type, worker_type
        )

        manager_stack = await self._get_or_create_manager_stack(
            node_config,
            node_type,
            is_head_node,
        )

        created_node_ids = []
        for _ in range(count):
            node_id = self._get_new_node_id()
            created_node_ids.append(node_id)

            cluster_node_class = self._get_cluster_node_class(is_head_node)

            node = cluster_node_class(
                cluster=self,
                golem_service=self._golem_service,
                manager_stack=manager_stack,
                node_id=node_id,
                tags=tags,
                node_config=node_config,
                ssh_private_key_path=self._provider_parameters.ssh_private_key,
                ssh_public_key_path=self._provider_parameters.ssh_private_key.with_suffix(".pub"),
                ssh_user=self._provider_parameters.ssh_user,
            )

            self._nodes[node_id] = node

            node.start()

        logger.info(
            "Requesting `%s` nodes of `%s` type as %s node done", count, node_type, worker_type
        )
        logger.debug(f"{node_config=}")

        return created_node_ids

    def _get_new_node_id(self) -> NodeId:
        node_id = f"node{self._nodes_id_counter}"
        self._nodes_id_counter += 1
        return node_id

    def _get_cluster_node_class(
        self, is_head_node: bool
    ) -> Type[Union[HeadClusterNode, WorkerClusterNode]]:
        return (
            partial(
                HeadClusterNode,
                webserver_port=self._webserver_port,
            )
            if is_head_node
            else WorkerClusterNode
        )

    def _is_head_node(self, tags: Tags) -> bool:
        return tags.get(TAG_RAY_NODE_KIND) == NODE_KIND_HEAD

    @staticmethod
    def _get_node_type(tags: Tags) -> str:
        return tags.get(TAG_RAY_USER_NODE_TYPE)

    async def _get_or_create_manager_stack(
        self,
        node_config: NodeConfigData,
        node_type: NodeType,
        is_head_node: IsHeadNode,
    ) -> ManagerStack:
        stack_key = (node_type, is_head_node)

        async with self._manager_stacks_locks[stack_key]:
            stack = self._manager_stacks.get(stack_key)

            if not stack:
                logger.info("Creating manager stack `%s`...", stack_key)

                self._manager_stacks[stack_key] = stack = await ManagerStack.create(
                    node_config=node_config,
                    payment_network=self._provider_parameters.payment_network,
                    is_head_node=is_head_node,
                    payment_manager=self._payment_manager,
                    demand_config_helper=self._demand_config_helper,
                    golem=self._golem_service.golem,
                )
                await stack.start()

                logger.info("Creating new manager stack `%s` done", stack_key)

            return stack

    async def _remove_manager_stack(self, stack_key: StackKey) -> None:
        logger.info(f"Removing stack `%s`...", stack_key)

        async with self._manager_stacks_locks[stack_key]:
            await self._manager_stacks[stack_key].stop()

            del self._manager_stacks[stack_key]

        # remove lock only if no one else is waiting for it
        if not self._manager_stacks_locks[stack_key].locked():
            del self._manager_stacks_locks[stack_key]

        logger.info(f"Removing stack `%s` done", stack_key)
