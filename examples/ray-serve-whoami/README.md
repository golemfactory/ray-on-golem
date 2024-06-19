# Example showing Ray Serve

## Steps to run

- `pip install ray[serve]`
- `ray up -y whoami.yaml`
- `ray exec whoami.yaml 'serve run ray-serve-whoami:whoami'`
- Now the head should have an endpoint on `127.0.0.1:8000` with four replicas
- `ray submit whoami.yaml ray-serve-whoami-client.py`
- `ray exec whoami.yaml 'seq 100 | xargs -n1 -P20 python3 ray-serve-whoami-client.py'` 

- Now tunnel the port to the requestor:
  - get ssh command (replace the `192.168.0.3` with your head ip):
    `grep -E "^ssh.*192.168.0.3$" ~/.local/share/ray_on_golem/webserver_debug.log | sed -e "s/ root@/ -L8000:localhost:8000 root@/" | sed -e "s/-vvv\? //g"`
  - use the ssh command (copy and run it)

- Now the requestor should have an endpoint on `127.0.0.1:8000`
- `python3 ray-serve-whoami-client.py`
- `seq 100 | xargs -n1 -P20 python3 ray-serve-whoami-client.py`
- Add sort & uniq to see count of tasks done on each actor:
- `seq 100 | xargs -n1 -P50 python3 ray-serve-whoami-client.py | sort -n | uniq -c`

- Check out actors with:
- `ray exec whoami.yaml 'ray list actors --filter "state=ALIVE"'`

## Screen casts
- Play the screencasts with (`-i1` compresses all pauses to 1 sec)
  - `asciinema play -i1 ray-serve-20240617-1.cast`
  - there is a couple of mishaps in the scenario (like tunnel failing in the middle of computations), it is a dirty one

### Scenario
Scenario:
- in `whoami-min1worker.yaml`:
  - `network: "polygon"`
  - head's `CPU: 0` (so it doesn't run replicas on head)
  - `min_workers: 1` (so there is always 1 worker)
  - worker's `CPU: 2` (so that only two replicas fit on 1 node)

- in `ray-serve-whoami.py`:
  - `@serve.deployment(num_replicas=4)` (so that there is 4 replicas, 1 per CPU)
  - potentially configurable to autoscale num of replicas, but we didn't dive deep enough yet
  - `__call__` method sleeps and returns IP with actor's id

- `ray-on-golem start` (so that yagna is warmed up, wait a minute for that)
- `ray up whoami-min1worker.yaml --yes` (so that cluster starts)
- `ray exec whoami-min1worker.yaml 'ray status'` (to see head is up an 1st worker is launching)
- check ray status outside screen cast to know when worker is up
- `ray exec whoami-min1worker.yaml 'ray status'` (to see head is up an 1st worker is up too)
- `ray exec whoami-min1worker.yaml 'serve run ray-serve-whoami:whoami'` (to start the deployment)
- observe the output to notice log from autoscaler (it will want to add 1 more worker to fit all 4 replicas, deployment is working even before (2 replicas on 1st worker)
- switch window
- `ray exec whoami-min1worker.yaml 'ray status'` (to see 2nd worker is launching)
- ssh to setup the tunnel (forward head's 8000 (where serve serves the deployment) to requestor's 8000)
- `python3 ray-serve-whoami-client.py` (one api call to show it works)
- `seq 100 | xargs -n1 -P50 python3 ray-serve-whoami-client.py` (to run 100 calls and observe two replicas' ids are visible)
- `seq 100 | xargs -n1 -P50 python3 ray-serve-whoami-client.py | sort -n | uniq -c` (to see how many calls to which replica)
- `ray exec whoami-min1worker.yaml 'ray status'` (to show 2nd worker is still launching)
- check ray status outside (to know when 2nd worker is up)
- `ray exec whoami-min1worker.yaml 'ray status'` (to show 2nd worker is up)
- `seq 100 | xargs -n1 -P50 python3 ray-serve-whoami-client.py | sort -n | uniq -c` (to show four replicas)
- `ray exec whoami-min1worker.yaml 'ray list actors --filter "state=ALIVE"'` (to show four replicas and three other actors ray serve uses)
- stop the exec with serve (with `C-c`)
- `ray exec whoami-min1worker.yaml 'ray status'` (to show 2 workers still up)
- `ray exec whoami-min1worker.yaml 'ray list actors --filter "state=ALIVE"'` (to show there is no alive actors)
- check ray status outside (to know when 2nd worker is gone)
- `ray exec whoami-min1worker.yaml 'ray status'` (to show only 1 worker is left)
- `ray down whoami-min1worker.yaml --yes` (to stop the cluster)
- `ray-on-golem stop` (to stop yagna)
