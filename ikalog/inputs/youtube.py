#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  IkaLog
#  ======
#  Copyright (C) 2015-2022 Takeshi HASEGAWA
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
import os
import time
import threading

import cv2
from pytube import YouTube
import subprocess
import numpy as np

from ikalog.utils import *
from ikalog.inputs import VideoInput


class YouTubeInput(VideoInput):

    def __init__(self, url):
        super(YouTubeInput, self).__init__()
        print("%s: opening YouTube Video %s", self, url)
        yt = YouTube(url)
        streams = yt.streams.filter(res="1080p", video_codec="vp9")
        if len(streams):
            W, H = 1920, 1080

        if len(streams) == 0:
            streams = yt.streams.filter(res="720p", video_codec="vp9")
            if len(streams):
                W, H = 1280, 720

        if len(streams) == 0:
            streams = yt.streams.filter(res="1080p")
            if len(streams):
                W, H = 1920, 1080

        if len(streams) == 0:
            streams = yt.streams.filter(res="720p")
            if len(streams):
                W, H = 1280, 720

        if len(streams) == 0:
            raise Exception("no applicable stream available")

        self.output_geometry = (H, W)
        self.out_width = W
        self.out_height = H
        self.effective_lines = H

        self.launch_ffmpeg()
        t = threading.Thread(target=self.download_thread)

        self.yt_stream = streams[0]
        self.yt_stream.on_progress = self.on_progress_func
        self.yt_stream.on_complete = self.on_complete_func
        t.start()

    def download_thread(self):
        print("Download thread started")
        self.yt_stream.stream_to_buffer(self.ffmpeg.stdin)
        print("Download thread finished")

    def on_progress_func(self, chunk: bytes, handler, bytes_remaining: int):
        #print("on_progress_func", "chunk", len(chunk), "handler", handler, "bytes_remaining => ", bytes_remaining)
        handler.write(chunk)

    def on_complete_func(self, x):
        print("on_complete_func")
        self.ffmpeg.stdin.flush()
        self.ffmpeg.stdin.close()

    def launch_ffmpeg(self):
        command= [ "ffmpeg", '-loglevel', 'error', '-i', 'pipe:', '-pix_fmt', 'bgr24', '-f', 'rawvideo', '-r', '10', 'pipe:1' ]
        self.ffmpeg = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=10**8)

    # override
    def _enumerate_sources_func(self):
        return ['Device Enumeration not supported']

    # override
    def _initialize_driver_func(self):
        self._cleanup_driver_func()
        self._current_timestamp = 0.0

    # override
    def _cleanup_driver_func(self):
        pass

    # override
    def _is_active_func(self):
        if not self.ffmpeg:
            return False
        return True

        raise Exception()
        return \
            hasattr(self, 'video_capture') and \
            (self.video_capture is not None)

    # override
    def _select_device_by_index_func(self, source):
        raise Exception()


    # override
    def _select_device_by_name_func(self, source):
        raise Exception()


    # override
    def _get_current_timestamp_func(self):
        return self._current_timestamp

    # override
    def _read_frame_func(self):
        num_frame_bytes = self.out_width*self.out_height*3
        frame_bytes = self.ffmpeg.stdout.read(num_frame_bytes)
        if len(frame_bytes) != num_frame_bytes:
            raise EOFError()

        frame = np.frombuffer(frame_bytes, np.uint8).reshape(self.out_height, self.out_width, 3)
        self._current_timestamp += 100 # ms
        return frame

if __name__ == "__main__":
    obj = YouTubeInput("https://www.youtube.com/watch?v=lWKDkGmRhR0")

    k = 0
    while k != 27:
        frame = obj.read_frame()
        if frame is not None:
            cv2.imshow(obj.__class__.__name__, frame)
        cv2.waitKey(1)
