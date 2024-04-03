import argparse
import math
from datetime import datetime, timezone
from typing import NamedTuple, Optional, Tuple

import numba
import numpy as np
import ray
from numba import cuda
from PIL import Image

ZOOM_BASE = 2.0
VSCALE = np.uint8(255)
NUM_GPUS = 0.1

print_verbose = print


class ScrCoords(NamedTuple):
    x: int
    y: int


def calculate_mandel_gpu(
    buffer: np.array,
    start_x: np.float64,
    end_x: np.float64,
    x_size: np.uint,
    start_y: np.float64,
    end_y: np.float64,
    y_size: np.uint,
    max_iter: np.uint,
) -> np.array:
    def mandel(c: complex) -> np.uint8:
        z = complex(0, 0)
        i = np.uint(0)

        while abs(z) < 2 and i < max_iter:
            z = z * z + c
            i += 1

        return np.uint8(i / max_iter * VSCALE)

    x_step = (end_x - start_x) / x_size
    y_step = (end_y - start_y) / y_size
    xs, ys = cuda.grid(2)
    buffer[ys, xs] = mandel(complex(start_x + xs * x_step, start_y + ys * y_step))


def calculate_mandel_cpu(
    buffer: np.array,
    start_x: np.float64,
    end_x: np.float64,
    x_size: np.uint,
    start_y: np.float64,
    end_y: np.float64,
    y_size: np.uint,
    max_iter: np.uint,
) -> np.array:
    def mandel(c: complex) -> np.uint8:
        z = complex(0, 0)
        i = np.uint(0)

        while abs(z) < 2 and i < max_iter:
            z = z * z + c
            i += 1

        return np.uint8(i / max_iter * VSCALE)

    x_step = (end_x - start_x) / x_size
    y_step = (end_y - start_y) / y_size

    for ys in range(y_size):
        y = start_y + ys * y_step
        for xs in range(x_size):
            x = start_x + xs * x_step
            buffer[ys, xs] = mandel(complex(x, y))


def calculate_mandel_chunk(
    tgt_range_x: Tuple[int, int],
    tgt_range_y: Tuple[int, int],
    space_x: np.linspace,
    space_y: np.linspace,
    max_iter: int,
    use_gpu: bool,
):
    tgt_size_x = tgt_range_x[1] - tgt_range_x[0]
    tgt_size_y = tgt_range_y[1] - tgt_range_y[0]
    buffer = np.zeros((tgt_size_y, tgt_size_x), dtype=np.uint8)
    print_verbose(f"starting chunk: {tgt_range_x}, {tgt_range_y}")

    if use_gpu:
        block = (32, 32)
        grid = (math.ceil(tgt_size_x / block[0]), math.ceil(tgt_size_y / block[1]))
        mandel_func = cuda.jit(calculate_mandel_gpu)[grid, block]
    else:
        mandel_func = numba.jit(nopython=False)(calculate_mandel_cpu)

    mandel_func(
        buffer,
        space_x[tgt_range_x[0]],
        space_x[tgt_range_x[1] - 1],
        tgt_size_x,
        space_y[tgt_range_y[0]],
        space_y[tgt_range_y[1] - 1],
        tgt_size_y,
        np.uint(max_iter),
    )

    print_verbose(f"finalized chunk: {tgt_range_x}, {tgt_range_y}")
    return buffer


def draw_mandelbrot(
    size: ScrCoords,
    x_range: Tuple[float, float],
    y_range: Tuple[float, float],
    max_iter: int,
    num_chunks: int = 1,
    output_file: Optional[str] = None,
    use_ray: bool = True,
    use_gpu: bool = False,
):
    chunks = list()

    chunk_size = math.ceil(size.y / num_chunks)

    for c in range(0, num_chunks):
        start_y = c * chunk_size
        end_y = min(start_y + chunk_size, size.y)

        if end_y <= start_y:
            break

        calc_args = (
            (0, size.x),
            (start_y, end_y),
            np.linspace(x_range[0], x_range[1], size.x),
            np.linspace(y_range[0], y_range[1], size.y),
            max_iter,
            use_gpu,
        )
        if not use_ray:
            f = calculate_mandel_chunk
        elif not use_gpu:
            f = ray.remote(calculate_mandel_chunk).remote
        else:
            f = ray.remote(num_gpus=NUM_GPUS)(calculate_mandel_chunk).remote

        print_verbose(f"{datetime.now()}: scheduling: {c}: {f}({calc_args[0], calc_args[1]})")
        chunks.append(f(*calc_args))

    print(f"{datetime.now()}: finished scheduling")

    img = Image.new("L", (size.x, size.y))

    for c in range(0, num_chunks):
        start_y = c * chunk_size
        end_y = min(start_y + chunk_size, size.y)

        if end_y <= start_y:
            break

        chunk = chunks.pop(0)

        if use_ray:
            chunk = ray.get(chunk)

        chunk_img_size = (size.x, end_y - start_y)
        box = (0, start_y)

        print_verbose(f"{datetime.now()}: got chunk {c}, size: {chunk_img_size}, box: {box}")

        chunk_img = Image.frombytes("L", size=chunk_img_size, data=bytearray(chunk.data))
        img.paste(chunk_img, box=box)

        print_verbose(f"{datetime.now()}: processed chunk {c}")

    img.show()

    current_time_str = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S%z")
    filename = output_file or f"mandel-{size.x}x{size.y}-{current_time_str}.png"
    img.save(filename, "PNG")

    print(f"{datetime.now()}: saved as {filename}")


def argument_parser():
    parser = argparse.ArgumentParser("mandelbrot on ray")
    parser.add_argument(
        "-s",
        "--size",
        nargs=2,
        metavar=("X", "Y"),
        help="size of the output image, default=%(default)s",
        type=int,
        default=(500, 500),
    )
    parser.add_argument(
        "-c",
        "--center",
        nargs=2,
        metavar=("X", "Y"),
        help="center of the drawn region, default=%(default)s",
        type=float,
        default=(-0.743643135, 0.131825963),
    )
    parser.add_argument(
        "-z",
        "--zoom",
        help="magnification of the drawn region, default=%(default)s",
        type=float,
        default=200000,
    )
    parser.add_argument(
        "-i",
        "--max-iterations",
        help="maximum number of iterations to perform per pixel, default=%(default)s",
        type=int,
        default=500,
    )
    parser.add_argument(
        "-n",
        "--num-chunks",
        help="number of chunks to divide output into, default=%(default)s",
        type=int,
        default=16,
    )
    parser.add_argument(
        "-f",
        "--output-file",
        help="name of file to save output into, defaults to predefined template",
        type=str,
        nargs="?",
    )
    parser.add_argument(
        "--ray-num-cpus",
        help="number of CPUs for ray to use",
        type=int,
    )
    parser.add_argument("-r", "--use-ray", action="store_true", help="use ray")
    parser.add_argument(
        "-R", "--no-use-ray", dest="use_ray", action="store_false", help="don't use ray"
    )
    parser.add_argument("-g", "--use-gpu", action="store_true", help="use GPU")
    parser.add_argument(
        "-G", "--no-use-gpu", dest="use_gpu", action="store_false", help="don't use GPU"
    )
    parser.add_argument("-q", "--quiet", help="Decrease verbosity", action="store_true")
    parser.set_defaults(use_ray=True, use_gpu=True)

    return parser


####


start = datetime.now()
print(f"{start}: starting...")

args = argument_parser().parse_args()

if args.quiet:
    print_verbose = lambda _: None

if args.use_ray:
    ray.init(num_cpus=args.ray_num_cpus)

    if args.use_gpu and ray.cluster_resources().get("GPU", 0) == 0:
        raise Exception("No GPUs available in this cluster.")

aspect_ratio = args.size[0] / args.size[1]

print(f"{datetime.now()}: drawing using {vars(args)}")

draw_mandelbrot(
    size=ScrCoords(args.size[0], args.size[1]),
    x_range=(args.center[0] - ZOOM_BASE / args.zoom, args.center[0] + ZOOM_BASE / args.zoom),
    y_range=(
        args.center[1] - ZOOM_BASE / (args.zoom * aspect_ratio),
        args.center[1] + ZOOM_BASE / (args.zoom * aspect_ratio),
    ),
    max_iter=args.max_iterations,
    num_chunks=args.num_chunks,
    output_file=args.output_file,
    use_ray=args.use_ray,
    use_gpu=args.use_gpu,
)

print(f"{datetime.now()}: finished. elapsed time: {datetime.now() - start}")
