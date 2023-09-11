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
        "golem_ray": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

YAGNA_PATH = Path(os.getenv("YAGNA_PATH", "yagna"))
WEBSOCAT_PATH = Path(os.getenv("WEBSOCAT_PATH", "websocat"))
TMP_PATH = Path("/tmp/golem_ray")

YAGNA_APPKEY = os.getenv("YAGNA_APPKEY")
GOLEM_RAY_PORT = int(os.getenv("GOLEM_RAY_PORT", 4578))

URL_HEALTH_CHECK = "/health_check"
URL_CREATE_CLUSTER = "/create_cluster"
URL_GET_NODES = "/"
URL_IS_RUNNING = "/is_running"
URL_IS_TERMINATED = "/is_terminated"
URL_NODE_TAGS = "/tags"
URL_INTERNAL_IP = "/internal_ip"
URL_SET_NODE_TAGS = "/set_tags"
URL_CREATE_NODES = "/create_nodes"
URL_TERMINATE_NODES = "/terminate"
URL_GET_SSH_PROXY_COMMAND = "/ssh_proxy_command"
URL_GET_OR_CREATE_SSH_KEY = "/ger_or_create_ssh_key"
URL_GET_HEAD_NODE_IP = "/head_node_ip"
