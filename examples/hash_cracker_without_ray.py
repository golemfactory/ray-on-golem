import argparse
from datetime import datetime
from hashlib import sha256
from itertools import chain

# some sample phrases to crack
#
# 'G0!3m':   070063ad89872aaa0fc0a2f170be5641e9c5d201d25b76703a4be3ee3848016c
# 'golem':   4c5cddb7859b93eebf26c551518c021a31fa0013b2c03afa5b541cbc8bd079a6
# `test`:    9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
# `foo`:     2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae
# `glm`:     2bf548d8056029c73e6e28132d19a3a277a49daf32b1c1ba7b0b7fc7e78bf5cd
# `be`:      46599c5bb5c33101f80cea8438e2228085513dbbb19b2f5ce97bd68494d3344d
# `x`:       2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881

CHARS = [
    chr(c)
    for c in chain(
        range(ord("a"), ord("z") + 1),
        range(ord("A"), ord("Z") + 1),
        range(ord("0"), ord("9") + 1),
        range(ord(" "), ord("/") + 1),
        range(ord(":"), ord("@") + 1),
        range(ord("["), ord("`") + 1),
        range(ord("{"), ord("~") + 1),
    )
]

start_time = datetime.now()

parser = argparse.ArgumentParser()
parser.add_argument("-w", "--words", type=str, help="dictionary file")
parser.add_argument(
    "-l",
    "--length",
    type=int,
    default=0,
    help="brute force length (if the `words` dictionary is not provided), default: %(default)s",
)
parser.add_argument("hash", type=str)
args = parser.parse_args()


def word_file(words_file: str):
    with open(words_file) as f:
        for line in f:
            yield bytes(line.strip(), "utf-8")


def brute_force(max_len: int):
    def brute_force_len(length: int):
        for char in CHARS:
            if length <= 1:
                yield char
            else:
                for suffix in brute_force_len(length - 1):
                    yield char + suffix

    for l in range(1, max_len + 1):
        for word in brute_force_len(l):
            yield bytes(word, "utf-8")


result = None

if args.words:
    words = word_file(args.words)
else:
    words = brute_force(args.length)

for word in words:
    word_hash = sha256(word).hexdigest()
    if word_hash == args.hash:
        result = word.decode("utf-8")
        break

print(
    f"finished in {datetime.now() - start_time},",
    f"match found: {result}" if result else f"match not found",
)
