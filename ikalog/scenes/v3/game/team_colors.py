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

    img_team_h_1d = img_team_hsv[:, :, 0].reshape(
        (-1))  # Hue Channel but 1D array
    # FIXME: remove low-saturation pixels (black/gray/white) to remove abesnt players
    img_team_blackmask = cv2.inRange(img_team_hsv[:, :, 2], 30, 255)
    img_team_black_1d = img_team_blackmask.reshape((-1))

    img_team_h_nonblack_1d = np.extract(img_team_blackmask, img_team_h_1d)
    hist, bins = np.histogram(img_team_h_nonblack_1d, 256, [0, 256])
    team_color_h = np.argmax(hist)

    return team_color_h


class Spl3GameTeamColors(StatefulScene):
    """
    Detect team colors
    FIXME: no tri-color battle support yet
    """

    def reset(self):
        super(Spl3GameTeamColors, self).reset()

        self.team_colors = []

    # event handlers
    def on_game_beginning(self, context, params):
        """
        Detect team colors at the beginning of game
        """
        if self._state != self._state_default:
            # Seems the event is already fired.
            return

        # 2 teams battle?
        team_colors = self.detect_team_colors2(context)
        if True:
            params = {
                'game_type': 'default',
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

        # FIXME
        # Since on_game_beginning seems not to be firing on
        # tri-color battles yet, run tri-color detection every frame.

        timer_scene = self.find_scene_object('Spl3GameTimer')

        # tri-color battle?
        team_colors = self.detect_team_colors3(context)

        if team_colors:  # tri-color match inklings detected
            # We want to check if timer is detected at top left because
            # detect_team_colors3() may cause false-positive.
            #
            # get Spl3GameTimer scene and let it detect the timer
            # from the frame. (one shot detection - don't matter its state)
            if timer_scene:
                timestr, coordinate = timer_scene.match_any_timer(context)

                # Filter the detection if Timer scene didn't detect
                # excepted timer.
                if coordinate is None:
                    return False

                if coordinate.id != 'tricolor':
                    return False

            params = {
                'game_type': 'tri-color',
                'team_colors': team_colors,
            }
            self._call_plugins('on_game_team_colors_detected', params)
            self._switch_state(self._state_wait_for_timeout)

    def _state_wait_for_timeout(self, context):
        """
        Match on-going. Stay in this state until a match ends.
        """
        self.detect_team_colors2(context)

        return False

    def detect_team_colors2(self, context):
        """
        Detect non-tri-color battles
        """
        rois = [
            # [x, y, w, h]
            ROIRect(x=350, y=15, w=240, h=60),
            ROIRect(x=697, y=15, w=240, h=60),
        ]

        frame = context['engine']['frame']
        img_frame_masked = frame & self._inklings2_mask
        # cv2.imshow("team_colors", img_frame_masked)

        team_colors = []

        for i, roi in enumerate(rois):
            img_team = img_frame_masked[roi.y: roi.y +
                                        roi.h, roi.x: roi.x+roi.w]
            hue = detect_team_color(img_team)
            team_colors.append({'hue': hue})

            if 1:
                # tiny preview
                img = np.zeros((1, 1, 3), dtype=np.uint8)
                img[:, :, 0] = hue  # Hue
                img[:, :, 1] = 128  # Saturation
                img[:, :, 2] = 255  # Visibility
                img_bgr = cv2.cvtColor(img, cv2.COLOR_HSV2BGR)
                color = img_bgr[0, 0, :]

                context['engine']['preview'][roi.y + roi.h: roi.y +
                                             roi.h + 5, roi.x: roi.x + roi.w] = color
                continue

        # ToDo: check result
        return team_colors  # or None

    def detect_team_colors3(self, context):
        """
        Detect Tri-Color Battles.
        """
        TEAM_HUE_RANGE = 5
        MAX_COLOR_LOSS_THRESHOLD = 10  # less than 3, 5, or 10
        MATCH_RATIO_THRESHOLD = 0.8  # more than 0.9, or 0.85?

        tri_color_rois = [
            # [x, y, w, h]
            ROIRect(x=350, y=15, w=120, h=60),
            ROIRect(x=524, y=15, w=234, h=60),
            ROIRect(x=810, y=15, w=120, h=60),
        ]

        def crop_image(img, roi):
            return img[roi.y: roi.y + roi.h, roi.x: roi.x+roi.w]
        # Detect team colors again each img_team roi
        team_colors = [None, None, None]  # Team Colors in Hue value.

        frame = context['engine']['frame']
        img_frame_masked = frame & self._inklings3_mask

        """
        Step 1: Check the bar at the step of inklings by Hue distribution
        """
        for i, roi in enumerate(tri_color_rois):
            img_team = crop_image(img_frame_masked, roi)
            team_colors[i] = detect_team_color(img_team)

        """
        Step 2: Check the bar at the step of inklings by Hue distribution
        """
        # max_color_loss: Max Distance of team_color on the bar and
        # team_colors[] from inklings indicator. Smaller value is better
        max_color_loss = 0

        img_bar = frame[67: 67+10, 349:349+583]
        img_bar_h = cv2.cvtColor(img_bar, cv2.COLOR_BGR2HSV)[0]
        hist, bins = np.histogram(img_bar_h, 256, [0, 256])

        # set 0 to the top 3 clusters (== squid team colors)
        for i in range(3):
            team_color = np.argmax(hist)

            # check if  the team_color value (Hue) is close to one of
            # team colors.
            team_color_loss = abs(np.array(team_colors) - team_color)
            max_color_loss = max(max_color_loss, np.min(team_color_loss))

            c1 = max(team_color - TEAM_HUE_RANGE, 0)
            c2 = min(team_color + TEAM_HUE_RANGE, 255)
            hist[c1:c2] = 0

        # Now, most of value of hist[] is masked by zeros.
        # Count the pixels not masked (0.0 best ~ 1.0 worst)
        match_ratio = 1 - np.sum(hist) / (img_bar.shape[0] * img_bar.shape[1])

        cond_max_color_loss = max_color_loss < MAX_COLOR_LOSS_THRESHOLD
        cond_match_ratio = match_ratio > MATCH_RATIO_THRESHOLD

        if cond_max_color_loss and cond_match_ratio:
            return team_colors  # 3 elements of the team hue, from left/center/right team
        return None

    def dump(self, context):
        pass

    def _analyze(self, context):
        pass

    def _init_scene(self, debug=False):
        self._inklings2_mask = imread('masks/v3_game_inklings2.png')
        self._inklings3_mask = imread('masks/v3_game_inklings3.png')


if __name__ == "__main__":
    Spl3GameTeamColors.main_func()
