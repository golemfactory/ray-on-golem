# Ray on Golem Pre-Alpha Preview Program #2

Welcome to the Ray on Golem Pre-Alpha Preview Program #2!

If you've ever tried scaling your Python code to process large data sets or solve complex computational tasks, you'll know that it may be challenging in various ways.
With Ray on Golem, we're aiming to make this as straightforward as possible, and we invite you to help us make it happen.

Therefore, we'd like to thank you for your interest in the Preview Program.
Its purpose is to field test the new Ray on Golem along with its documentation: https://docs.golem.network/docs/creators/ray.

Our current line of releases is a sneak peek, with a happy path working on our test network.
We publish these releases and run subsequent editions of our preview program with the aim of verifying the potential
of our product against real users' needs.

At the time, we're limiting our tests to Ray on Golem on **Linux**, since we want to focus on the core experience and not on idiosyncrasies of particular platforms on which Golem or Ray in general can run.
The task described below will help you broaden your knowledge while actively contributing to the improvement of the Golem Network.

We have rewards for 10 people (100 USD each) that you will be able to claim via Upwork after completing the task.
Note that only those who filled out the qualification survey and were contacted on Discord with a link to Upwork are eligible to participate.
We estimate the task should take 1-3 hours to complete.

If you have any questions, we encourage you to contact the Ray on Golem team directly on [Discord: `#Ray on Golem` channel](https://discord.gg/golem) in the Golem projects section.

We also invite you to visit https://www.golem.network/, where you can find more basic information about our open-source project.

## Task: parallelize the hash cracker script with Ray and execute it on Ray on Golem

**Goal**: Evaluate if Ray on Golem makes it easier to parallelize Python code. 

**Task**: Parallelize the provided hash cracker code. Please show us the resulting code and logs from running it with Ray on Golem. Last but not least, share the feedback about your experience with Ray on Golem with us.

**Steps**:
- Go through Ray on Golem documentation
- Consider the provided piece of code.
- Parallelize it with Ray (i.e. make it run faster for bigger inputs)
- Run it on Ray on Golem
- Send us your code, the console logs of the code execution on Ray on Golem, and Ray on Golem debug log file.
- Fill out the [submission form](https://qkjx8blh5hm.typeform.com/to/UlpvzPrD) (code, logs and meaningful and thought-out feedback)

### The documentation
Take a look at this [documentation](https://docs.golem.network/docs/creators/ray).

While doing that consider its clarity, purpose, structure & completeness - we will be asking about this at the end.
The direction we should take with the docs is an important aspect of the Preview Program for us.

### The code
Take a look at this [piece of code](https://github.com/golemfactory/ray-on-golem/raw/main/examples/hash_cracker_ray_ready.py).

It takes a sha256 hash of some unknown word as input and looks for a word that results in a match.
The code doesn't know anything about Golem or Ray.

```bash
python hash_cracker_ray_ready.py -l 4 -n 16 de6c0da53ac2bf2b6954e400767106011e4471db7a412cce0388e3441e0ad2ec
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

We designed the example code so that it's easily parallelizable and allows precise control over the sizes of individual tasks.
While it may seem overly complex initially, its structure should make it straightforward to convert to Ray on Golem.

One additional challenge (and a learning opportunity) here is that we would like to avoid waiting for Ray on Golem to scan the whole of the word space.
We would like the code to stop the computation when it finds the match. 
You might wish to use Ray mechanisms which are not directly described in our docs for Ray on Golem.
We suggest you check out the `ray.wait()` function, which allows you to retrieve individual results as soon as they're ready instead of waiting for all of them to finish.

### Acceptance criteria 

In the end, we would like a code that finds the word: `golem`, represented by the hash: `4c5cddb7859b93eebf26c551518c021a31fa0013b2c03afa5b541cbc8bd079a6` in 10 minutes, using Ray on Golem.
The 10-minute criterion is not critical - the main point is for you to think of ways to optimize the time it takes the Ray on Golem cluster to find the solution.

Please don't hesitate to talk to us on [Discord: `#Ray on Golem` channel`](https://discord.gg/golem) - we would love to see what you struggle with.
At the same time, we don't want to waste your time on powering through the rough edges of our young product.

### Fill out the submission form

The final step is to submit your solution, the logs, and your feedback via the [submission form](https://qkjx8blh5hm.typeform.com/to/UlpvzPrD).

Remember that your insights have the power to refine and propel Ray on Golem forward.
Apart from the solution to the above task, the most attractive feedback for us would be your ideas for real-life Ray on Golem applications.
Ideally, the ones that you would like to implement yourself.
We need reference usages and are willing to actively support their potential creators.
