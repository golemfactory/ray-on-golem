import os
from datetime import timedelta
from pathlib import Path

from yarl import URL

RAY_ON_GOLEM_PATH = Path(os.getenv("RAY_ON_GOLEM_PATH", "ray-on-golem"))
YAGNA_PATH = Path(os.getenv("YAGNA_PATH", "yagna"))
WEBSOCAT_PATH = Path(os.getenv("WEBSOCAT_PATH", "websocat"))
TMP_PATH = Path("/tmp/ray_on_golem")
LOGGING_INFO_PATH = TMP_PATH / "webserver.log"
LOGGING_DEBUG_PATH = TMP_PATH / "webserver_debug.log"
LOGGING_YAGNA_PATH = TMP_PATH / "yagna.log"

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "add_trace_id": {
            "()": "golem.utils.logging.AddTraceIdFilter",
        },
    },
    "formatters": {
        "compact": {
            "format": "[%(asctime)s] [%(levelname)-7s] [%(name)s] %(message)s",
        },
        "verbose": {
            "format": "[%(asctime)s] [%(levelname)-7s] [%(traceid)s] "
            "[%(name)s:%(lineno)d] %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "verbose",
            "filters": ["add_trace_id"],
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "INFO",
            "formatter": "compact",
            "filename": LOGGING_INFO_PATH,
            "mode": "w",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": [
            "console",
            "file",
        ],
    },
    "loggers": {
        "aiohttp": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
        "ray_on_golem": {
            "level": "DEBUG",
        },
        "golem": {
            "level": "INFO",
        },
        "golem.utils.asyncio": {
            "level": "DEBUG",
        },
        "golem.managers.payment": {
            "level": "DEBUG",
        },
        "golem.managers.network": {
            "level": "DEBUG",
        },
        "golem.managers.demand": {
            "level": "DEBUG",
        },
        "golem.managers.proposal": {
            "level": "DEBUG",
        },
        "golem.managers.agreement": {
            "level": "DEBUG",
        },
        "golem.managers.activity": {
            "level": "DEBUG",
        },
        "golem.managers.work": {
            "level": "DEBUG",
        },
    },
}

YAGNA_APPKEY = os.getenv("YAGNA_APPKEY")
YAGNA_APPNAME = os.getenv("YAGNA_APPNAME", "ray-on-golem")
YAGNA_API_URL = URL(os.getenv("YAGNA_API_URL", "http://127.0.0.1:7465"))
YAGNA_START_DEADLINE = timedelta(minutes=2)
YAGNA_FUND_DEADLINE = timedelta(minutes=10)
YAGNA_CHECK_DEADLINE = timedelta(seconds=2)

RAY_ON_GOLEM_START_DEADLINE = timedelta(minutes=5)
RAY_ON_GOLEM_CHECK_DEADLINE = timedelta(seconds=2)
RAY_ON_GOLEM_SHUTDOWN_DELAY = timedelta(seconds=30)
RAY_ON_GOLEM_SHUTDOWN_DEADLINE = timedelta(seconds=30)

URL_HEALTH_CHECK = "/health_check"
URL_CREATE_CLUSTER = "/create_cluster"
URL_NON_TERMINATED_NODES = "/non_terminated_nodes"
URL_IS_RUNNING = "/is_running"
URL_IS_TERMINATED = "/is_terminated"
URL_NODE_TAGS = "/tags"
URL_GET_CLUSTER_DATA = "/cluster_data"
URL_INTERNAL_IP = "/internal_ip"
URL_SET_NODE_TAGS = "/set_tags"
URL_REQUEST_NODES = "/request_nodes"
URL_TERMINATE_NODE = "/terminate"
URL_GET_SSH_PROXY_COMMAND = "/ssh_proxy_command"
URL_GET_OR_CREATE_DEFAULT_SSH_KEY = "/ger_or_create_default_ssh_key"
URL_SELF_SHUTDOWN = "/self_shutdown"

PAYMENT_NETWORK_MAINNET = "mainnet"
PAYMENT_NETWORK_POLYGON = "polygon"
