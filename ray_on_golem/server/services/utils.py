from pathlib import Path
from shlex import quote

from ray_on_golem.server.settings import SSH_SERVER_ALIVE_COUNT_MAX, SSH_SERVER_ALIVE_INTERVAL


def get_ssh_command(
    ip: str, ssh_proxy_command: str, ssh_user: str, ssh_private_key_path: Path
) -> str:
    proxy_command_str = f"ProxyCommand={ssh_proxy_command}"
    ssh_user_str = f"{ssh_user}@{ip}"

    return " ".join(
        [
            "ssh",
            "-o StrictHostKeyChecking=no",
            "-o UserKnownHostsFile=/dev/null",
            "-o PasswordAuthentication=no",
            f"-o ServerAliveInterval={SSH_SERVER_ALIVE_INTERVAL}",
            f"-o ServerAliveCountMax={SSH_SERVER_ALIVE_COUNT_MAX}",
            f"-o {quote(proxy_command_str)}",
            f"-i {quote(str(ssh_private_key_path))}" if ssh_private_key_path else "",
            quote(ssh_user_str),
        ]
    )
