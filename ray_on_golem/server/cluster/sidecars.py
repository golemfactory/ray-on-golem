import asyncio
import logging
from abc import ABC, abstractmethod
from asyncio.subprocess import Process
from datetime import timedelta
from typing import TYPE_CHECKING, Optional

from golem.utils.asyncio import create_task_with_logging, ensure_cancelled
from golem.utils.logging import get_trace_id_name

from ray_on_golem.exceptions import RayOnGolemError
from ray_on_golem.server.mixins import WarningMessagesMixin
from ray_on_golem.utils import run_subprocess

if TYPE_CHECKING:
    from ray_on_golem.server.cluster.cluster import Cluster
    from ray_on_golem.server.cluster.nodes import ClusterNode, HeadClusterNode  # noqa

logger = logging.getLogger(__name__)


class ClusterNodeSidecar(WarningMessagesMixin, ABC):
    @abstractmethod
    async def start(self) -> None:
        ...

    @abstractmethod
    async def stop(self) -> None:
        ...

    @abstractmethod
    async def is_running(self) -> bool:
        ...


class MonitorClusterNodeSidecar(ClusterNodeSidecar, ABC):
    name = "monitor"

    def __init__(self, node: "ClusterNode", cluster: "Cluster"):
        super().__init__()

        self._node = node
        self._cluster = cluster

        self._monitor_task: Optional[asyncio.Task] = None

    @abstractmethod
    async def _monitor(self) -> None:
        ...

    async def start(self) -> None:
        if self.is_running():
            logger.info(f"Not starting `%s` node {self.name}, as it's already running", self._node)
            return

        logger.info(f"Starting `%s` node {self.name}...", self._node)

        self._monitor_task = create_task_with_logging(
            self._monitor(), trace_id=get_trace_id_name(self, self._get_monitor_task_name())
        )

        logger.info(f"Starting `%s` node {self.name} done", self._node)

    async def stop(self) -> None:
        if not self.is_running():
            logger.info(f"Not stopping `%s` node {self.name}, as it's already stopped", self._node)
            return

        logger.info(f"Stopping `%s` node {self.name}...", self._node)

        await ensure_cancelled(self._monitor_task)
        self._monitor_task = None

        logger.info(f"Stopping `%s` node {self.name} done", self._node)

    def is_running(self) -> bool:
        return self._monitor_task and not self._monitor_task.done()

    def _get_monitor_task_name(self) -> str:
        return "{}-{}".format(self._node, self.name.replace(" ", "-"))


class ActivityStateMonitorClusterNodeSidecar(MonitorClusterNodeSidecar):
    name = "activity monitor"

    def __init__(self, node: "ClusterNode", cluster: "Cluster", check_interval: timedelta) -> None:
        super().__init__(node, cluster)

        self._check_interval = check_interval

    async def _monitor(self) -> None:
        from ray_on_golem.server.cluster.nodes import HeadClusterNode

        while True:
            activity_state = await self._node.activity.get_state()

            if (
                "Terminated" in activity_state.state
                or "Unresponsive" in activity_state.state
                or activity_state.error_message is not None
            ):
                logger.warning(
                    "`%s` node activity is no longer accessible, terminating", self._node
                )

                provider_desc = await self._node.get_provider_desc(self._node.activity)

                if isinstance(self._node, HeadClusterNode):
                    self.add_warning_message(
                        f"Terminating whole cluster as Head({self._node.node_id}) {provider_desc}"
                        " activity is no longer accessible"
                    )
                    create_task_with_logging(self._cluster.stop())
                else:
                    self.add_warning_message(
                        f"Terminating node as Worker({self._node.node_id}) as {provider_desc}"
                        " activity is no longer accessible"
                    )
                    create_task_with_logging(self._node.stop())

                return

            await asyncio.sleep(self._check_interval.total_seconds())


class SshStateMonitorClusterNodeSidecar(MonitorClusterNodeSidecar):
    name = "ssh monitor"

    def __init__(
        self,
        node: "ClusterNode",
        cluster: "Cluster",
        check_interval: timedelta,
        retry_interval: timedelta,
        max_fail_count: int,
    ) -> None:
        super().__init__(node, cluster)

        self._check_interval = check_interval
        self._retry_interval = retry_interval
        self._max_fail_count = max_fail_count

    async def _monitor(self) -> None:
        from ray_on_golem.server.cluster.nodes import HeadClusterNode

        fails_count = 0
        while True:
            try:
                await self._node.verify_ssh_connection()
            except RayOnGolemError:
                fails_count += 1
                if self._max_fail_count <= fails_count:
                    logger.warning("`%s` node ssh is no longer accessible, terminating", self._node)

                    provider_desc = await self._node.get_provider_desc(self._node.activity)

                    if isinstance(self._node, HeadClusterNode):
                        self.add_warning_message(
                            f"Terminating whole cluster as Head({self._node.node_id}) {provider_desc}"
                            " ssh is no longer accessible"
                        )
                        create_task_with_logging(self._cluster.stop())
                    else:
                        self.add_warning_message(
                            f"Terminating node as Worker({self._node.node_id}) as {provider_desc}"
                            " ssh is no longer accessible"
                        )
                        create_task_with_logging(self._node.stop())

                    return

                logger.debug(
                    "`%s` node ssh stopped working, restarting ssh server",
                    self._node,
                    exc_info=True,
                )
                await self._node.restart_ssh_server()
                await asyncio.sleep(self._retry_interval.total_seconds())
                continue

            await asyncio.sleep(self._check_interval.total_seconds())


class HeadNodeToWebserverTunnelClusterNodeSidecar(ClusterNodeSidecar):
    def __init__(self, head_node: "HeadClusterNode") -> None:
        super().__init__()

        self._head_node = head_node

        self._tunnel_process: Optional[Process] = None
        self._early_exit_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        if self.is_running():
            logger.info(
                "Not starting `%s` node to webserver tunnel, as it's already running",
                self._head_node,
            )
            return

        logger.info("Starting `%s` node to webserver tunnel...", self._head_node)

        self._tunnel_process = await run_subprocess(
            "ssh",
            "-N",
            "-R",
            f"*:{self._head_node.webserver_port}:127.0.0.1:{self._head_node.webserver_port}",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            "-o",
            f"ProxyCommand={self._head_node.ssh_proxy_command}",
            "-i",
            str(self._head_node.ssh_private_key_path),
            f"{self._head_node.ssh_user}@{str(self._head_node.internal_ip)}",
        )
        self._early_exit_task = create_task_with_logging(
            self._on_tunnel_early_exit(), trace_id=get_trace_id_name(self, "early-exit")
        )

        logger.info("Starting `%s` node to webserver tunnel done", self._head_node)

    async def stop(self) -> None:
        if not self.is_running():
            logger.info(
                "Not stopping `%s` node to webserver tunnel, as it's not running", self._head_node
            )
            return

        logger.info("Stopping `%s` node to webserver tunnel...", self._head_node)

        await ensure_cancelled(self._early_exit_task)
        self._early_exit_task = None

        self._tunnel_process.terminate()
        await self._tunnel_process.wait()

        self._tunnel_process = None

        logger.info("Stopping `%s` node to webserver tunnel done", self._head_node)

    def is_running(self) -> bool:
        return self._tunnel_process and self._tunnel_process.returncode is None

    async def _on_tunnel_early_exit(self) -> None:
        await self._tunnel_process.communicate()

        logger.warning(f"`%s` node to webserver tunnel exited prematurely!", self._head_node)
