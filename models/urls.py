import os
from pathlib import Path

import dotenv
from yarl import URL

dotenv.load_dotenv(Path(__file__).parent / '.env')


class GolemRayURLs:
    BASE_URL = URL(os.getenv("WEB_SERVER_URL", 'http:localhost:8080'))
    CREATE_CLUSTER = 'create_cluster'

    class Nodes:
        _NODES_PREFIX = 'nodes'
        GET_NODES = '/'
        IS_RUNNING = '/is_running'
        IS_TERMINATED = '/is_terminated'
        NODE_TAGS = '/tags'
        INTERNAL_IP = '/internal_ip'
        SET_NODE_TAGS = '/set_tags'
        CREATE_NODES = '/create'
        TERMINATE_NODES = '/terminate'

        def __getattr__(self, item):
            return self._NODES_PREFIX + item

    def __getattr__(self, item):
        return self.BASE_URL.join(item)
