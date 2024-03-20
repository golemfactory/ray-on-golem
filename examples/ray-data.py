import numpy as np
from typing import Dict

import ray
from ray.data import ActorPoolStrategy

NUM_VIDEOS = 100
VIDEO_FILE_SIZE = 10 * 1024 * 1024
FRAMES_PER_VIDEO = 100
FRAME_SIZE = (3, 400, 300)

# connect to a running ray cluster
ray.init()


def dummy_video_file(i: int):
    return "0" * VIDEO_FILE_SIZE


def decode_frames(batch: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    return {"frames": np.ones((FRAMES_PER_VIDEO,) + FRAME_SIZE, dtype=np.uint8)}


class FrameAnnotator:
    def __init__(self):
        def dummy_annotate(frames):
            return frames  # no-op

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


# enable verbose output
ray.data.DataContext.get_current().execution_options.verbose_progress = True

# Create a datastream from in-memory dummy base data.
ds = ray.data.from_items(
    [dummy_video_file(i) for i in range(NUM_VIDEOS)], parallelism=NUM_VIDEOS
)

# Apply the decode step. We can customize the resources per
# task. Here each decode task requests 4 CPUs.
ds = ds.map_batches(decode_frames, num_cpus=4)

# Apply the annotation step, using an actor pool of size 5. We
# will also request 4 CPUs per actor here.
ds = ds.map_batches(FrameAnnotator, compute=ActorPoolStrategy(size=5))

# Trigger execution and write output to json.
ds.write_json("/tmp/ray-data/output")
