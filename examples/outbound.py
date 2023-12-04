import argparse
import colorful
import requests
import socket
from dataclasses import dataclass
from datetime import datetime, timedelta
from traceback import print_exc
from typing import Set, List, Tuple
from urllib.request import urlopen, Request

urls = [
    'https://ipfs.io/ipfs/QmZtmD2qt6fJot32nabSP3CUjicnypEBz7bHVDhPQt9aAy',
    'https://ipfs.io/ipfs/QmTudJSaoKxtbEnTddJ9vh8hbN84ZLVvD5pNpUaSbxwGoa',
    'https://ipfs.io/ipfs/bafkreiemev2isidd7gk7352wxtqh6rwbuumt4vgnkkbx5wi6giaizt2bvq',
    'https://ipfs.io/ipfs/bafkreigks6arfsq3xxfpvqrrwonchxcnu6do76auprhhfomao6c273sixm',
    'https://ipfs.io/ipfs/bafkreifb7tsdmocu76eiz72lrz4hlvqayjuchecbfkgppgzx2cyrcsfq7i',
    'https://ipfs.io/ipfs/bafkreiaplag3id7ckuzs6eiwca3skuheddup7p7espat5omqv6r7m2byhi',
    'https://ipfs.io/ipfs/bafkreibthyfb4j4blugo5zk4i476hxet2vwghy564kz3jlxi53lnoamrum',
    'https://ipfs.io/ipfs/bafkreidfy5gbljugdb53no7zswhust6gxaagqa2kmwnjvvcjsgyiywhs2i',
    'https://ipfs.io/ipfs/bafkreifmvsdmbzqjzkig6yzlbyw2ztfsw56sfmdcd4qox3hbusbvxe7w6a',
    'https://ipfs.io/ipfs/bafkreib7pg5xwq23auzbmuo257jxjtogqhoan6vgly3u4obtpoemubdn5i',
    'https://ipfs.io/ipfs/bafkreidcyzvhuxoxbqyumymampbujzjr43kllhrxtaeeiphjmkz2xvr4li',
    'https://ipfs.io/ipfs/bafkreibwvht7dsk3ql73tf2d4dc4jtuv3a6juqykvrm7qtxtzp5lmfcqna',
    'https://ipfs.io/ipfs/bafkreihwavxppciktfeuynevdal4f3kp2nqivbei54fon4vpvsj625ufjy',
    'https://ipfs.io/ipfs/bafkreif3oielzg25pqcpci3kqkqasos6gp2aii6vxkguezxxbewdxjb3mi',
]

DEFAULT_NUM_REQUESTS = 128
DEFAULT_NUM_ATTEMPTS = 3
DEFAULT_TIMEOUT = 10

import ray
ray.init()


@dataclass
class UrlResult:
    node_ip: str
    url: str
    length: int
    success: bool
    attempts: int
    errors: Set
    times: List[str]
    total_time: float


def exc_causes(e: BaseException):
    causes = [f"{type(e)}: {e}"]
    if e.__cause__:
        causes.extend(exception_causes(e.__cause__))
    return causes


@ray.remote
def get_url_len(url: str, num_attempts: int, timeout: int, keep_alive: bool) -> UrlResult:
    node_ip = socket.gethostbyname(socket.gethostname())
    start = datetime.now()

    def seconds():
        return (datetime.now() - start).total_seconds()

    print(f"Processing: {url}")
    errors = set()
    times = list()
    attempt = 0
    while attempt < num_attempts:
        try:
            attempt += 1
            if not keep_alive:
                headers = {}
            else:
                headers = {
                    "Connection": "Keep-Alive",
                    "Keep-Alive": "timeout=60, max=10"
                }
            response = requests.get(url, timeout=timeout, headers=headers)
            if response.status_code == 200:
                html = response.content
                times.append(f"{seconds():.3f}: ok {attempt}")
                return UrlResult(
                    node_ip, url, len(html), True, attempt, errors, times, seconds()
                )
            else:
                times.append(f"{seconds():.3f}: err {attempt}")
                errors.add(response.status_code)
        except Exception as e:
            times.append(f"{seconds():.3f}: exc {attempt}")
            errors.add(str(exc_causes(e)))

    return UrlResult(node_ip, url, -1, False, attempt, errors, times, seconds())


def get_urls(n):
    for i in range(n):
        yield urls[i % len(urls)] + f"#i={i}"


parser = argparse.ArgumentParser()
parser.add_argument("-r", "--num-requests", type=int, default=DEFAULT_NUM_REQUESTS)
parser.add_argument("-a", "--num-attempts", type=int, default=DEFAULT_NUM_ATTEMPTS)
parser.add_argument("-t", "--timeout", type=int, default=DEFAULT_TIMEOUT)
parser.add_argument("-k", "--keep-alive", dest="keep_alive", action="store_true")
parser.add_argument("-K", "--no-keep-alive", dest="keep_alive", action="store_false")
args = parser.parse_args()

refs = [
    get_url_len.remote(
        url, num_attempts=args.num_attempts, timeout=args.timeout, keep_alive=args.keep_alive
    ) for url in get_urls(args.num_requests)
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
