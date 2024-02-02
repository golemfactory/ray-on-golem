from pathlib import Path
from shlex import quote


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
            f"-o {quote(proxy_command_str)}",
            f"-i {quote(str(ssh_private_key_path))}" if ssh_private_key_path else "",
            quote(ssh_user_str),
        ]
    )
