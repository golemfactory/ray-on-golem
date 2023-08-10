import shlex

from ray.autoscaler._private.cli_logger import cli_logger, cf
from ray.autoscaler._private.command_runner import SSHCommandRunner, SSHOptions


class SSHProviderCommandRunner(SSHCommandRunner):

    def set_proxy_command(self, proxy_command: str) -> None:
        self.ssh_proxy_command = proxy_command
        self.ssh_options = SSHOptions(ssh_key=None,
                                      control_path=None,
                                      ProxyCommand=proxy_command)

    def run_rsync_up(self, source, target, options=None):
        super()._set_ssh_ip_if_required()
        options = options or {}

        command = ["scp"]
        destination = "{}@{}:{}".format(self.ssh_user, self.ssh_ip, target)

        # Construct the full command by joining the source and destination
        command += [source, destination]

        # Add the proxy command options as part of the scp command
        command = [
                      "ssh",
                      "-o", "ProxyCommand={}".format(shlex.quote(self.ssh_proxy_command)),
                      "-o", "StrictHostKeyChecking=no",
                      "-o", "UserKnownHostsFile=/dev/null",
                  ] + command
        print(command)
        cli_logger.verbose("Running `{}`", cf.bold(" ".join(command)))
        self._run_helper(command, silent=False)
