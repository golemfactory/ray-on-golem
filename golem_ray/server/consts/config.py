from pathlib import Path

_UTILS_DIR = "utils"
_MANIFEST_FILE_NAME = "manifest.json"
MANIFEST_DIR = Path(__file__).parent.joinpath(_UTILS_DIR).joinpath(_MANIFEST_FILE_NAME)

DICT_CONFIG = {
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
