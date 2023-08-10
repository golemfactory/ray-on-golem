import hashlib
import shlex
import subprocess
from getpass import getuser
from typing import Dict

from ray.autoscaler._private.cli_logger import cli_logger, cf
from ray.autoscaler._private.command_runner import SSHCommandRunner, SSHOptions, HASH_MAX_LENGTH, is_using_login_shells, \
    _with_environment_variables, _with_interactive


class SSHProviderCommandRunner(SSHCommandRunner):

    def __init__(
            self,
            log_prefix,
            node_id,
            provider,
            auth_config,
            cluster_name,
            process_runner,
            use_internal_ip,
    ):
        ssh_control_hash = hashlib.md5(cluster_name.encode()).hexdigest()
        ssh_user_hash = hashlib.md5(getuser().encode()).hexdigest()
        ssh_control_path = "/tmp/ray_ssh_{}/{}".format(
            ssh_user_hash[:HASH_MAX_LENGTH], ssh_control_hash[:HASH_MAX_LENGTH]
        )

        self.cluster_name = cluster_name
        self.log_prefix = log_prefix
        self.process_runner = process_runner
        self.node_id = node_id
        self.use_internal_ip = use_internal_ip
        self.provider = provider
        self.ssh_private_key = auth_config.get("ssh_private_key")
        self.ssh_user = auth_config["ssh_user"]
        self.ssh_control_path = ssh_control_path
        self.ssh_ip = None
        self.ssh_port = None
        self.ssh_proxy_command = auth_config.get("ssh_proxy_command", None)
        self.ssh_options = SSHOptions(
            self.ssh_private_key,
            self.ssh_control_path,
            ProxyCommand=self.ssh_proxy_command,
        )

    def set_ssh_port(self, ssh_port: int):
        self.ssh_ip = '127.0.0.1'
        self.ssh_port = ssh_port

    def run(
            self,
            cmd,
            timeout=120,
            exit_on_fail=False,
            port_forward=None,
            with_output=False,
            environment_variables: Dict[str, object] = None,
            run_env="auto",  # Unused argument.
            ssh_options_override_ssh_key="",
            shutdown_after_run=False,
            silent=False,
    ):
        if shutdown_after_run:
            cmd += "; sudo shutdown -h now"

        if ssh_options_override_ssh_key:
            if self.ssh_proxy_command:
                ssh_options = SSHOptions(
                    ssh_options_override_ssh_key, ProxyCommand=self.ssh_proxy_command
                )
            else:
                ssh_options = SSHOptions(ssh_options_override_ssh_key)
        else:
            ssh_options = self.ssh_options

        assert isinstance(
            ssh_options, SSHOptions
        ), "ssh_options must be of type SSHOptions, got {}".format(type(ssh_options))

        self._set_ssh_ip_if_required()

        if is_using_login_shells():
            ssh = ["ssh", "-tt"]
        else:
            ssh = ["ssh"]

        final_cmd = (
                ssh
                + ssh_options.to_ssh_options_list(timeout=timeout)
                + ["{}@{}".format(self.ssh_user, self.ssh_ip)]
                + ['-p'] + [f"{self.ssh_port}"]
        )
        if cmd:
            if environment_variables:
                cmd = _with_environment_variables(cmd, environment_variables)
            if is_using_login_shells():
                final_cmd += _with_interactive(cmd)
            else:
                final_cmd += [cmd]
        else:
            # We do this because `-o ControlMaster` causes the `-N` flag to
            # still create an interactive shell in some ssh versions.
            final_cmd.append("while true; do sleep 86400; done")

        cli_logger.verbose("Running `{}`", cf.bold(cmd))
        with cli_logger.indented():
            cli_logger.very_verbose(
                "Full command is `{}`", cf.bold(" ".join(final_cmd))
            )

        if cli_logger.verbosity > 0:
            with cli_logger.indented():
                return self._run_helper(
                    final_cmd, with_output, exit_on_fail, silent=silent
                )
        else:
            return self._run_helper(final_cmd, with_output, exit_on_fail, silent=silent)


    def run_rsync_up(self, source, target, options=None):
        self._set_ssh_ip_if_required()
        options = options or {}

        command = ["rsync"]
        command += [
            "--rsh",
            subprocess.list2cmdline(
                ["ssh"] + ["-p"] + [f"{self.ssh_port}"] + self.ssh_options.to_ssh_options_list(timeout=120)
            ),
        ]
        command += ["-avz"]
        command += self._create_rsync_filter_args(options=options)
        command += [source, "{}@{}:{}".format(self.ssh_user, self.ssh_ip, target)]
        cli_logger.verbose("Running `{}`", cf.bold(" ".join(command)))
        self._run_helper(command, silent=False)