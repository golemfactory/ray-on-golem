import socket
import time
from collections import Counter

import ray

ray.init()


@ray.remote
class CounterActor:
    def __init__(self):
        self.value = 0
        self.node_ips = []

    def increment(self):
        time.sleep(0.5)
        self.value += 1

        node_ip = socket.gethostbyname(socket.gethostname())
        self.node_ips.append(node_ip)

        return node_ip

    def get_counter(self):
        return self.value

    def get_node_ips(self):
        return self.node_ips


# Create ten Counter actors.
counters = [CounterActor.remote() for _ in range(10)]

# Increment each Counter once and get the results. These tasks all happen in
# parallel.

object_ids = []

for _ in range(10):
    object_ids += [c.increment.remote() for c in counters]


ip_addresses = ray.get(object_ids)
print("Actor calls executed")
for ip_address, num_tasks in Counter(ip_addresses).items():
    print("    {} tasks on {}".format(num_tasks, ip_address))

node_ips = ray.get([c.get_node_ips.remote() for c in counters])


for i in range(len(counters)):
    print("Actor {} executed".format(counters[i]))
    for node_id, num_tasks in Counter(node_ips[i]).items():
        print("    {} tasks on {}".format(num_tasks, node_id))

# Increment the first Counter five times. These tasks are executed serially
# and share state.
ip_addresses = ray.get([counters[0].increment.remote() for _ in range(5)])

print("Actor calls executed")
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
