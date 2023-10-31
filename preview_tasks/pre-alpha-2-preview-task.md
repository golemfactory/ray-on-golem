# Ray on Golem Pre-Alpha Preview #2 Program

Welcome to the Ray on Golem Pre-Alpha Preview #2 Program description!

Thank you for your interest in the Preview Program. 
Its purpose is to test the new Ray on Golem solution with its documentation: https://docs.golem.network/docs/creators/ray.

The pre-alpha release is a sneak-peak, with a happy path working on our test network. We published the release and decided 
to run the preview program to get it out of the building - to start verifying the potential 
and decide if further investment in Ray on Golem is justified.

We want to test Ray on Golem on **Linux**.
The set of tasks described below will help you broaden your knowledge while contributing to the improvement of the Golem Network. 

We have rewards for 10 people (100 USD each) - that you will be able to claim via Upwork after completing the task. 
Note that only those who filled the qualification survey and were contacted on Discord with a link to Upwork are eligible to participate.

If you have any questions, we encourage you to contact the `Ray on Golem` team directly on Discord: `#Ray on Golem` channel in the Golem projects section.

We also encourage you to visit https://www.golem.network/, where you can find more basic information about our open-source project.

# Preview tasks

There are three tasks. You need to complete them all to apply for the reward.

## (Bonus task) Parallelize the hash cracker script with Ray and execute it on Ray on Golem

**Goal**: Evaluate if Ray on Golem makes it easier to parallelize Python code

**Task**: Parallelize the provided hash cracker code. Please show us the resulting code and logs from running it with Ray on Golem.

**Steps**:
- Consider the provided piece of code.
- Parallelize it with Ray (i.e. make it run faster for bigger inputs)
- Run it on Ray on Golem
- Send us your code, the console logs of the code execution on Ray on Golem
- Fill out the [submission form](todo) (code, logs and meaningful and thought-out feedback)

### The code
Take a look at this [piece of code](https://github.com/golemfactory/ray-on-golem/raw/main/examples/hash_cracker_ray_ready.py)

It takes a sha256 hash of some unknown word as input and looks for a word that results in a match.
The code doesn't know anything about Golem or Ray.

```bash
python hash_cracker_ray_ready.py -l 4 de6c0da53ac2bf2b6954e400767106011e4471db7a412cce0388e3441e0ad2ec
```
```
scanning: de6c0da53ac2bf2b6954e400767106011e4471db7a412cce0388e3441e0ad2ec: a, fffg
scanning: de6c0da53ac2bf2b6954e400767106011e4471db7a412cce0388e3441e0ad2ec: fffg, lllm
scanning: de6c0da53ac2bf2b6954e400767106011e4471db7a412cce0388e3441e0ad2ec: lllm, rrrs
scanning: de6c0da53ac2bf2b6954e400767106011e4471db7a412cce0388e3441e0ad2ec: rrrs, xxxy
scanning: de6c0da53ac2bf2b6954e400767106011e4471db7a412cce0388e3441e0ad2ec: xxxy, DDDE
scanning: de6c0da53ac2bf2b6954e400767106011e4471db7a412cce0388e3441e0ad2ec: DDDE, JJJK
scanning: de6c0da53ac2bf2b6954e400767106011e4471db7a412cce0388e3441e0ad2ec: JJJK, PPPQ
scanning: de6c0da53ac2bf2b6954e400767106011e4471db7a412cce0388e3441e0ad2ec: PPPQ, VVVW
scanning: de6c0da53ac2bf2b6954e400767106011e4471db7a412cce0388e3441e0ad2ec: VVVW, 1112
scanning: de6c0da53ac2bf2b6954e400767106011e4471db7a412cce0388e3441e0ad2ec: 1112, 7778
scanning: de6c0da53ac2bf2b6954e400767106011e4471db7a412cce0388e3441e0ad2ec: 7778, ###$
finished in 0:01:45.139588, match found: 9Lm!
```

You can find a couple of other hashes to crack in the code's comments.

### Parallelize to make the code run faster.

You will notice that it runs very fast for hashes of 3-character words, ok-ish for 4-character words (30-120 seconds), and very slowly for longer words (over 20 mins for 5-character words).

Your task is to parallelize the code and execute it on the Ray on Golem cluster.
The goal is to benefit from distributed execution on the Ray on Golem cluster so that it takes less time than executed locally.

Our original hash cracker code was a bit more straightforward, but it was more challenging to parallelize as the obvious candidate for the Ray task was too small.
So now the code is a bit more complex, but it should be easier to parallelize as it now allows more control over the sizes of the tasks.

One additional challenge (and a learning opportunity) here is that we would like to avoid waiting for Ray on Golem to scan the whole of the word space.
We would like to stop the computation when we find the match.

### Fill out the submission form

At the end, we would like a code that finds the `golem` word for `4c5cddb7859b93eebf26c551518c021a31fa0013b2c03afa5b541cbc8bd079a6` hash in 10 minutes.

