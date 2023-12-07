import colorful
import requests

urls = [
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

import ray
ray.init()

@ray.remote
def get_url(url):

    attempt = 0
    while attempt < 8:
        attempt += 1
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                text = response.content.decode()
                return (url, text)
            else:
                print(url, "failure #"+str(attempt), response.status_code)
        except Exception as e:
            print(url, "failure #"+str(attempt), e)

    return (url, "?")

refs = [get_url.remote(url) for url in urls]

results = ray.get(refs)

aggregate_text = ""

for (url, text) in results:
    print(url, "->", text) 
    aggregate_text += text

print(colorful.purple(f"\n{aggregate_text}"))
