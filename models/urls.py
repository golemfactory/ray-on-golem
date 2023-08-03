import os
from pathlib import Path

import dotenv
from yarl import URL

dotenv.load_dotenv(Path(__file__).parent / '.env')


class GolemRayURLs:
    def __init__(self):
        # TODO: przeniesc do constow, tworzenie urla w requestach, base url jako argument (nie w zmiennej, definiowane gdzies na gorze klienta)
        self.BASE_URL = URL(os.getenv("WEB_SERVER_URL", 'http://localhost:8080'))
        self.CREATE_CLUSTER = self.BASE_URL / 'create_cluster'
        self.GET_NODES = self.BASE_URL / ''
        self.IS_RUNNING = self.BASE_URL / 'is_running'
        self.IS_TERMINATED = self.BASE_URL / 'is_terminated'
        self.NODE_TAGS = self.BASE_URL / 'tags'
        self.INTERNAL_IP = self.BASE_URL / 'internal_ip'
        self.SET_NODE_TAGS = self.BASE_URL / 'set_tags'
        self.CREATE_NODES = self.BASE_URL / 'create_nodes'
        self.TERMINATE_NODES = self.BASE_URL / 'terminate'
