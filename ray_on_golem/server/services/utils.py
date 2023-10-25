from pathlib import Path


def get_ssh_command(
    ip: str, ssh_proxy_command: str, ssh_user: str, ssh_private_key_path: Path
) -> str:
    return (
        "ssh "
        "-o StrictHostKeyChecking=no "
        "-o UserKnownHostsFile=/dev/null "
        f'-o "ProxyCommand={ssh_proxy_command}" '
        f"-i {ssh_private_key_path} "
        f"{ssh_user}@{ip}"
    )
