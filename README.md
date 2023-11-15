# Ray on Golem

<h5 align="center">
  <a href='https://docs.golem.network/docs/creators/ray'><img
      width='500px'
      alt=''
      src="https://github.com/golemfactory/ray-on-golem/raw/main/Ray_on_Golem.jpg" /></a>
</h5>

## What is Golem, Ray and Ray on Golem

[Golem](https://golem.network) is a decentralized marketplace for computing power, where providers let requestors use their machines for a small fee.

Ray on Golem makes it super easy to set up and use Golem Network to run your Ray applications.

[Ray](https://ray.io) on the other hand is an open-source framework dedicated to scaling Python workloads. 
It specializes in tooling for AI/ML applications, but at the same time, it is based on Ray Core which understands every piece of generic Python code.

Ray uses concepts of tasks, actors, and objects to enable building and scaling distributed software.
It can be used to parallelize your Python code to use all cores on your own computer, but more importantly, it also offers a cluster interface to run your payload on several, remote machines.

You can learn about Ray Core mechanisms on [Ray docs website](https://docs.ray.io/en/latest/ray-core/walkthrough.html) or check out [Ray on Golem docs](https://docs.golem.network/docs/creators/ray) to dive right into development.

## Quickstart

This [quickstart](https://docs.golem.network/docs/creators/ray/quickstart) shows you how to set Ray and Ray on Golem up, start your cluster, test it, and then stop it.
It limits the explanation to the bare minimum - if you are looking for more details jump to [setup tutorial](https://docs.golem.network/docs/creators/ray/setup-tutorial)


### Install software

**Note:** We recommend creating a new directory and a clean Python virtual environment before you proceed. This avoids cluttering your system installation with unnecessary packages.

The first step is installing Ray on Golem. It will install Ray as a dependency.

```bash
# install ray-on-golem and ray (recommended within a clean virtual environment)
pip3 install -U ray-on-golem
```

**Note:** As an added convenience, the installation of `ray-on-golem` ensures that both `ray` and `yagna` are set up for you. With these components in place, you're well-prepared to harness the full potential of Ray on the Golem Network.

### Set the cluster up

With the packages in place, you can download our sample golem cluster configuration yaml, and use it with `ray up` to start up the cluster.
It will give you a cluster of one node (which will expand when you feed it with work) on the Golem test network (free, but not very powerful)

```bash
# Download the golem-cluster.yaml
wget https://github.com/golemfactory/ray-on-golem/raw/main/golem-cluster.yaml

# In this command:
# * yagna starts in the background (if not running)
# * ray-on-golem cluster manager starts in the background
# * ray head node is started on a golem provider
ray up golem-cluster.yaml --yes

```

Consult the [troubleshooting](/docs/creators/ray/troubleshooting) guide if anything goes wrong.

### Execute a Ray application

Download our example Ray app and execute it locally (a Ray instance will be created on your machine)

```bash
# Download the example Ray app
wget https://github.com/golemfactory/ray-on-golem/raw/main/examples/simple-task.py

# Execute the app locally by starting a local ray instance on your computer
python3 simple-task.py
```

This particular script shows information about the cluster it is being run on 
and also visualizes the number of tasks run on different nodes (by default it executes 100 tasks).

Once you ensure the app works, you can feed it to your Ray on Golem cluster:

```bash
# Submit the app to be executed on your cluster
ray submit golem-cluster.yaml simple-task.py
```

You can see the information about the cluster both before and after running the computations.

Submit the code again, requesting more tasks to see how the autoscaler expands the cluster, as the work progresses (give it up to 5 mins).

```bash
# Submit the app with 400 tasks
ray submit golem-cluster.yaml simple-task.py -- --count 400 
```

The above shows the usual workflow with Ray apps.
- You develop them, while at the same time testing them, on your local machine.
- When you are ready to get more power - you send them to a Ray cluster **without changing a single line** of your application's code.


### Stop the cluster

Finally, stop your cluster to free the Golem network providers and to avoid spending more than needed (the testnet is free, but good practice is a good practice).

```bash
# Tear down the cluster.
ray down golem-cluster.yaml --yes
```

## Summary

By completing the above quickstart you have successfully:

- Installed ray and ray-on-golem packages
- Downloaded the example golem cluster yaml and the example ray application
- Started up the Ray on Golem cluster
- Run the app on your local computer and then on the cluster
- Stopped the cluster

Congratulations!

## Limitations

Current version is `pre-alpha` which means the happy path is working on **Ubuntu** on the Golem test network.
We have tested Ray on Golem on Ubuntu and on WSL, but it should work on other Linux distributions. At the moment, we don't support MacOS or bare Windows.
 
We use this version to show the direction and get feedback.

There is one Ray on Golem image. It contains `ray 2.7.1` and `python 3.10.13`.
It should work with any combination of local ray and python versions. Please let us know if you have any troubles because of that (on [`#Ray on Golem` discord channel](https://chat.golem.network/))

The images include only basic libraries, if you need any dependencies, 
you can use `pip` via [cluster yaml `initialization_commands`](https://golem-docs-git-mateusz-ray-on-golem-pre-alpha-golem.vercel.app/docs/creators/ray/cluster-yaml-reference#initializationcommands)

## Next steps

Explore [Ray on Golem docs](https://docs.golem.network/docs/creators/ray) to learn more about various aspects and usages of our platform.

If you have any questions, comments, insights, praises, or doubts about these docs and Ray on Golem in general please don't hesitate to reach out to us either on
- [`#Ray on Golem` discord channel](https://chat.golem.network/) 
- [Ray on Golem general feedback form](https://qkjx8blh5hm.typeform.com/to/GtaCVz0b)
