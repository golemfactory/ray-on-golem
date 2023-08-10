import os

import dotenv
from yarl import URL

dotenv.load_dotenv()
LOGGER_DICT_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        "root": {
            "handlers": ["console"],
            "level": "INFO"
        },
    },
    "handlers": {
        "console": {
            # "formatter": "std_out",
            "class": "logging.StreamHandler",
            "level": "DEBUG"
        }
    },
}

YAGNA_PATH = os.getenv('YAGNA_PATH', 'yagna')
GCS_REVERSE_TUNNEL_PORT = os.getenv('GCS_REVERSE_TUNNEL_PORT', 3009)
PROXY_IP = os.getenv('PROXY_IP', 'proxy.dev.golem.network')
YAGNA_APPKEY = os.getenv('YAGNA_APPKEY')
BASE_URL = URL(os.getenv('BASE_URL', 'http://localhost:8080'))

URL_CREATE_CLUSTER = '/create_cluster'
URL_GET_NODES = '/'
URL_IS_RUNNING = '/is_running'
URL_IS_TERMINATED = '/is_terminated'
URL_NODE_TAGS = '/tags'
URL_INTERNAL_IP = '/internal_ip'
URL_SET_NODE_TAGS = '/set_tags'
URL_CREATE_NODES = '/create_nodes'
URL_TERMINATE_NODES = '/terminate'
URL_GET_NODE_SSH_PORT = '/port'
