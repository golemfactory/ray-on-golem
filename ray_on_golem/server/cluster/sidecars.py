import asyncio
import logging
from abc import ABC, abstractmethod
from asyncio.subprocess import Process
from datetime import timedelta
from typing import TYPE_CHECKING, Callable, Optional

from golem.utils.asyncio import create_task_with_logging, ensure_cancelled
from golem.utils.asyncio.tasks import resolve_maybe_awaitable
from golem.utils.logging import get_trace_id_name
from golem.utils.typing import MaybeAwaitable

from ray_on_golem.exceptions import RayOnGolemError
from ray_on_golem.server.mixins import WarningMessagesMixin
from ray_on_golem.utils import run_subprocess

if TYPE_CHECKING:
    from ray_on_golem.server.cluster.nodes import ClusterNode

logger = logging.getLogger(__name__)


class ClusterNodeSidecar(WarningMessagesMixin, ABC):
    """Base class for companion business logic that runs in relation to the node."""

    def __init__(self, *, node: "ClusterNode", **kwargs) -> None:
        super().__init__(**kwargs)

        self._node = node

    @abstractmethod
    async def start(self) -> None:
        """Start the sidecar and its internal state."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the sidecar and cleanup its internal state."""
        ...

    @abstractmethod
    async def is_running(self) -> bool:
        """Check if the sidecar is running."""
        ...


class MonitorClusterNodeSidecar(ClusterNodeSidecar, ABC):
    """Base class for companion business logic that monitor the state of the related node."""

    name = "<unnamed>"

    def __init__(
        self,
        *,
        on_monitor_failed_func: Callable[
            ["MonitorClusterNodeSidecar", "ClusterNode"], MaybeAwaitable[None]
        ],
        **kwargs,
    ):
        super().__init__(**kwargs)

        self._on_monitor_check_failed_func = on_monitor_failed_func

        self._monitor_task: Optional[asyncio.Task] = None

    def __str__(self) -> str:
        return f"{self.name} monitor"

    @abstractmethod
    async def _monitor(self) -> None:
        ...

    async def start(self) -> None:
        """Start the sidecar and its internal state."""

        if self.is_running():
            logger.info(f"Not starting `%s` node {self}, as it's already running", self._node)
            return

        logger.info(f"Starting `%s` node {self}...", self._node)

        self._monitor_task = create_task_with_logging(
            self._monitor(), trace_id=get_trace_id_name(self, self._get_monitor_task_name())
        )

        logger.info(f"Starting `%s` node {self} done", self._node)

    async def stop(self) -> None:
        """Stop the sidecar and cleanup its internal state."""

        if not self.is_running():
            logger.info(f"Not stopping `%s` node {self}, as it's already stopped", self._node)
            return

        logger.info(f"Stopping `%s` node {self}...", self._node)

        await ensure_cancelled(self._monitor_task)
        self._monitor_task = None

        logger.info(f"Stopping `%s` node {self} done", self._node)

    def is_running(self) -> bool:
        """Check if the sidecar is running."""

        return self._monitor_task and not self._monitor_task.done()

    def _get_monitor_task_name(self) -> str:
        return "{}-{}".format(self._node, str(self).replace(" ", "-"))


class ActivityStateMonitorClusterNodeSidecar(MonitorClusterNodeSidecar):
    """Sidecar that monitor the activity state of the related node.

    External callback will be called if the activity enters non-working state.
    """

    name = "activity"

    def __init__(self, *, check_interval: timedelta, **kwargs) -> None:
        super().__init__(**kwargs)

        self._check_interval = check_interval

    async def _monitor(self) -> None:
        while True:
            activity_state = await self._node.activity.get_state()

            if (
                "Terminated" in activity_state.state
                or "Unresponsive" in activity_state.state
                or activity_state.error_message is not None
            ):
                await resolve_maybe_awaitable(self._on_monitor_check_failed_func(self, self._node))

                return

            await asyncio.sleep(self._check_interval.total_seconds())


class SshStateMonitorClusterNodeSidecar(MonitorClusterNodeSidecar):
    """Sidecar that monitor the ssh state of the related node.

    External callback will be called if the ssh connection check will fail.
    """

    name = "ssh"

    def __init__(
        self,
        *,
        check_interval: timedelta,
        retry_interval: timedelta,
        max_fail_count: int,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self._check_interval = check_interval
        self._retry_interval = retry_interval
        self._max_fail_count = max_fail_count

    async def _monitor(self) -> None:
        fails_count = 0
        while True:
            try:
                await self._node.verify_ssh_connection()
            except RayOnGolemError:
                fails_count += 1
                if self._max_fail_count <= fails_count:
                    await resolve_maybe_awaitable(
                        self._on_monitor_check_failed_func(self, self._node)
                    )

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


class PortTunnelClusterNodeSidecar(ClusterNodeSidecar):
    """Sidecar that runs ssh tunnel from the related node to local machine.

    Warning will be generated if tunnel exists prematurely.
    """

    def __init__(
        self,
        *,
        local_port: int,
        remote_port: Optional[int] = None,
        reverse: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self._local_port = local_port
        self._remote_port = local_port if remote_port is None else remote_port
        self._reverse = reverse

        self._tunnel_process: Optional[Process] = None
        self._early_exit_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the sidecar and its internal state."""

        if self.is_running():
            logger.info(
                "Not starting `%s` node `%s` tunnel, as it's already running",
                self._node,
                self._get_tunel_type(),
            )
            return

        logger.info("Starting `%s` node `%s` tunnel...", self._node, self._get_tunel_type())

        self._tunnel_process = await run_subprocess(
            "ssh",
            "-N",
            "-R" if self._reverse else "-L",
            f"*:{self._remote_port}:127.0.0.1:{self._local_port}",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            "-o",
            f"ProxyCommand={self._node.ssh_proxy_command}",
            "-i",
            str(self._node.ssh_private_key_path),
            f"{self._node.ssh_user}@{str(self._node.internal_ip)}",
        )
        self._early_exit_task = create_task_with_logging(
            self._on_tunnel_early_exit(),
            trace_id=get_trace_id_name(self, f"{self._get_tunel_type()}-early-exit"),
        )

        logger.info("Starting `%s` node `%s` tunnel done", self._node, self._get_tunel_type())

    async def stop(self) -> None:
        """Stop the sidecar and cleanup its internal state."""

        if not self.is_running():
            logger.info(
                "Not stopping `%s` node `%s`, as it's not running",
                self._node,
                self._get_tunel_type(),
            )
            return

        logger.info("Stopping `%s` node `%s` tunnel...", self._node, self._get_tunel_type())

        await ensure_cancelled(self._early_exit_task)
        self._early_exit_task = None

        self._tunnel_process.terminate()
        await self._tunnel_process.wait()

        self._tunnel_process = None

        logger.info("Stopping `%s` node `%s` tunnel done", self._node, self._get_tunel_type())

    def is_running(self) -> bool:
        """Check if the sidecar is running."""

        return self._tunnel_process and self._tunnel_process.returncode is None

    async def _on_tunnel_early_exit(self) -> None:
        await self._tunnel_process.communicate()

        logger.warning(
            f"`%s` node %s exited prematurely!",
            self._node,
            self._get_tunel_type(),
        )

    def _get_tunel_type(self) -> str:
        return ":{}{}:{}".format(
            self._local_port, "<-" if self._reverse else "->", self._remote_port
        )
