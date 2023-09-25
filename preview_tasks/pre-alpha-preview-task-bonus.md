
### (Bonus task) Parallelize the hash cracker script with Ray and execute it on Ray on Golem

Take a look at this [piece of code](https://github.com/golemfactory/ray-on-golem/raw/main/examples/hash_cracker_ray_ready.py)

It takes a sha256 hash of some unknown word as an input and looks for a word that results in a match.
The code doesn't know anything about Golem nor Ray.

```bash
python hash_cracker_ray_ready.py -l 4 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
```
```
finished in 0:00:40.953827, match found: test
```

You can find a couple of other hashes to crack in the code's comments.


Your task is to parallelize the code and execute it on Ray on Golem cluster.
The goal is to benefit from distributed execution on Ray on Golem cluster so that it takes less time than executed locally.

Please send us your code and console output from running the code on Ray on Golem.

As a result of this task, we'd like to learn whether, and how, our documentation helped you run such an arbitrary piece of python code on a Ray on Golem cluster.

