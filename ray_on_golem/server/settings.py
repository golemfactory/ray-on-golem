import os
from datetime import timedelta
from pathlib import Path
from typing import Literal, Optional

import appdirs
from yarl import URL

YAGNA_APPKEY = os.getenv("YAGNA_APPKEY")
YAGNA_APPNAME = os.getenv("YAGNA_APPNAME", "ray-on-golem")
YAGNA_API_URL = URL(os.getenv("YAGNA_API_URL", "http://127.0.0.1:7465"))
YAGNA_START_TIMEOUT = timedelta(minutes=2)
YAGNA_FUND_TIMEOUT = timedelta(minutes=2)
YAGNA_CHECK_INTERVAL = timedelta(seconds=2)

# how long will we wait until we raise an error on webserver startup
RAY_ON_GOLEM_START_TIMEOUT = timedelta(minutes=5)

# how often the startup/shutdown status is checked
RAY_ON_GOLEM_CHECK_INTERVAL = timedelta(seconds=2)

# how long a shutdown request will wait until the webserver shutdown is initiated
RAY_ON_GOLEM_SHUTDOWN_DELAY = timedelta(seconds=60)

# how long we wait for the webserver shutdown to complete
RAY_ON_GOLEM_SHUTDOWN_TIMEOUT = timedelta(seconds=60)

# how long we wait for the webserver process to exit
RAY_ON_GOLEM_STOP_TIMEOUT = timedelta(minutes=3)

RAY_ON_GOLEM_PID_FILENAME = "ray_on_golem.pid"

URL_STATUS = "/"
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
URL_SHUTDOWN = "/shutdown"

PAYMENT_NETWORK_MAINNET = "mainnet"
PAYMENT_NETWORK_POLYGON = "polygon"
PAYMENT_NETWORK_GOERLI = "goerli"
PAYMENT_DRIVER_ERC20 = "erc20"

SUGGESTED_HEADS_SUBNET_TAG = "ray-on-golem-heads"

RAY_ON_GOLEM_PATH = Path(os.getenv("RAY_ON_GOLEM_PATH", "ray-on-golem"))
YAGNA_PATH = Path(os.getenv("YAGNA_PATH", "yagna"))
WEBSOCAT_PATH = Path(os.getenv("WEBSOCAT_PATH", "websocat"))
TMP_PATH = Path("/tmp/ray_on_golem")
LOGGING_BACKUP_COUNT = 99

APPLICATION_NAME = "ray_on_golem"
APPLICATION_AUTHOR = "golemfactory"

DEFAULT_DATADIR = Path(
    os.getenv("RAY_ON_GOLEM_DATADIR", appdirs.user_data_dir(APPLICATION_NAME, APPLICATION_AUTHOR))
)


LogTypes = Literal["webserver", "webserver_debug", "yagna"]


def get_datadir(datadir: Optional[Path] = None) -> Path:
    if not datadir:
        datadir = DEFAULT_DATADIR
    datadir.mkdir(parents=True, exist_ok=True)
    return datadir


def get_log_path(log_type: LogTypes, datadir: Optional[Path] = None) -> Path:
    datadir = get_datadir(datadir)
    return datadir / f"{log_type}.log"


def get_logging_config(datadir: Optional[Path] = None):
    return {
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
                "class": "ray_on_golem.log.ZippingRotatingFileHandler",
                "level": "INFO",
                "formatter": "compact",
                "filename": get_log_path("webserver", datadir),
                "backupCount": LOGGING_BACKUP_COUNT,
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
