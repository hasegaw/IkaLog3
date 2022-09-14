#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  IkaLog
#  ======
#  Copyright (C) 2022 Takeshi HASEGAWA
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

import logging
import time

import cv2
import numpy as np

from ikalog.scenes.stateful_scene import StatefulScene
from ikalog.utils import *


logger = logging.getLogger()



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

def detect_team_color(img_team):
    """
    img = masked image of the team
    """
    img_team_hsv = cv2.cvtColor(img_team, cv2.COLOR_BGR2HSV)

    img_team_h_1d = img_team_hsv[:, :, 0].reshape((-1))  # Hue Channel but 1D array
    # FIXME: remove low-saturation pixels (black/gray/white) to remove abesnt players
    img_team_blackmask = cv2.inRange(img_team_hsv[:, :, 2], 30, 255)
    img_team_black_1d = img_team_blackmask.reshape((-1))

    img_team_h_nonblack_1d = np.extract(img_team_blackmask, img_team_h_1d)
    hist,bins = np.histogram(img_team_h_nonblack_1d, 256, [0, 256])
    team_color_h = np.argmax(hist)

    return team_color_h


class Spl3GameTeamColors(StatefulScene):
    """
    Detect team colors
    FIXME: no tri-color battle support yet
    """

    def reset(self):
        super(Spl3GameTeamColors, self).reset()

    # event handlers
    def on_game_beginning(self, context, params):
        team_colors = self.detect_team_colors2(context)
        params = {
            'team_colors': team_colors,
        }
        self._call_plugins('on_game_team_colors_detected', params)
        self._switch_state(self._state_wait_for_timeout)


    def on_game_timer_reset(self, context, params):
        self.reset()
        self._switch_state(self._state_default)

    # states

    def _state_default(self, context):
        """
        State: Waiting for a match to detect.
        """
        self.detect_team_colors2(context)

        return False

    def _state_wait_for_timeout(self, context):
        """
        Match on-going. Stay in this state until a match ends.
        """
        self.detect_team_colors2(context)

        return False

    def detect_team_colors2(self, context):
        rois = [
            # [x, y, w, h]
            ROIRect(x=350, y=15, w=240, h=60),
            ROIRect(x=697, y=15, w=240, h=60),
        ] 

        frame = context['engine']['frame']
        img_frame_masked = frame & self._inklings2_mask
        cv2.imshow("team_colors", img_frame_masked)

        team_colors = []

        for i, roi in enumerate(rois):
            img_team = img_frame_masked[roi.y: roi.y + roi.h, roi.x: roi.x+roi.w]
            hue = detect_team_color(img_team)
            team_colors.append({'hue': hue})

            if 1:
                # tiny preview
                img = np.zeros((1, 1, 3), dtype=np.uint8)
                img[:, :, 0] = hue # Hue
                img[:, :, 1] = 128 # Saturation
                img[:, :, 2] = 255 # Visibility
                img_bgr = cv2.cvtColor(img, cv2.COLOR_HSV2BGR)
                color = img_bgr[0, 0, :]

                context['engine']['preview'][roi.y + roi.h: roi.y + roi.h + 5, roi.x: roi.x + roi.w] = color
                continue

        # ToDo: check result
        return team_colors # or None


    def dump(self, context):
        pass

    def _analyze(self, context):
        pass

    def _init_scene(self, debug=False):
        self._inklings2_mask = imread('masks/v3_game_inklings2.png')


if __name__ == "__main__":
    Spl3GameTeamColors.main_func()
