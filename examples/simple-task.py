import time
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

    # Return IP address. (should work when Golem providers have hostname)
    # return socket.gethostbyname(socket.gethostname())

    # use this line if you prefer to see node ids instead of node ips
    return ray.get_runtime_context().get_node_id()


object_ids = [f.remote() for _ in range(1000)]
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
