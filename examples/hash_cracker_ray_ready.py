import argparse
import itertools
from datetime import datetime
from hashlib import sha256
from typing import Optional

# `test`: 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
# `foo`:  2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae
# `glm`:  2bf548d8056029c73e6e28132d19a3a277a49daf32b1c1ba7b0b7fc7e78bf5cd
# `be`:   46599c5bb5c33101f80cea8438e2228085513dbbb19b2f5ce97bd68494d3344d
# `x`:    2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881

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

start_time = datetime.now()

parser = argparse.ArgumentParser()
parser.add_argument(
    "-l", "--length", type=int, default=3, help="brute force length, default: %(default)s"
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


def brute_force_range(start_string: str, end_string: str):
    for i in range(str_to_int(start_string), str_to_int(end_string)):
        s = int_to_str(i)
        if s:
            yield bytes(s, "utf-8")


result = None

words = brute_force_range(CHARS[0], CHARS[0] * (args.length + 1))

for word in words:
    word_hash = sha256(word).hexdigest()
    if word_hash == args.hash:
        result = word.decode("utf-8")
        break


print(
    f"finished in {datetime.now() - start_time},",
    f"match found: {result}" if result else f"match not found",
)
