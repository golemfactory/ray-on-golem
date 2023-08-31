import hashlib
from getpass import getuser

from ray.autoscaler._private.command_runner import SSHCommandRunner as BaseSshCommandRunner
from ray.autoscaler._private.command_runner import SSHOptions


class SSHCommandRunner(BaseSshCommandRunner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        auth_config = kwargs["auth_config"]
        self._provider = kwargs["provider"]
        print(self._provider.ray_head_ip)

        if not auth_config.get("ssh_private_key"):
            ssh_user_hash = hashlib.md5(getuser().encode()).hexdigest()[:10]

            self.ssh_control_path = "/tmp/golem-ray-ssh/golem_ray_{}".format(ssh_user_hash)
            self.ssh_private_key = "/tmp/golem-ray-ssh/golem_ray_rsa_{}".format(ssh_user_hash)
            self.ssh_options = SSHOptions(
                self.ssh_private_key,
                self.ssh_control_path,
                ProxyCommand=self.ssh_proxy_command,
            )

    def remote_shell_command_str(self):
        ssh_str = f'ssh -o UserKnownHostsFile=/dev/null -o ProxyCommand="{self.ssh_proxy_command}"'

        if self.ssh_private_key:
            ssh_str += f" -i {self.ssh_private_key}"

        ssh_str += f" {self.ssh_user}@{self.ssh_ip}\n"

        return ssh_str
