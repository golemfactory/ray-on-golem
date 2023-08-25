from ray.autoscaler._private.command_runner import SSHCommandRunner as BaseSshCommandRunner


class SSHCommandRunner(BaseSshCommandRunner):
    def remote_shell_command_str(self):
        ssh_str = f'ssh -o UserKnownHostsFile=/dev/null -o ProxyCommand="{self.ssh_proxy_command}"'

        if self.ssh_private_key:
            ssh_str += f" -i {self.ssh_private_key}"
        
        ssh_str += f' {self.ssh_user}@{self.ssh_ip}\n'
        
        return ssh_str
