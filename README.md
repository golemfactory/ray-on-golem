# Ray on Golem

## What is Golem, Ray and Ray on Golem

Golem on is a decentralized marketplace for computing power, where the providers let the requestors use their machines for a small fee.

Ray on Golem makes it super easy to set up and use Golem Network to run your Ray application.

Ray on the other hand is an open-source framework for scaling Python applications. 
It specializes in tooling for AI/ML applications, but at the same time, it is based on Ray Core which understands every piece of generic Python code.

Ray uses concepts of tasks, actors, and objects for building and scaling distributed applications.
It can be used to parallelize your Python code to use all cores on your own computer, but more importantly, it also offers Ray Cluster interface to run your payload on several, remote machines.

You can learn about Ray Core mechanisms on [Ray docs website](https://docs.ray.io/en/latest/ray-core/walkthrough.html).

Check out [Ray on Golem docs](https://docs.golem.network/docs/creators/ray) to get started :)


If you have any questions, comments, insights, praises, or doubts about these docs and Ray on Golem in general please don't hesitate to reach out to us either on
- [`#Ray on Golem` discord channel](https://chat.golem.network/) 
- [Ray on Golem general feedback form](https://qkjx8blh5hm.typeform.com/to/GtaCVz0b)


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

