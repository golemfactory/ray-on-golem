from types import ModuleType
from typing import Dict, List, Optional, Tuple

from ray.autoscaler.command_runner import CommandRunnerInterface

class InvalidLocalHeadArg(Exception):
    def __init__(self, arg, val):
        msg = f"LocalHeadCommandRunner doesn't work with {arg} = {val}"
        super().__init__(msg)

class LocalHeadCommandRunner(CommandRunnerInterface):
    def __init__(self, log_prefix: str, cluster_name: str, process_runner: ModuleType):
        #   NOTE: We have here a subset of things passed to 
        #   `NodeProvider.get_command_runner` that I think might be useful.
        #   Ommited arguments:
        #   *   node_id, as it's always the same node
        #   *   auth_config, as we're not authenticating
        #   *   use_internal_ip - I don't know what is this for
        #   *   docker_config - we decided to run only non-docker ray
        self.log_prefix = log_prefix
        self.cluster_name = cluster_name
        self.process_runner = process_runner

    def run(
        self,
        cmd: Optional[str] = None,
        timeout: int = 120,
        exit_on_fail: bool = False,
        port_forward: List[Tuple[int, int]] = None,
        with_output: bool = False,
        environment_variables: Optional[Dict[str, object]] = None,
        run_env: str = "auto",
        ssh_options_override_ssh_key: str = "",
        shutdown_after_run: bool = False,
    ) -> str:
        if shutdown_after_run:
            raise InvalidLocalHeadArg('shutdown_after_run', shutdown_after_run)

        bytes_output = self.process_runner.check_output(cmd, shell=True)
        return bytes_output.decode()
