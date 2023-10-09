import time
import timeit
import ray

ray.init()

dupa = 123


@ray.remote
def func(v):
    global dupa
    dupa += 1
    print(f"computing {v} {dupa}...")
    time.sleep(3)  # sleep three seconds
    return dupa


def main():
    results = list()

    for i in range(0, 32):  # “calculate” for eight values
        result = func.remote(i)
        results.append(result)

    print(f"finished! {ray.get(results)}")


print(timeit.timeit(main, number=1))
