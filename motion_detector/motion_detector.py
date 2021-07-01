import logging
from datetime import timedelta
from typing import Any, List, Optional, Tuple, Union

import cv2
import numpy as np
from motion_detector.mask import Mask

logger = logging.getLogger(__name__)


class MotionDetector:
    def __init__(
        self,
        stream: cv2.VideoCapture,
        history: int = 30,
        blur: int = 64 + 1,
        masks: List[Union[np.ndarray, Mask]] = [],
        background: Optional[cv2.VideoCapture] = None,
        show=False,
    ):
        self.stream = stream
        self.shape: Tuple[int, int] = (
            int(self.stream.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            int(self.stream.get(cv2.CAP_PROP_FRAME_WIDTH)),
        )
        self.masks: List[np.ndarray] = [
            (mask.as_array(self.shape) if isinstance(mask, Mask) else mask)
            for mask in masks
        ]
        self.background_substractor: cv2.BackgroundSubtractorMOG2 = (
            cv2.createBackgroundSubtractorMOG2(history=history, detectShadows=False)
        )

        self.background = self.read_background(
            stream if background is None else background
        )
        self.weight = 1 / history
        self.blur = blur

        self.windows = dict()
        self.show = show

        # We must normalize the background here after the masks have been created
        self.background = self.normalize(self.background).astype(float)

    def read_background(self, stream: cv2.VideoCapture) -> np.ndarray:
        v: Tuple[bool, np.ndarray] = self.stream.read()
        ret, background = v
        if not ret:
            raise RuntimeError("Unabel to read first frame of stream.")
        return background

    def imshow(self, name: str, img: np.ndarray) -> Any:
        if not self.show:
            return
        if name not in self.windows:
            self.windows[name] = cv2.namedWindow(name, cv2.WINDOW_NORMAL)
        return cv2.imshow(name, img)

    def normalize(self, frame: np.ndarray) -> np.ndarray:
        for mask in self.masks:
            frame = cv2.bitwise_and(frame, frame, mask=mask)

        return cv2.GaussianBlur(
            cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY),
            (self.blur, self.blur),
            0,
        )

    def detect_motion(self):
        frame_count = 0
        has_motion = False
        start_time = None
        motion_times: List[Tuple[timedelta, timedelta]] = []

        while self.stream.isOpened():
            frame_count += 1
            if frame_count % (60 * 25) == 0:
                logger.info("Timestamp: %s", timedelta(seconds=frame_count / 25))

            if frame_count % 25 == 0:
                ret, frame = self.stream.read()
                if not ret:
                    logger.warn(
                        "Unable to read new frame at %s.",
                        timedelta(seconds=frame_count / 25),
                    )
                    break
            else:
                ret = self.stream.grab()
                if not ret:
                    logger.warn(
                        "Unable to grab new frame at %s.",
                        timedelta(seconds=frame_count / 25),
                    )
                continue

            (motion, frame) = self.process_frame(frame)
            self.imshow("Input", frame)

            if has_motion != motion:
                has_motion = motion

                if has_motion:
                    start_time = timedelta(
                        milliseconds=self.stream.get(cv2.CAP_PROP_POS_MSEC)
                    )
                    logger.info(
                        "Motion starts at %s",
                        start_time,
                    )
                else:
                    motion_times.append(
                        (
                            start_time,
                            timedelta(
                                milliseconds=self.stream.get(cv2.CAP_PROP_POS_MSEC)
                            ),
                        )
                    )
                    logger.info(
                        "Motion ends at %s",
                        motion_times[-1][1],
                    )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        return self.consolidate_motion_times(motion_times)

    def consolidate_motion_times(
        self, motion_times: List[Tuple[timedelta, timedelta]]
    ) -> List[Tuple[timedelta, timedelta]]:

        motion_times = [
            (t1 - timedelta(seconds=2.1), t2 + timedelta(seconds=2.1))
            for t1, t2 in motion_times
        ]

        if len(motion_times) <= 1:
            return motion_times

        new_times: List[Tuple[timedelta, timedelta]] = []
        start_time, end_time = motion_times[0]
        for t1, t2 in motion_times[1:]:
            # If previous segment overlaps with previous, extend the end time
            if t1 < end_time:
                end_time = t2
            # Otheriwse finish the previous segment and start a new one
            else:
                new_times.append((start_time, end_time))
                start_time = t1
                end_time = t2

        # Add the last segment if it is still ongoing
        new_times.append((start_time, motion_times[-1][1]))

        return new_times

    def process_frame(self, frame: np.ndarray) -> Tuple[bool, np.ndarray]:
        processed = self.normalize(frame)

        # fgmask = self.background_substractor.apply(processed)
        # self.imshow("Foreground Mask", fgmask)

        delta = cv2.absdiff(processed, cv2.convertScaleAbs(self.background))
        # self.imshow("Delta", delta)
        threshold = cv2.dilate(
            cv2.threshold(delta, 16, 255, cv2.THRESH_BINARY)[1], None, iterations=2
        )
        self.imshow("Threshold", threshold)
        contours, hierarchy = cv2.findContours(
            threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if self.show:
            for contour in contours:
                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(
                    frame, (x, y), (x + w, y + h), color=(255, 0, 0), thickness=2
                )

        # Update the background
        cv2.accumulateWeighted(processed, self.background, self.weight)

        return (len(contours) != 0, frame)
