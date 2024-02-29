"""numba/cuda-on-ray equivalent of hello world"""
import math

import numpy as np
import ray
from numba import cuda


def test(v: np.array):
    x, y = cuda.grid(2)
    v[x, y] = 1


@ray.remote(num_gpus=1)
def cuda_test(width, height):
    res = np.zeros((width, height), dtype=np.uint8)

    block = (16, 16)
    grid = (math.ceil(width / block[0]), math.ceil(height / block[1]))
    print(block, grid)
    gpu_test = cuda.jit(test)[block, grid]
    gpu_test(res)
    return res


ray.init()
if ray.cluster_resources().get("GPU", 0) == 0:
    raise Exception("No GPUs available in this cluster.")

w = 512
h = 512

print(ray.get(cuda_test.remote(w, h)))
