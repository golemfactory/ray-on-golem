# Ray on Golem pre-alpha Preview Program

Welcome to the Ray on Golem pre-alpha Preview Program description!

Thank you for your interest in the Preview Program. 
Its purpose is to test the new Ray on Golem solution with its documentation at https://golem-docs-git-mateusz-ray-on-golem-pre-alpha-golem.vercel.app/docs/creators/ray.

The pre-alpha release is a sneak-peak, with happy path working on our test network. We publish the release and run the preview program 
to get it out of the building - to start verifying the potential to decide on further investment in Ray on Golem. 

This article contains a set of tasks that you can complete to broaden your knowledge and help improve the Golem Network.

We have rewards for 10 people (USD 120 each) - we will communicate via the Upwork platform.
We want to test Ray on Golem on Linux.

If you have any questions, we encourage you to contact the Ray on Golem team directly - join our community on [Discord](https://chat.golem.network) and find the `#Ray on Golem` channel in the Golem projects section.

We also encourage you to visit https://www.golem.network/, where you can find more basic information about our open-source project.

## Preview tasks

There are four tasks. You need to complete them all to apply for the reward.

### #1 Setup tutorial

Go through the [setup tutorial](https://golem-docs-git-mateusz-ray-on-golem-pre-alpha-golem.vercel.app/docs/creators/ray/setup-tutorial) and send us your console outputs (copy the content of all the terminals you used and paste them to a text file)

We want to test how our solution behaves in different environments and how helpful our tutorial is.

### #2 Converting a real-life use case to Ray on Golem

Go through the [converting a real-life use case to Ray on Golem tutorial](https://golem-docs-git-mateusz-ray-on-golem-pre-alpha-golem.vercel.app/docs/creators/ray/conversion-to-ray-on-golem-tutorial) and send us your console outputs (just copy the content of all the terminals you used and paste them to a text file)

We want to test how our solution behaves in different environments and how helpful our tutorial is.
 
### #3 Parallelize the hash cracker script with Ray and execute it on Ray on Golem

Take a look at this [piece of code](https://github.com/golemfactory/ray-on-golem/raw/main/examples/hash_cracker_ray_ready.py)

It takes a sha256 hash of some unknown word as an input and looks for a word that results in a match.
The code doesn't know anything about Golem nor Ray.

```bash
python hash_cracker_without_ray.py -l 4 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
```
```
finished in 0:00:40.953827, match found: test
```

You can find a couple of other hashes to crack in the code's comments.


Your task is to parallelize the code and execute it on Ray on Golem cluster.
The goal is to benefit from distributed execution on Ray on Golem cluster so that it takes less time than executed locally.

As a result of this task, we'd like to learn whether, and how, our documentation helped you run such an arbitrary piece of python code on a Ray on Golem cluster.

### #4 Fill out the feedback form  

Please fill out the [submission form](https://qkjx8blh5hm.typeform.com/to/GtaCVz0b)
We are looking for meaningful and thought-out feedback that will help us drive the solution.

The form will ask you to upload console logs from the first three tasks.

### Useful links

- [Ray on Golem docs](https://golem-docs-git-mateusz-ray-on-golem-pre-alpha-golem.vercel.app/docs/creators/ray)
- [Ray docs](https://docs.ray.io)
- [`#Ray on Golem` discord channel](https://chat.golem.network/) 
