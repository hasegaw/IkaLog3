from PIL import ImageFont, ImageDraw, Image
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  IkaLog
#  ======
#  Copyright (C) 2015 Takeshi HASEGAWA
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

import sys
import cv2
import time
import numpy as np

from ikalog.ml.classifier import ImageClassifier
from ikalog.utils import *
from ikalog.scenes.stateful_scene import StatefulScene


class ROIRect:
    x: int
    y: int
    w: int
    h: int

    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h


ROIs = {
    'ja': ROIRect(970, 375, 173, 65),
    # TODO: en
}


def convert_color(color, mode):
    dest = np.zeros((1, 1, 3), dtype=np.uint8)
    dest[:, :, 0] = color[0]
    dest[:, :, 1] = color[1]
    dest[:, :, 2] = color[2]
    dest_hsv = cv2.cvtColor(dest, cv2.mode)
    return dest_hsv[0,0,0], dest_hsv[0, 0, 1], dest_hsv[0, 0, 2]


class Spl3GameFinish(StatefulScene):

    def reset(self):
        super(Spl3GameFinish, self).reset()

        self._last_event_msec = - 100 * 1000


    def match1(self, frame):
        lang = None  # FIXME
        roi = ROIs.get(lang) or ROIs.get('ja')

        """
        Phase 1: Check Finish! (GAME!)
        """
        img_mask_roi = self._finish_mask[roi.y: roi.y + roi.h, roi.x: roi.x + roi.w, 0]
        img_roi = frame[roi.y: roi.y + roi.h, roi.x: roi.x + roi.w]
        img_roi_hsv = cv2.cvtColor(img_roi, cv2.COLOR_BGR2HSV)
        img_roi_v = img_roi_hsv[:, :, 2]
        img_roi_v2 = cv2.inRange(img_roi_v, 20, 70)
        img_finish_loss = abs(np.array(img_roi_v2, dtype=np.uint32) - (255 - img_mask_roi))


        hist,bins = np.histogram(img_finish_loss, 2, [0, 256])
        match_phase1 = hist[0] / np.sum(hist)   # (0.0 = no detect  ~ 1.0 = detected)

        if match_phase1 < 0.9:
            return False


        """
        Phase 2: Check the belt on black bg
        """
        img_frame_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        img_frame_hsv_masked = img_frame_hsv & self._finish_mask

        # Check the color distribution, but all of 720p pixels are too much to do that.
        # Generate a smaller image for the detection
        img_frame_hsv_masked_small = cv2.resize(img_frame_hsv_masked, (128, 72), img_frame_hsv_masked, cv2.INTER_NEAREST)
        img_frame_hsv_1d = img_frame_hsv_masked_small.reshape((-1, 3)).astype(np.float32)

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        flags = cv2.KMEANS_RANDOM_CENTERS
        compactness,labels,centers = cv2.kmeans(img_frame_hsv_1d, 2, None, criteria, 10, flags)

        if centers[0, 2] < centers[1, 2]:
            c_black = centers[0]
            c_tape = centers[1]
        else:
            c_black = centers[1]
            c_tape = centers[0]

        RANGE = 10
        tape_hue = max(0, c_tape[0] - RANGE), min(c_tape[0] + RANGE, 255)
        tape_vis = (30, 255)

        bg_method=matcher.MM_COLOR_BY_HUE(hue=tape_hue, visibility=tape_vis)
        self._mask_finish.bg_method=bg_method
        matched = self._mask_finish.match(frame)

        return matched


    def _state_default(self, context):
        frame = context['engine']['frame']

        matched = self.match1(frame)
        if 0:
            preview = context['engine']['preview']
            cv2.putText(preview, "game_finish %s" % matched, (100, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        if matched:
            self._last_event_msec = context['engine']['msec']
            self._call_plugins('on_game_finish', {})
            self._switch_state(self._state_wait_for_timeout)
            return True


    def _state_wait_for_timeout(self, context):
        # detection test only
        frame = context['engine']['frame']
        matched = self.match1(frame)
        if 0:
            preview = context['engine']['preview']
            cv2.putText(preview, "game_finish %s" % matched, (100, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        if self.matched_in(context, 60 * 10000, attr='_last_event_msec'):
            return False

        self.reset()
        return False


    def _analyze(self, context):
        pass

    def _init_scene(self, debug=False):
        self._finish_mask = imread('masks/ja/v3_game_finish.png')  # FIXME

        # fg = black, bg = tape color
        self._mask_finish = IkaMatcher(
            0, 0, 1280, 720,
            #553, 59, 134, 25,
            img_file='v3_game_finish.png',
            threshold=0.95,
            orig_threshold=0.1,
            bg_method=None,  # To be overrided
            fg_method=matcher.MM_BLACK(),
            label="finish",
            call_plugins=self._call_plugins,
            debug=False,
        )


if __name__ == "__main__":
    Spl3GameFinish.main_func()
