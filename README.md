# golem-ray
Setup project
```bash
$ poetry install
```
Create an .env file basing on .env.example

Run yagna
```bash
$ export YAGNA_APPKEY=...
$ yagna payment fund
$ yagna service run
```
Run Server
```bash
$ ray-on-golem
```
Start ray
```bash
$ ray up golem-cluster.yaml
```


## Contributing

### Running code auto format

```bash
$ poetry run poe format
```


## Creating docker images for use with providers

### Requirements

```text
- docker
- gvmkit-build
```

### Select python and ray versions in pyproject.toml

```toml
python = "3.9.2"
ray = "2.6.1"
```

### Select python version in Dockerfile

```yaml
FROM python:3.9.2-slim # slim images preferred due to their size
```

### Build docker image

```bash
$ docker image build -t py3.9.2-ray2.6.1 .
```

### Build and push image to golem registry

```bash
$ gvmkit-build py3.9.2-ray2.6.1 --push-to user/repo_name:py3.9.2-ray2.6.1
```