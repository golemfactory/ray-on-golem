import argparse
import colorful
from datetime import datetime
from dataclasses import dataclass, field
import dns.message
import dns.name
import dns.resolver
import dns.query
import itertools
import os
import ray
import socket
from typing import Callable, Dict, List, Literal, Optional, Set

NAMES = [
    "ipfs.io",
    "golem.network",
    "google.com",
    "github.com",
    "duckduckgo.com",
]

DEFAULT_NUM_REQUESTS = 256
DEFAULT_NUM_ATTEMPTS = 3
DEFAULT_TIMEOUT = 10

ResultType = Literal["ok", "problem", "error"]



@dataclass
class Result:
    node_ip: str
    node_pid: str
    nameserver: str
    name: str
    ips: List[str]
    success: bool = True
    attempts: int = 1
    errors: Set = field(default_factory=set)
    times: List[str] = field(default_factory=list)
    total_time: Optional[str] = None


def result_color(r: Result) -> Callable:
    color_map = {
        "ok": colorful.bold_green,
        "problem": colorful.bold_yellow,
        "error": colorful.bold_red,
    }
    return color_map[result_type(r)]


def result_type(r: Result) -> ResultType:
    if r.success:
        if not r.errors:
            return "ok"
        else:
            return "problem"
    return "error"


@dataclass
class ResultSummary:
    ok: List[Result] = field(default_factory=list)
    problem: List[Result] = field(default_factory=list)
    error: List[Result] = field(default_factory=list)

    def all(self) -> List[Result]:
        return list(itertools.chain(self.ok, self.problem, self.error))

    def count_hosts(self) -> Dict:
        c = {}
        for r in self.all():
            c.setdefault(r.node_ip, {"all": 0, "ok": 0, "problem": 0, "error": 0})
            c[r.node_ip]["all"] += 1
            c[r.node_ip][result_type(r)] += 1

        return c

    def count_all(self):
        return len(self.ok) + len(self.problem) + len(self.error)

    def summary(self):
        per_host_counts = [f"    {node_ip}: {cnt}" for node_ip, cnt in self.count_hosts().items()]

        return (
            f"all:     {self.count_all()}\n"
            f"    ok:      {len(self.ok)}\n"
            f"    problem: {len(self.problem)}\n"
            f"    bad:     {len(self.error)}\n"
            "\n\n"
            f"hosts: \n"
            +
            "\n".join(per_host_counts)
        )

    def add(self, result_type: Literal["ok", "problem", "error"], result: Result):
        l: List[Result] = getattr(self, result_type)
        l.append(result)


def exc_causes(e: BaseException):
    causes = [f"{type(e)}: {e}"]
    if e.__cause__:
        causes.extend(exc_causes(e.__cause__))
    return causes


def query_name(ns: str, name: str, timeout: Optional[int] = None):
    q = dns.message.make_query(name, dns.rdatatype.A)
    r = dns.query.udp(q, ns, timeout=timeout)
    ips = list()
    for a in r.answer:
        for i in a.items:
            ips.append(i.address)

    return ips, r


def perform_query(ns: str, name: str, num_attempts: int = 1, timeout: Optional[int] = None):
    node_ip = socket.gethostbyname(socket.gethostname())
    node_pid = str(os.getpid())
    start = datetime.now()

    def seconds():
        return f"{((datetime.now() - start).total_seconds()):.3f}"

    print(f"{node_ip}: querying: {name} on {ns}")

    errors = set()
    times = list()
    attempt = 0
    while attempt < num_attempts:
        try:
            attempt += 1
            ips, r = query_name(ns, name, timeout)
            return Result(node_ip, node_pid, ns, name, ips, True, attempt, errors, times, seconds())
        except Exception as e:
            times.append(seconds())
            errors.add(str(exc_causes(e)))

    return Result(node_ip, node_pid, ns, name, [], False, attempt, errors, times, seconds())


@ray.remote
def perform_queries(name: str, num_attempts: int = 1, timeout: Optional[int] = None):
    results = list()
    for ns in dns.resolver.Resolver().nameservers:
        results.append(perform_query(ns, name, num_attempts, timeout))

    return results


def get_names(names, n):
    for i in range(n):
        yield names[i % len(names)]


parser = argparse.ArgumentParser()
parser.add_argument("-r", "--num-requests", type=int, default=DEFAULT_NUM_REQUESTS)
parser.add_argument("-a", "--num-attempts", type=int, default=DEFAULT_NUM_ATTEMPTS)
parser.add_argument("-t", "--timeout", type=int, default=DEFAULT_TIMEOUT)
args = parser.parse_args()

print(colorful.bold_white(f"Running with: {vars(args)}"))

ray.init()

refs = [
    perform_queries.remote(
        url, num_attempts=args.num_attempts, timeout=args.timeout,
    )
    for url in get_names(NAMES, args.num_requests)
]

summary = ResultSummary()

while refs:
    ready, refs = ray.wait(refs)
    for ref in ready:
        url_results: List[Result] = ray.get(ref)
        out = ""
        for url_result in url_results:
            color = result_color(url_result)
            out += f"{color(url_result)}\n"
            summary.add(result_type(url_result), url_result)

        print(f"{out}{len(refs)}")

print(summary.summary())

