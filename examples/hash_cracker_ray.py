import argparse
import itertools
import math
from datetime import datetime
from hashlib import sha256
from typing import Optional

import ray

# some sample phrases to crack
#
# 'G0!3m':   070063ad89872aaa0fc0a2f170be5641e9c5d201d25b76703a4be3ee3848016c
# 'golem':   4c5cddb7859b93eebf26c551518c021a31fa0013b2c03afa5b541cbc8bd079a6
# '9Lm!':    de6c0da53ac2bf2b6954e400767106011e4471db7a412cce0388e3441e0ad2ec
# `test`:    9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
# `foo`:     2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae
# `glm`:     2bf548d8056029c73e6e28132d19a3a277a49daf32b1c1ba7b0b7fc7e78bf5cd
# `be`:      46599c5bb5c33101f80cea8438e2228085513dbbb19b2f5ce97bd68494d3344d
# `x`:       2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881

# the character table that we want to use to construct possible phrases
CHARS = [
    chr(c)
    for c in itertools.chain(
        range(ord("a"), ord("z") + 1),
        range(ord("A"), ord("Z") + 1),
        range(ord("0"), ord("9") + 1),
        range(ord(" "), ord("/") + 1),
        range(ord(":"), ord("@") + 1),
        range(ord("["), ord("`") + 1),
        range(ord("{"), ord("~") + 1),
    )
]

parser = argparse.ArgumentParser()
parser.add_argument(
    "-l", "--length", type=int, default=3, help="brute force length, default: %(default)s"
)
parser.add_argument(
    "-n",
    "--num-chunks",
    help="number of chunks to divide the range into, default=%(default)s",
    type=int,
    default=16,
)
parser.add_argument("hash", type=str)
args = parser.parse_args()


def str_to_int(value: str) -> int:
    """
    Convert a string to its numerical value.

    Each character in the string is treated as a non-zero digit
    (the value of which is the index in the CHARS table)
    in a base equal to the length of the CHARS table.

    :param value: the string of "digits" to convert
    :return: its integer value after conversion from base[len(chars)]
    """

    base = len(CHARS) + 1
    intval = 0
    for position, digit in zip(itertools.count(), [CHARS.index(v) + 1 for v in reversed(value)]):
        intval += digit * base**position

    return intval


def int_to_str(intval: int, round_nulls=False) -> Optional[str]:
    """
    Convert an integer value back to the equivalent string.

    Treats the CHARS table as a table of "digits" in
    a numerical system with a base equal to the length of the CHARS table.

    :param intval: the integer value to convert
    :param round_nulls: whether to round a "number" containing null values to the closest proper string.
        if set to False, `int_to_str` will just return a `None`
    :return: the resultant string
    """
    div = intval
    output = ""
    base = len(CHARS) + 1
    while div > 0:
        div, mod = divmod(div, base)
        if mod > 0:
            output = CHARS[mod - 1] + output
        elif round_nulls:
            # "round up"
            output = CHARS[0] * (len(output) + 1)
        else:
            return None

    return output


@ray.remote
def scan_range(searched_hash: str, start: int, end: int):
    print(
        f"scanning: {searched_hash}: {int_to_str(start, True)}, {int_to_str(end, True)}",
    )
    for i in range(start, end):
        word = int_to_str(i)
        if word:
            word_hash = sha256(bytes(word, "utf-8")).hexdigest()
            if word_hash == searched_hash:
                return word


start_time = datetime.now()

ray.init()

result = None
results = []

start_space = str_to_int(CHARS[0])
end_space = str_to_int(CHARS[0] * (args.length + 1))
chunk_size = math.ceil((end_space - start_space) / args.num_chunks)

for c in range(0, args.num_chunks):
    start_chunk = start_space + c * chunk_size
    end_chunk = min(end_space, start_chunk + chunk_size)
    results.append(scan_range.remote(args.hash, start_chunk, end_chunk))

print(datetime.now(), ": scheduled...")

while not result:
    ready, results = ray.wait(results, num_returns=1)
    for r in ready:
        result = ray.get(r)
        if result:
            print("found!")
            break
        else:
            print("miss...")

print(
    f"finished in {datetime.now() - start_time},",
    f"match found: {result}, skipped chunks: {len(results)}" if result else f"match not found",
)
