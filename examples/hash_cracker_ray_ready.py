import argparse
from datetime import datetime
import itertools
from typing import Optional
from hashlib import sha256

# `test`: 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
# `foo`:  2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae
# `glm`:  2bf548d8056029c73e6e28132d19a3a277a49daf32b1c1ba7b0b7fc7e78bf5cd
# `be`:   46599c5bb5c33101f80cea8438e2228085513dbbb19b2f5ce97bd68494d3344d
# `x`:    2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881

# the chars
CHARS = [chr(c) for c in itertools.chain(
    range(ord("a"), ord("z") + 1),
    range(ord("A"), ord("Z") + 1),
    range(ord("0"), ord("9") + 1),
    range(ord(" "), ord("/") + 1),
    range(ord(":"), ord("@") + 1),
    range(ord("["), ord("`") + 1),
    range(ord("{"), ord("~") + 1),
)]

start_time = datetime.now()

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--length", type=int, default=3, help="brute force length, default: %(default)s")
parser.add_argument("hash", type=str)
args = parser.parse_args()


def str_to_index(value: str) -> int:
    base = len(CHARS) + 1
    index = 0
    for position, digit in zip(itertools.count(), [CHARS.index(v) + 1 for v in reversed(value)]):
        index += digit * base ** position

    return index


def index_to_str(index: int, round_nulls = False) -> Optional[str]:
    div = index
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


def brute_force_range(start_string: str, end_string: str):
    for i in range(str_to_index(start_string), str_to_index(end_string)):
        s = index_to_str(i)
        if s:
            yield bytes(s, "utf-8")


result = None

words = brute_force_range("a", "a" * (args.length + 1))

for word in words:
    word_hash = sha256(word).hexdigest()
    if word_hash == args.hash:
        result = word.decode("utf-8")
        break


print(
    f"finished in {datetime.now() - start_time},",
    f"match found: {result}" if result else f"match not found"
)
