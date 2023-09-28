import socket
import time
import argparse
from collections import Counter

import ray

ray.init()


print(
    """This cluster consists of
    {} nodes in total
    {} CPU resources in total
""".format(
        len(ray.nodes()), ray.cluster_resources()["CPU"]
    )
)


@ray.remote
def f():
    time.sleep(0.5)

    return socket.gethostbyname(socket.gethostname())



parser = argparse.ArgumentParser()
parser.add_argument(
    "-c", "--count", type=int, default=100, help="number of tasks to perform, default: %(default)s"
)
args = parser.parse_args()


object_ids = [f.remote() for _ in range(args.count)]
ip_addresses = ray.get(object_ids)

print("Tasks executed")
for ip_address, num_tasks in Counter(ip_addresses).items():
    print("    {} tasks on {}".format(num_tasks, ip_address))


print(
    """This cluster consists of
    {} nodes in total
    {} CPU resources in total
""".format(
        len(ray.nodes()), ray.cluster_resources()["CPU"]
    )
)
