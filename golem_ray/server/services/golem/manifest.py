from ast import Dict


def get_manifest(image_hash: str, gcp_tunnel_port: int) -> Dict:
    return {
        "version": "0.1.0",
        "createdAt": "2023-06-26T00:00:00.000000Z",
        "expiresAt": "2100-01-01T00:00:00.000000Z",
        "metadata": {
            "name": "Golem Ray",
            "description": "Golem ray webserver",
            "version": "0.0.1"
        },
        "payload": [
            {
                "urls": [
                    f"http://registry.golem.network/download/{image_hash}"
                ],
                "hash": f"sha3:{image_hash}"
            }
        ],
        "compManifest": {
            "version": "0.1.0",
            "script": {
                "commands": [
                    "run /bin/sh -c echo*",
                    "run /bin/sh -c mkdir -p /root/.ssh",
                    "run /bin/sh -c cat*",
                    "run /bin/sh -c service ssh start",
                    "run /bin/sh -c ssh*",
                    "run /bin/sh -c *"
                ],
                "match": "regex"
            },
            "net": {
                "inet": {
                    "out": {
                        "protocols": ["https", "tcp"],
                        "urls": [
                            f"tcp://proxy.dev.golem.network:{gcp_tunnel_port}/",
                            "tcp://proxy.dev.golem.network:3020/",
                            "tcp://proxy.dev.golem.network:3021/",
                            "tcp://proxy.dev.golem.network:3022/",
                            "tcp://proxy.dev.golem.network:3023/",
                            "tcp://proxy.dev.golem.network:3024/",
                            "tcp://proxy.dev.golem.network:3025/",
                            "tcp://proxy.dev.golem.network:3026/",
                            "https://pypi.dev.golem.network"]
                    }
                }
            }
        }
    }
