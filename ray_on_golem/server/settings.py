import os
from pathlib import Path

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "standard",
        }
    },
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "loggers": {
        "root": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "aiohttp": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "ray_on_golem": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

YAGNA_PATH = Path(os.getenv("YAGNA_PATH", "yagna"))
WEBSOCAT_PATH = Path(os.getenv("WEBSOCAT_PATH", "websocat"))
TMP_PATH = Path("/tmp/ray_on_golem")

YAGNA_APPKEY = os.getenv("YAGNA_APPKEY")
RAY_ON_GOLEM_SERVER_PORT = int(os.getenv("RAY_ON_GOLEM_SERVER_PORT", 4578))

URL_HEALTH_CHECK = "/health_check"
URL_CREATE_CLUSTER = "/create_cluster"
URL_NON_TERMINATED_NODES = "/non_terminated_nodes"
URL_IS_RUNNING = "/is_running"
URL_IS_TERMINATED = "/is_terminated"
URL_NODE_TAGS = "/tags"
URL_INTERNAL_IP = "/internal_ip"
URL_SET_NODE_TAGS = "/set_tags"
URL_CREATE_NODES = "/create_nodes"
URL_TERMINATE_NODE = "/terminate"
URL_GET_SSH_PROXY_COMMAND = "/ssh_proxy_command"
URL_GET_OR_CREATE_DEFAULT_SSH_KEY = "/ger_or_create_default_ssh_key"