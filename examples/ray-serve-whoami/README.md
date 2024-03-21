# Example showing Ray Serve

## Steps to run

- `pip install ray[serve]`
- `ray up -y whoami.yaml`
- `ray exec whoami.yaml 'serve run ray-serve-whoami:whoami'`
- Now the head should have an endpoint on `127.0.0.1:8000`
- ray submit whoami.yaml ray-serve-whoami-client.py
- ray exec whoami.yaml 'for i in `seq 100`; do python3 ray-serve-whoami-client.py ; done' 
