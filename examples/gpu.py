import numpy
import numpy as np
import numba
from numba import cuda


def test(v: np.array):
    a, b = cuda.grid(2)
    v[0] = a
    v[1] = b


res = numpy.zeros(2, dtype=numpy.uint8)

gpu_test = cuda.jit(test)
gpu_test[1, 1](res)

# cpu_test = numba.jit(nopython=False)(test)
# cpu_test(res)

print(res)
