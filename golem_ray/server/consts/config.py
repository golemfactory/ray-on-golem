import os
from pathlib import Path

from yarl import URL

_UTILS_DIR = "utils"
_MANIFEST_FILE_NAME = "manifest.json"
MANIFEST_DIR = Path(__file__).parent.joinpath(_UTILS_DIR).joinpath(_MANIFEST_FILE_NAME)

ROOT_DIR = Path(__file__).parents[3]

LOGGER_DICT_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        '': {
            'level': 'INFO',
        },
        'another.module': {
            'level': 'DEBUG',
        },
    }
}

YAGNA_PATH = os.getenv('YAGNA_PATH', 'yagna')
GCS_REVERSE_TUNNEL_PORT = os.getenv('GCS_REVERSE_TUNNEL_PORT', 3009)
PROXY_IP = os.getenv('PROXY_IP', 'proxy.dev.golem.network')
YAGNA_APPKEY = os.getenv('YAGNA_APPKEY')
BASE_URL = URL(os.getenv('BASE_URL', 'http://localhost:8080'))
