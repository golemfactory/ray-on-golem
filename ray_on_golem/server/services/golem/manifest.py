from typing import Dict

from yarl import URL


def get_manifest(image_url: URL, image_hash: str) -> Dict:
    return {
        "version": "0.1.0",
        "createdAt": "2023-06-26T00:00:00.000000Z",
        "expiresAt": "2100-01-01T00:00:00.000000Z",
        "metadata": {
            "name": "Golem Ray",
            "description": "Golem ray webserver",
            "version": "0.0.1",
        },
        "payload": [
            {
                "urls": [str(image_url)],
                "hash": f"sha3:{image_hash}",
            }
        ],
        "compManifest": {
            "version": "0.1.0",
            "script": {
                "commands": [
                    "run /bin/sh -c *",
                ],
                "match": "regex",
            },
            "net": {
                "inet": {
                    "out": {
                        "protocols": ["https"],
                        "urls": [
                            "https://pypi.dev.golem.network",
                        ],
                    }
                }
            },
        },
    }
