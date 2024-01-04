import argparse
import socket
from dataclasses import dataclass
from datetime import datetime
from typing import List, Set

import colorful

names = [
    "ipfs.io",
    "golem.network",
    "google.com",
    "github.com",
    "duckduckgo.com",
]

DEFAULT_NUM_REQUESTS = 128
DEFAULT_NUM_ATTEMPTS = 3
DEFAULT_TIMEOUT = 10

import ray

ray.init()


@dataclass
class UrlResult:
    node_ip: str
    name: str
    ips: List[str]
    success: bool
    attempts: int
    errors: Set
    times: List[str]
    total_time: float


def exc_causes(e: BaseException):
    causes = [f"{type(e)}: {e}"]
    if e.__cause__:
        causes.extend(exc_causes(e.__cause__))
    return causes


@ray.remote
def resolve_name(name: str, num_attempts: int) -> UrlResult:
    node_ip = socket.gethostbyname(socket.gethostname())
    start = datetime.now()

    def seconds():
        return (datetime.now() - start).total_seconds()

    print(f"Processing: {name}")
    errors = set()
    times = list()
    attempt = 0
    while attempt < num_attempts:
        try:
            attempt += 1
            result = socket.gethostbyname_ex(name)
            return UrlResult(node_ip, name, result[2], True, attempt, errors, times, seconds())
        except Exception as e:
            times.append(f"{seconds():.3f}: exc {attempt}")
            errors.add(str(exc_causes(e)))

    return UrlResult(node_ip, name, [], False, attempt, errors, times, seconds())


def get_names(n):
    for i in range(n):
        yield names[i % len(names)]


parser = argparse.ArgumentParser()
parser.add_argument("-r", "--num-requests", type=int, default=DEFAULT_NUM_REQUESTS)
parser.add_argument("-a", "--num-attempts", type=int, default=DEFAULT_NUM_ATTEMPTS)
args = parser.parse_args()

print(colorful.bold_white(f"Running with: {vars(args)}"))

refs = [
    resolve_name.remote(
        url, num_attempts=args.num_attempts
    )
    for url in get_names(args.num_requests)
]

while refs:
    ready, refs = ray.wait(refs)
    for ref in ready:
        url_result: UrlResult = ray.get(ref)
        if url_result.success:
            if not url_result.errors:
                color = colorful.bold_green
            else:
                color = colorful.bold_yellow
        else:
            color = colorful.bold_red
        print(color(url_result), len(refs))
