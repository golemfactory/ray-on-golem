import urllib.request

urls = [
    "https://gutenberg.org/cache/epub/1342/pg1342.txt",
    #  'https://gutenberg.org/cache/epub/1342/pg1342.txt',
    #  'https://gutenberg.org/cache/epub/1342/pg1342.txt',
    #  'https://gutenberg.org/cache/epub/1342/pg1342.txt',
]

import ray

ray.init()


@ray.remote
def get_url_len(url):
    print(url)
    response = urllib.request.urlopen(url)
    print("opened", url)
    html = response.read()
    print("read", url)
    return (url, len(html))


refs = [get_url_len.remote(url) for url in urls]

results = ray.get(refs)

for url, length in results:
    print(url, ":", length, "bytes")
