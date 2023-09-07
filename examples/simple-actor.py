import ray

#ray.init()
ray.init(address="ray://127.0.0.1:10001")

import socket
import time
from collections import Counter


@ray.remote
class CounterActor:
    def __init__(self):
        self.value = 0
        self.node_ids = []

    def increment(self):
        time.sleep(0.5)
        self.value += 1

        #ip = socket.gethostbyname(socket.gethostname())
        node_id = ray.get_runtime_context().get_node_id()
        self.node_ids.append(node_id)

        return node_id 

    def get_counter(self):
        return self.value

    def get_node_ids(self):
        return self.node_ids

# Create ten Counter actors.
counters = [CounterActor.remote() for _ in range(10)]

# Increment each Counter once and get the results. These tasks all happen in
# parallel.

object_ids = []

for _ in range(10):
    object_ids += [c.increment.remote() for c in counters] 


ip_addresses = ray.get(object_ids)
print('Actor calls executed')
for ip_address, num_tasks in Counter(ip_addresses).items():
    print('    {} tasks on {}'.format(num_tasks, ip_address))

node_ids = ray.get([c.get_node_ids.remote() for c in counters])


for i in range(len(counters)):
    print('Actor {} executed'.format(counters[i]))
    for node_id, num_tasks in Counter(node_ids[i]).items():
        print('    {} tasks on {}'.format(num_tasks, node_id))

# Increment the first Counter five times. These tasks are executed serially
# and share state.
ip_addresses = ray.get([counters[0].increment.remote() for _ in range(5)])

print('Actor calls executed')
for ip_address, num_tasks in Counter(ip_addresses).items():
    print('    {} tasks on {}'.format(num_tasks, ip_address))


from ray.autoscaler.sdk import request_resources

print('''This cluster consists of
    {} nodes in total
    {} CPU resources in total
'''.format(len(ray.nodes()), ray.cluster_resources()['CPU']))
