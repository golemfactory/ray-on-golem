import argparse
from datetime import datetime, timezone
from functools import partial
from typing import Any, Dict

import numpy as np
import ray

MB = 1024 * 1024
FRAME_SIZE = (3, 400, 300)


def log(msg, *args, **kwargs):
    print(f"{datetime.now(timezone.utc).isoformat()} {msg}", *args, **kwargs)


def dummy_video_file(i: int, size_mb: int):
    return "0" * size_mb * MB


def decode_frames(frames_per_video: int, batch: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    return {"frames": np.ones((frames_per_video,) + FRAME_SIZE, dtype=int)}


class FrameAnnotator:
    def __init__(self):
        def dummy_annotate(frames):
            # return frames.ravel()
            return frames.flatten()

        self.model = dummy_annotate

    def __call__(self, batch: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        frames = batch["frames"]
        return {"annotated_frames": self.model(frames)}


class FrameClassifier:
    def __init__(self):
        def dummy_classify(frames):
            return ["dummy_result" * len(frames)]  # dummy

        self.model = dummy_classify

    def __call__(self, batch: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        frames = batch["annotated_frames"]
        return {"results": self.model(frames)}


def run_ray_data(
    num_actors,
    num_cpu,
    output_mode,
    output_kwargs: Dict[Any, Any],
    num_videos,
    video_size_mb,
    frames_per_video,
):
    # enable verbose output
    log("enable verbose output")
    ray.data.DataContext.get_current().execution_options.verbose_progress = True

    # Create a datastream from in-memory dummy base data.
    log("Create a datastream from in-memory dummy base data.")
    ds = ray.data.from_items(
        [dummy_video_file(i, video_size_mb) for i in range(num_videos)], parallelism=num_videos
    )

    # Apply the decode step. We can customize the resources per
    # task. Here each decode task requests `num_cpu` CPUs.
    log("Apply the decode step. We can customize the resources per task.")
    ds = ds.map_batches(partial(decode_frames, frames_per_video), num_cpus=num_cpu)

    # Apply the annotation step, using an actor pool of size `num_actors`. We
    # will also request `num_cpu` CPUs per actor here.
    log(" Apply the annotation step, using an actor pool of size {num_actors}")
    ds = ds.map_batches(FrameAnnotator, concurrency=num_actors)

    # Trigger execution and write output to `output_mode`.
    log(f"Trigger execution and write output to {output_mode}.")
    OUTPUT_MODE[output_mode]["WRITE"](ds, **output_kwargs)

    log("Ray Data example finished successfully.")


# output
def handle_json_kwargs(args):
    kwargs = {"path": args.json_path}
    log(f"set to save result JSON files to `{kwargs['path']}`")

    return kwargs


def handle_json_output(ds, **kwargs):
    ds.write_json(**kwargs)


def handle_s3_kwargs(args):
    from s3fs import S3FileSystem
    from pyarrow.fs import PyFileSystem, FSSpecHandler

    kwargs = {
        "path": args.s3_bucket,
        "filesystem": PyFileSystem(
            FSSpecHandler(
                S3FileSystem(
                    key=args.s3_access_key,
                    secret=args.s3_secret_key,
                    client_kwargs={"endpoint_url": args.s3_url},
                )
            )
        ),
    }
    return kwargs


def handle_s3_output(ds, **kwargs):
    ds.write_json(**kwargs)


def ensure_mongo_collection(uri, database, collection):
    import pymongo

    myclient = pymongo.MongoClient(uri)
    mydb = myclient[database]
    mycol = mydb[collection]

    mycol.insert_one({})
    if database in myclient.list_database_names():
        log(f"{database} available in Mongo")
    if collection in mydb.list_collection_names():
        log(f"{collection} available in Mongo")


def handle_mongo_kwargs(args):
    kwargs = {
        "uri": args.mongo_uri,
        "database": args.mongo_database,
        "collection": args.mongo_collection,
    }
    ensure_mongo_collection(**kwargs)

    return kwargs


def handle_mongo_output(ds, **kwargs):
    ds.write_mongo(**kwargs)


OUTPUT_MODE = {
    "json": {
        "KWARGS": handle_json_kwargs,
        "WRITE": handle_json_output,
    },
    "s3": {
        "KWARGS": handle_s3_kwargs,
        "WRITE": handle_s3_output,
    },
    "mongo": {
        "KWARGS": handle_mongo_kwargs,
        "WRITE": handle_mongo_output,
    },
}


def parse_arguments():
    parser = argparse.ArgumentParser("ray data example")
    # ray
    parser.add_argument(
        "-a",
        "--num-actors",
        help="number of actors, default=%(default)s",
        type=int,
        default=2,
    )
    parser.add_argument(
        "-n",
        "--num-cpu",
        help="number of CPU per actor, default=%(default)s",
        type=int,
        default=1,
    )
    # input - generated
    parser.add_argument(
        "-v",
        "--num-videos",
        help="number of videos to compute, default=%(default)s",
        type=int,
        default=6,
    )
    parser.add_argument(
        "-f",
        "--num-frames",
        help="number of frames per video to compute, default=%(default)s",
        type=int,
        default=4,
    )
    parser.add_argument(
        "-s",
        "--video-size-mb",
        help="size of each video in mb, default=%(default)s",
        type=int,
        default=1,
    )
    # output
    parser.add_argument(
        "-o",
        "--output-mode",
        help="Output Mode, default=%(default)s",
        type=str,
        choices=OUTPUT_MODE.keys(),
        default="json",
    )
    # output - json
    parser.add_argument(
        "-jp",
        "--json-path",
        help="Json write path, default=%(default)s",
        type=str,
        default="/tmp/ray-data",
    )
    # output - s3
    parser.add_argument(
        "-su",
        "--s3-url",
        help="S3 URL, default=%(default)s",
        type=str,
        default="http://localhost:9000/",
    )
    parser.add_argument(
        "-sb",
        "--s3-bucket",
        help="S3 Bucket, default=%(default)s",
        type=str,
        default="s3://ray-data-bucket",
    )
    parser.add_argument(
        "-sa",
        "--s3-access-key",
        help="S3 Access Key, default=%(default)s",
        type=str,
        default="TLicrTuB3aH9KOsUHba8",
    )
    parser.add_argument(
        "-ss",
        "--s3-secret-key",
        help="S3 Secret Key, default=%(default)s",
        type=str,
        default="ePPbqY6vKbuBTwIjFSSmWNTh72sd3LMt1QzoaGwN",
    )
    # output - mongo
    parser.add_argument(
        "-mu",
        "--mongo-uri",
        help="MongoDB URI, default=%(default)s",
        type=str,
        default="mongodb://localhost:27017/",
    )
    parser.add_argument(
        "-md",
        "--mongo-database",
        help="MongoDB Database, default=%(default)s",
        type=str,
        default="ray_data_db",
    )
    parser.add_argument(
        "-mc",
        "--mongo-collection",
        help="MongoDB Collection, default=%(default)s",
        type=str,
        default="ray_data_collection",
    )

    return parser.parse_args()


def main():
    args = parse_arguments()
    run_ray_data(
        num_actors=args.num_actors,
        num_cpu=args.num_cpu,
        output_mode=args.output_mode,
        output_kwargs=OUTPUT_MODE[args.output_mode]["KWARGS"](args),
        num_videos=args.num_videos,
        video_size_mb=args.video_size_mb,
        frames_per_video=args.num_frames,
    )


if __name__ == "__main__":
    main()
