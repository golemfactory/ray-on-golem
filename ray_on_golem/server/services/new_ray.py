import asyncio
import logging
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import DefaultDict, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

from ray_on_golem.server.cluster import Cluster
from ray_on_golem.server.cluster.nodes import ClusterNode
from ray_on_golem.server.exceptions import ClusterNotFound, NodeNotFound
from ray_on_golem.server.mixins import WarningMessagesMixin
from ray_on_golem.server.models import (
    NodeConfigData,
    NodeData,
    NodeId,
    NodeState,
    ProviderParametersData,
    Tags,
)
from ray_on_golem.server.services.new_golem import GolemService
from ray_on_golem.utils import are_dicts_equal, get_default_ssh_key_name, run_subprocess_output

logger = logging.getLogger(__name__)


class RayService(WarningMessagesMixin):
    def __init__(self, golem_service: GolemService, datadir: Path, webserver_port: int) -> None:
        super().__init__()

        self._golem_service = golem_service
        self._datadir = datadir
        self._webserver_port = webserver_port

        self._clusters: Dict[str, Cluster] = {}
        self._clusters_locks: DefaultDict[str, asyncio.Semaphore] = defaultdict(asyncio.Semaphore)

    @property
    def datadir(self) -> Path:
        return self._datadir

    def get_warning_messages(self) -> Sequence[str]:
        warnings = list(super().get_warning_messages())

        for cluster_name, cluster in self._clusters.items():
            warnings.extend(
                [f"[{cluster_name}] {warning}" for warning in cluster.get_warning_messages()]
            )

        return warnings

    async def stop(self):
        logger.info("Stopping RayService...")

        for cluster in self._clusters.values():
            await cluster.stop()

        self._clusters.clear()
        self._clusters_locks.clear()

        logger.info("Stopping RayService...")

    async def request_nodes(
        self,
        cluster_name: str,
        provider_config: ProviderParametersData,
        node_config: NodeConfigData,
        count: int,
        tags: Tags,
    ) -> Iterable[NodeId]:
        cluster = await self._get_or_create_cluster(cluster_name, provider_config)

        return await cluster.request_nodes(node_config, count, tags)

    async def terminate_node(self, cluster_name: str, node_id: NodeId) -> Dict[NodeId, Dict]:
        async with self._with_cluster_node_context(
            cluster_name, node_id
        ) as node:  # type: ClusterNode
            node_data = node.get_data()

            await node.stop()

            return {node_id: node_data.dict()}

    async def get_cluster_data(self, cluster_name: str) -> Dict[NodeId, NodeData]:
        async with self._with_cluster_context(cluster_name) as cluster:  # type: Cluster
            return {node.node_id: node.get_data() for node in cluster.nodes.values()}

    async def get_non_terminated_nodes_ids(
        self, cluster_name: str, tags_to_match: Optional[Dict[str, str]] = None
    ) -> List[NodeId]:
        try:
            async with self._with_cluster_context(cluster_name) as cluster:
                nodes = self._get_non_terminated_nodes_ids(cluster)

            if tags_to_match is None:
                return [node.node_id for node in nodes]

            return [node.node_id for node in nodes if are_dicts_equal(node.tags, tags_to_match)]
        except ClusterNotFound:
            return []

    def _get_non_terminated_nodes_ids(self, cluster: Cluster) -> List[ClusterNode]:
        return [
            node
            for node in cluster.nodes.values()
            if node.state not in [NodeState.terminating, NodeState.terminated]
        ]

    async def is_node_running(self, cluster_name: str, node_id: NodeId) -> bool:
        async with self._with_cluster_node_context(
            cluster_name, node_id
        ) as node:  # type: ClusterNode
            return node.state == NodeState.running

    async def is_node_terminated(self, cluster_name: str, node_id: NodeId) -> bool:
        async with self._with_cluster_node_context(
            cluster_name, node_id
        ) as node:  # type: ClusterNode
            return node.state in [NodeState.terminating, NodeState.terminated]

    async def get_node_tags(self, cluster_name: str, node_id: NodeId) -> Dict:
        async with self._with_cluster_node_context(
            cluster_name, node_id
        ) as node:  # type: ClusterNode
            return node.tags

    async def get_node_internal_ip(self, cluster_name: str, node_id: NodeId) -> Optional[str]:
        async with self._with_cluster_node_context(
            cluster_name, node_id
        ) as node:  # type: ClusterNode
            return node.internal_ip

    async def get_ssh_proxy_command(self, cluster_name: str, node_id: NodeId) -> Optional[str]:
        async with self._with_cluster_node_context(
            cluster_name, node_id
        ) as node:  # type: ClusterNode
            return node.ssh_proxy_command

    async def set_node_tags(self, cluster_name: str, node_id: NodeId, tags: Tags) -> None:
        async with self._with_cluster_node_context(
            cluster_name, node_id
        ) as node:  # type: ClusterNode
            node.tags.update(tags)

    async def get_or_create_default_ssh_key(self, cluster_name: str) -> Tuple[str, str]:
        ssh_key_path = self._datadir / get_default_ssh_key_name(cluster_name)
        ssk_public_key_path = ssh_key_path.with_suffix(".pub")

        if not ssh_key_path.exists():
            logger.info(f"Creating default ssh key for `{cluster_name}`...")

            ssh_key_path.parent.mkdir(parents=True, exist_ok=True)

            # FIXME: Use cryptography module instead of subprocess
            await run_subprocess_output(
                "ssh-keygen", "-t", "rsa", "-b", "4096", "-N", "", "-f", str(ssh_key_path)
            )

            logger.info(
                f"Creating default ssh key for `{cluster_name}` done with path `{ssh_key_path}`"
            )

        # TODO: async file handling
        with ssh_key_path.open("r") as priv_f, ssk_public_key_path.open("r") as pub_f:
            return str(priv_f.read()), str(pub_f.read())

    def is_any_node_running(self) -> bool:
        for cluster in self._clusters.values():
            if self._get_non_terminated_nodes_ids(cluster):
                return True

        return False

    async def _get_or_create_cluster(
        self, cluster_name: str, provider_parameters: ProviderParametersData
    ) -> Cluster:
        async with self._clusters_locks[cluster_name]:
            cluster = self._clusters.get(cluster_name)

            if not cluster:
                logger.info("Creating cluster `%s`...", cluster_name)

                self._clusters[cluster_name] = cluster = Cluster(
                    self._golem_service,
                    self._webserver_port,
                    cluster_name,
                    provider_parameters,
                )

                await cluster.start()

                logger.info("Creating cluster `%s` done", cluster_name)

            return cluster

    @asynccontextmanager
    async def _with_cluster_context(self, cluster_name: str) -> Iterator[Cluster]:
        try:
            async with self._clusters_locks[cluster_name]:
                cluster = self._clusters.get(cluster_name)

                if not cluster:
                    raise ClusterNotFound

                yield cluster
        except ClusterNotFound:
            # cleanup dangling lock when the cluster was not found
            # and nobody else is waiting for the lock (thanks for asyncio.Semaphore)
            if not self._clusters_locks[cluster_name].locked():
                del self._clusters_locks[cluster_name]

            raise

    @asynccontextmanager
    async def _with_cluster_node_context(
        self, cluster_name: str, node_id: NodeId
    ) -> Iterator[ClusterNode]:
        async with self._with_cluster_context(cluster_name) as cluster:
            try:
                yield cluster.nodes[node_id]
            except KeyError:
                raise NodeNotFound
