import argparse
import math
import numba
import numpy as np
from datetime import datetime, timezone
from typing import NamedTuple, Optional, Tuple

import ray
from PIL import Image

ZOOM_BASE = 2.0


class ScrCoords(NamedTuple):
    x: int
    y: int


@numba.jit(nopython=False)
def calculate_mandel_cpu(
    buffer: np.array,
    tgt_range_x: Tuple[int, int],
    tgt_range_y: Tuple[int, int],
    space_x: np.linspace,
    space_y: np.linspace,
    max_iter: int,
) -> np.array:
    max_iter = np.uint(max_iter)
    vscale = np.uint8(255)

    def mandel(c: complex) -> np.uint8:
        z = complex(0, 0)
        i = np.uint(0)

        while abs(z) < 2 and i < max_iter:
            z = z * z + c
            i += 1

        return np.uint8(i / max_iter * vscale)

    for ys in range(tgt_range_y[0], tgt_range_y[1]):
        for xs in range(tgt_range_x[0], tgt_range_x[1]):
            c = complex(space_x[xs], space_y[ys])
            buffer[ys - tgt_range_y[0], xs - tgt_range_x[0]] = mandel(c)


def calculate_mandel(
    tgt_range_x: Tuple[int, int],
    tgt_range_y: Tuple[int, int],
    space_x: np.linspace,
    space_y: np.linspace,
    max_iter: int,
):
    tgt_size_x = tgt_range_x[1] - tgt_range_x[0]
    tgt_size_y = tgt_range_y[1] - tgt_range_y[0]
    buffer = np.zeros((tgt_size_y, tgt_size_x), dtype=np.uint8)
    print(f"starting chunk: {tgt_range_x}, {tgt_range_y}")
    calculate_mandel_cpu(buffer, tgt_range_x, tgt_range_y, space_x, space_y, max_iter)
    print(f"finalized chunk: {tgt_range_x}, {tgt_range_y}")
    return buffer


def draw_mandelbrot(
    size: ScrCoords,
    x_range: Tuple[float, float],
    y_range: Tuple[float, float],
    max_iter: int,
    num_chunks: int = 1,
    output_file: Optional[str] = None,
    use_ray: bool = True,
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
        )
        f = ray.remote(calculate_mandel).remote if use_ray else calculate_mandel

        print(f"{datetime.now()}: scheduling: {c}: {f}({calc_args[0], calc_args[1]})")
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

        print(f"{datetime.now()}: got chunk {c}, size: {chunk_img_size}, box: {box}")

        chunk_img = Image.frombytes("L", size=chunk_img_size, data=bytearray(chunk.data))
        img.paste(chunk_img, box=box)

        print(f"{datetime.now()}: processed chunk {c}")

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
    parser.set_defaults(use_ray=True)

    return parser


####


start = datetime.now()
print(f"{start}: starting...")

args = argument_parser().parse_args()

if args.use_ray:
    ray.init(num_cpus=args.ray_num_cpus)

aspect_ratio = args.size[0] / args.size[1]

print(f"{datetime.now()}: drawing...")

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
)

print(f"{datetime.now()}: finished. elapsed time: {datetime.now() - start}")
