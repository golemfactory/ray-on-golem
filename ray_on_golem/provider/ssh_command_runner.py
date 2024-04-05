from ray.autoscaler._private.command_runner import SSHCommandRunner as BaseSshCommandRunner
from ray.autoscaler._private.command_runner import SSHOptions

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
