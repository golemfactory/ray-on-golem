import subprocess

from ray.autoscaler._private.cli_logger import cf, cli_logger
from ray.autoscaler._private.command_runner import SSHCommandRunner as BaseSshCommandRunner
from ray.autoscaler._private.command_runner import SSHOptions, is_rsync_silent

from ray_on_golem.server.settings import SSH_SERVER_ALIVE_COUNT_MAX, SSH_SERVER_ALIVE_INTERVAL
from ray_on_golem.utils import get_ssh_command


class SSHCommandRunner(BaseSshCommandRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ssh_options = SSHOptions(
            self.ssh_private_key,
            self.ssh_control_path,
            ProxyCommand=self.ssh_proxy_command,
            ServerAliveInterval=SSH_SERVER_ALIVE_INTERVAL,
            ServerAliveCountMax=SSH_SERVER_ALIVE_COUNT_MAX,
        )

    def remote_shell_command_str(self):
        return get_ssh_command(
            ip=self.ssh_ip,
            ssh_proxy_command=self.ssh_proxy_command,
            ssh_user=self.ssh_user,
            ssh_private_key_path=self.ssh_private_key,
        )

    def run_rsync_up(self, source, target, options=None):
        self._set_ssh_ip_if_required()
        options = options or {}

        command = ["rsync"]
        command += [
            "--rsh",
            subprocess.list2cmdline(["ssh"] + self.ssh_options.to_ssh_options_list(timeout=120)),
        ]
        command += ["-avz"]
        command += ["--no-o"]
        command += ["--no-g"]
        command += self._create_rsync_filter_args(options=options)
        command += [source, "{}@{}:{}".format(self.ssh_user, self.ssh_ip, target)]
        cli_logger.verbose("Running `{}`", cf.bold(" ".join(command)))
        self._run_helper(command, silent=is_rsync_silent())

    def run_rsync_down(self, source, target, options=None):
        self._set_ssh_ip_if_required()

        command = ["rsync"]
        command += [
            "--rsh",
            subprocess.list2cmdline(["ssh"] + self.ssh_options.to_ssh_options_list(timeout=120)),
        ]
        command += ["-avz"]
        command += ["--no-o"]
        command += ["--no-g"]
        command += self._create_rsync_filter_args(options=options)
        command += ["{}@{}:{}".format(self.ssh_user, self.ssh_ip, source), target]
        cli_logger.verbose("Running `{}`", cf.bold(" ".join(command)))
        self._run_helper(command, silent=is_rsync_silent())
