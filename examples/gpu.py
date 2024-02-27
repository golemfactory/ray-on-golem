import math
import numpy
import numpy as np
from numba import cuda
import ray


def test(v: np.array):
    x, y = cuda.grid(2)
    v[x, y] = 1


@ray.remote(num_gpus=1)
def cuda_test(width, height):
    res = numpy.zeros((width, height), dtype=numpy.uint8)

    block = (16, 16)
    grid = (math.ceil(width / block[0]), math.ceil(height / block[1]))
    print(block, grid)
    gpu_test = cuda.jit(test)[block, grid]
    gpu_test(res)
    return res


ray.init()

w = 512
h = 512

print(ray.get(cuda_test.remote(w, h)))
