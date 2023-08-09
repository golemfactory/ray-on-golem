from ray.autoscaler._private.command_runner import SSHCommandRunner


class SSHProviderCommandRunner(SSHCommandRunner):

    def set_ssh_proxy_command(self, proxy_command: str):
        self.ssh_proxy_command = proxy_command
