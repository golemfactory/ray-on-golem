# Ray on Golem

## What is Golem, Ray and Ray on Golem

[Golem](https://golem.network) on is a decentralized marketplace for computing power, where providers let requestors use their machines for a small fee.

Ray on Golem makes it super easy to set up and use Golem Network to run your Ray applications.

[Ray](https://ray.io) on the other hand is an open-source framework dedicated to scaling Python workloads. 
It specializes in tooling for AI/ML applications, but at the same time, it is based on Ray Core which understands every piece of generic Python code.

Ray uses concepts of tasks, actors, and objects to enable building and scaling distributed software.
It can be used to parallelize your Python code to use all cores on your own computer, but more importantly, it also offers a cluster interface to run your payload on several, remote machines.

You can learn about Ray Core mechanisms on [Ray docs website](https://docs.ray.io/en/latest/ray-core/walkthrough.html).

Check out [Ray on Golem docs](https://docs.golem.network/docs/creators/ray) to get started :)


If you have any questions, comments, insights, praises, or doubts about these docs and Ray on Golem in general please don't hesitate to reach out to us either on
- [`#Ray on Golem` discord channel](https://chat.golem.network/) 
- [Ray on Golem general feedback form](https://qkjx8blh5hm.typeform.com/to/GtaCVz0b)


## In this README

- [Limitations](#limitations) Describes the current limitations of Ray on Golem
- [Quickstart](#quickstart) Drives you through copy and paste installation and execution of the example Ray app on example Ray on Golem cluster
- [Contributing](#contributing) Offers advice on building Golem images for Ray on Golem development purposes


# Limitations

Current version is `pre-alpha` which means the happy path is working on Ubuntu on the Golem test network.
We have tested Ray on Golem on Ubuntu and on WSL. It should work on other Linux distributuions, might work on MacOS and shouldn't on bare Windows.
 
We use this version to show the direction and get feedback.

There is one Ray on Golem image. It contains `ray 2.3.1` and `python 3.10.12`.
It should work with any combination of local ray & python versions. Please let us know if you have any troubles because of that (on [`#Ray on Golem` discord channel](https://chat.golem.network/))

The images include only basic libraries, if you need any dependencies, 
you can use `pip` via [cluster yaml `initialization_commands`](https://golem-docs-git-mateusz-ray-on-golem-pre-alpha-golem.vercel.app/docs/creators/ray/cluster-yaml-reference#initializationcommands)

We have tested Ray on Golem on Ubuntu and on WSL. It should work on MacOS and shouldn't on bare Windows.

# Quickstart

This [quickstart](https://golem-docs-git-mateusz-ray-on-golem-pre-alpha-golem.vercel.app/docs/creators/ray/quickstart) shows you how to set Ray and Ray on Golem up, start your cluster, test it, and then stop it.
It limits the explanation to the bare minimum - if you are looking for more details jump to [setup tutorial](/docs/creators/ray/setup-tutorial)


## Install software

The first step is installing Ray and Ray on Golem (recommended within a clean venv)

```bash
# install ray & ray-on-golem (recommended within a clean venv)
pip3 install -U ray[default] ray-on-golem
```

For now, you also need to download and install Golem node software representing you in the Golem network.

```bash
# install yagna - golem network daemon
curl -sSf https://join.golem.network/as-requestor | bash -
```

## Start `ray-on-golem` server

For the time being you need to manually run `ray-on-golem` server (in a separate terminal)

```bash
ray-on-golem
```

## Set the cluster up

With the packages in place, you can download our sample golem cluster configuration yaml, and feed it to `ray up` to start up the cluster.
It will give you a cluster of one node (which will expand when you feed it with work) on the Golem test network (free, but not very powerful)


```bash
# Download the golem-cluster.yaml
wget https://github.com/golemfactory/ray-on-golem/blob/main/golem-cluster.yaml

# In this command:
# * yagna starts in the background (if not running)
# * ray-on-golem cluster manager starts in the background
# * ray head node is started on a golem provider
ray up golem-cluster.yaml

```

## Execute a Ray application

Download our example Ray app and execute it locally (a Ray instance will be created on your machine)

```bash
# Download the example Ray app
wget https://github.com/golemfactory/ray-on-golem/blob/main/examples/simple-task.py

# Execute the app locally by starting a local ray instance on your computer
python3 simple-task.py
```

Feed the app to the cluster. Observe how Ray on Golem cluster expands during the computation

```bash
# Run some ray-based code (that knows *nothing** about Golem) - this will either:
# A) Run only on one node (the head node), if the autoscaler decides there is no need for a worker node
# B) Or create worker node(s) on the Golem Network. Worker nodes will be later auto-terminated by the autoscaler)

# Submit the app to be executed on your cluster
ray submit golem-cluster.yaml simple-task.py 
```

## Stop the cluster

In the end, stop your cluster to free the Golem network providers and to avoid too much spending (the testnet is free, but good practice is a good practice)

```bash
# Tear down the cluster.
ray down golem-cluster.yaml
```

For the time being you also nee to stop `ray-on-golem` server (with `Control-C`).

## Summary

By completing the above quickstart you have successfully:
- installed ray and ray-on-golem packages
- downloaded the example golem cluster yaml and the example ray application
- started up the Ray on Golem cluster
- run the app on your local computer and then on the cluster
- stopped the cluster

Congratulations!

## Next steps
- [Ray on Golem docs](https://golem-docs-git-mateusz-ray-on-golem-pre-alpha-golem.vercel.app//docs/creators/ray)

# Contributing

## Running code auto format

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

