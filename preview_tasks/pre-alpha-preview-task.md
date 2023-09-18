# Ray on Golem pre-alpha Preview Program

Welcome to the Ray on Golem pre-alpha Preview Program description!

Thank you for your interest in the Preview Program. 
Its purpose is to test the new Ray on Golem solution with its documentation at https://docs.golem.network/docs/creators/ray.

The pre-alpha release is a sneak-peak, with only happy path working on our test network. We publish the release and run the preview program 
to get it out of the building - to start veryfing the potential to decide on further investment in Ray on Golem. 

This article contains a set of tasks that you can complete to broaden yout knowledge and help improve Golem Network.

We have rewards for 10 people (USD 120 each) - we will be communicating via Upwork platform.

If you have any questions, we encourage you to contact Ray on Golem team directy - join our community on [Discord](https://chat.golem.network) and find `#Ray on Golem` channel in Golem projects section.

We also encourage you to visit https://www.golem.network/, where you can find more basic information about our open-source project.

**Below you will find the followin information:**

- Available tasks
- Useful links

## Available tasks

There are three tasks. You need to complete them all to apply for the reward.

### #1 Setup tutorial

Go through the [setup tutorial](https://docs.golem.network/docs/creators/ray/setup-tutorial) and send us your console outputs (just copy the content of all the terminals you used and paste them to a text file)

We want to test how our solution behaves on different environments and how helpful our tutorial is.

### #2 Converting a real-life use case to Ray on Golem

Go through the [Converting a real-life use case to Ray on Golem tutorial](https://docs.golem.network/docs/creators/ray/conversion-to-ray-on-golem-tutorial) and send us your console outputs (just copy the content of all the terminals you used and paste them to a text file)

We want to test how our solution behaves on different environments and how helpful our tutorial is.
 
### #3 Parallelize the hash cracker script with Ray and execute it on Ray on Golem

Take a look at this [piece of code](https://github.com/golemfactory/ray-on-golem/blob/mateusz/preview_tasks/examples/hash_cracker_without_ray.py)

It takes a sha256 hash of some unknown word as an input and looks for a word that results in a match.
The code doesn't know anything about Golem nor Ray.

```bash
python hash_cracker_without_ray.py -l 4 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
```
```
```

You can find a couple of other hashes to crack in the code's comments.


Your task is to parallelize the code and execute it on Ray on Golem cluster.
The goal is to benefit from distributed execution on Ray on Golem cluster so that it takes less time than executed locally.

As a result of this task, we'd like to learn whether, and how, our documentation helped you run such an arbitrary piece of python code on a Ray on Golem cluster.

At the end we want you to send us the resulting code and console outputs from its execution.

### Useful links

- [Ray on Golem docs](https://docs.golem.network/docs/creators/ray)
- [Ray docs](https://docs.ray.io)
