import os
from datetime import timedelta
from pathlib import Path

from yarl import URL

RAY_ON_GOLEM_PATH = Path(os.getenv("RAY_ON_GOLEM_PATH", "ray-on-golem"))
YAGNA_PATH = Path(os.getenv("YAGNA_PATH", "yagna"))
WEBSOCAT_PATH = Path(os.getenv("WEBSOCAT_PATH", "websocat"))
TMP_PATH = Path("/tmp/ray_on_golem")

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "standard",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "standard",
            "filename": TMP_PATH / "webserver.log",
            "maxBytes": 1024 * 1024,  # 1MB
            "backupCount": 3,
        },
    },
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
    "loggers": {
        "aiohttp": {
            "level": "DEBUG",
        },
        "ray_on_golem": {
            "level": "INFO",
        },
    },
}

YAGNA_APPKEY = os.getenv("YAGNA_APPKEY")
YAGNA_APPNAME = os.getenv("YAGNA_APPNAME", "ray-on-golem")
YAGNA_API_URL = URL(os.getenv("YAGNA_API_URL", "http://127.0.0.1:7465"))

RAY_ON_GOLEM_PORT = int(os.getenv("RAY_ON_GOLEM_PORT", 4578))
RAY_ON_GOLEM_START_DEADLINE = timedelta(seconds=30)
RAY_ON_GOLEM_CHECK_DEADLINE = timedelta(seconds=2)
RAY_ON_GOLEM_SHUTDOWN_DELAY = timedelta(seconds=10)

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
URL_SELF_SHUTDOWN = "/self_shutdown"
