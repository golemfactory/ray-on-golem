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
