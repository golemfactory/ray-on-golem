import logging
from typing import Dict, List

from yarl import URL

logger = logging.getLogger(__name__)


def get_manifest(
    image_url: URL, image_hash: str, protocols: List[str], outbound_urls: List[str]
) -> Dict:
    manifest = {
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
                        "protocols": protocols,
                        "urls": outbound_urls,
                    }
                }
            },
        },
    }
    logger.debug(f"Manifest generated: {manifest}")
    return manifest
