import argparse
import socket
import time
from collections import Counter

import ray

ray.init()


def output_cluster_info():
    print(
        """This cluster consists of
        {} nodes in total
        {} CPU resources in total
    """.format(
            len(ray.nodes()), ray.cluster_resources()["CPU"]
        )
    )


# cluster information before the computation
output_cluster_info()


# remote function returning ip of the worker (after 0.5 sec of sleep)
@ray.remote
def f():
    time.sleep(0.5)

    return socket.gethostbyname(socket.gethostname())


# get the number of remote calls from the command line
parser = argparse.ArgumentParser()
parser.add_argument(
    "-c", "--count", type=int, default=100, help="number of tasks to perform, default: %(default)s"
)
args = parser.parse_args()

# start args.count remote calls
object_ids = [f.remote() for _ in range(args.count)]

# wait for the results
ip_addresses = ray.get(object_ids)

print("Tasks executed")
for ip_address, num_tasks in Counter(ip_addresses).items():
    print("    {} tasks on {}".format(num_tasks, ip_address))


# cluster information after the computation
output_cluster_info()
