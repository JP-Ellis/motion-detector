#!/usr/bin/env python3

import argparse
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict

import coloredlogs
import cv2
from motion_detector.mask import Mask
from motion_detector.motion_detector import MotionDetector

logger = logging.getLogger(__name__)


def parse_args() -> Dict[str, Any]:
    ap = argparse.ArgumentParser()
    ap.add_argument("video", help="Path to the video file")
    ap.add_argument("-b", "--background", help="reference background image")
    ap.add_argument(
        "-m",
        "--mask",
        action="append",
        help="Bounds of rectangle to ignore, specified as 'x1,x2,y1,y2'",
        default=[],
    )
    ap.add_argument("--history", default=30)
    ap.add_argument(
        "-s", "--show", action="store_true", default=False, help="Show the stream"
    )
    ap.add_argument("-v", "--verbose", action="count", default=0)
    return vars(ap.parse_args())


def main():
    args = parse_args()
    coloredlogs.install(
        level=30 - 10 * args["verbose"],
        fmt="%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s",
    )

    logger.info(f"Opening '{args['video']}'.")

    motion_detector = MotionDetector(
        stream=cv2.VideoCapture(args["video"]),
        history=args["history"],
        masks=[Mask(v) for v in args["mask"]],
        background=cv2.VideoCapture(args["background"]) if args["background"] else None,
        show=args["show"],
    )

    motion_times = motion_detector.detect_motion()
    logger.info("Motion Times:")
    for (t1, t2) in motion_times:
        logger.info(f"{t1} -> {t2}")

    if len(motion_times) == 0:
        exit(0)

    video_file = Path(args["video"])

    # directory = video_file.parent / video_file.stem
    # if not directory.is_dir():
    #     directory.mkdir()

    video_filter = "select='"

    for segment, (t1, t2) in enumerate(motion_times):
        video_filter += f"between(t,{t1.total_seconds()},{t2.total_seconds()})+"
    video_filter = video_filter.rstrip("+") + "', setpts=N/(25*TB)"

    subprocess.run(
        [
            "ffmpeg",
            "-hwaccel",
            "vaapi",
            "-hwaccel_output_format",
            "vaapi",
            "-hwaccel_device",
            "/dev/dri/renderD128",
            "-i",
            video_file,
            "-filter:v",
            f"{video_filter},format=nv12|vaapi,hwupload",
            "-codec:v",
            "hevc_vaapi",
            video_file.with_suffix(".mkv"),
        ]
    )


if __name__ == "__main__":
    main()
