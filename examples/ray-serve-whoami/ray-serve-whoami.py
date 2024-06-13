import requests
from starlette.requests import Request
from typing import Dict
import socket
import time

from ray import serve

import ray

def get_own_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("192.168.0.1", 1))
    return s.getsockname()[0]

# 1: Define a Ray Serve application.
@serve.deployment(num_replicas=4)
class WhoamiDeployment:
    _replica_id = "?"
    def __init__(self, msg: str):
        # Initialize model state: could be very large neural net weights.
        #self._msg = msg
        self._replica_id = ray.get_runtime_context().get_actor_id()
        #pass

    async def __call__(self, request: Request) -> Dict:
        #return {"result": await request.body()}
        #return {"result":  socket.gethostbyname(socket.gethostname())}
        
        time.sleep(0.5)
        return {"result":  get_own_ip() + " " + self._replica_id}


whoami = WhoamiDeployment.bind(msg="not important")

# 2: Deploy the application locally.
#serve.run(app, route_prefix="/")

# 3: Query the application and print the result.
#print(requests.get("http://localhost:8000/").json())
# {'result': 'Hello world!'}
