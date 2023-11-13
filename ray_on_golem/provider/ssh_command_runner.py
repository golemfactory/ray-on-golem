from ray.autoscaler._private.command_runner import SSHCommandRunner as BaseSshCommandRunner
from ray_on_golem.server.services.utils import get_ssh_command


class SSHCommandRunner(BaseSshCommandRunner):
    def remote_shell_command_str(self):
        return get_ssh_command(
            ip=self.ssh_ip,
            ssh_proxy_command=self.ssh_proxy_command,
            ssh_user=self.ssh_user,
            ssh_private_key_path=self.ssh_private_key
        )
