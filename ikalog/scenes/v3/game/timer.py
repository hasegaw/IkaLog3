#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  IkaLog
#  ======
#  Copyright (C) 2017 Takeshi HASEGAWA
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

from dataclasses import dataclass
import logging
import re
import sys

import cv2
import numpy as np

from ikalog.scenes.stateful_scene import StatefulScene
from ikalog.ml.text_reader import TextReader
from ikalog.utils import *

from ikalog.utils.character_recoginizer.number2 import Number2Classifier

logger = logging.getLogger()
number2 = Number2Classifier()


"""
Y position

y0
    ^^^^^^^
y1
      5:00
y2
    vvvvvvv
y3
"""
y0 = 16
y1 = 16 + 22
y2 = 16 + 48
y3 = 16 + 72


@dataclass
class CustomTimeCoordinate:
    id: str
    left: int
    top: int
    width: int
    height: int

    def crop(self, frame):
        return frame[self.top: self.top + self.height, self.left: self.left + self.width]

    def left720p(self):
        return int(self.left * 1280 / 1920) if self.left != 0 else 0

    def width720p(self):
        return int(self.width * 1280 / 1920) if self.width != 0 else 0

    def top720p(self):
        return int(self.top * 720 / 1280) if self.top != 0 else 0

    def height720p(self):
        return int(self.height * 720 / 1280) if self.height != 0 else 0

    def to_720p(self):
        return CustomTimeCoordinate(
            id=self.id,
            left=self.left720p(),
            width=self.width720p(),
            top=self.top720p(),
            height=self.height720p(),
        )

    def drawRect(self, img_preview720p, color=(0, 0, 255)):
        cv2.rectangle(img_preview720p,
                      pt1=(self.left, self.top),
                      pt2=(self.left + self.width, self.top + self.height),
                      color=(0, 0, 255),
                      thickness=2,
                      lineType=cv2.LINE_4,
                      shift=0)


# Coordinates of time possible
TimeCoordinate = CustomTimeCoordinate(
    'default', 900, 48, 120, 53)          # in 1080p
TriColorTimeCoordinate = CustomTimeCoordinate(
    'tricolor', 328, 43, 120, 53)         # in 1080p - hasegaw
# TriColorTimeCoordinate = CustomTimeCoordinate('tricolor', 328, 30, 120, 53)         # in 1080p - clover's option


class TimerReader(object):
    _p_threshold = 0.7
    time_regexp = re.compile('(\d+):(\d+)')

    def _read_time(self, img):
        # if self._debug:
        cv2.imwrite('time.png', img)

        img = cv2.resize(img, (img.shape[1] * 2, img.shape[0] * 2))

        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        img_gray = img_hsv[:, :, 2]
        img_gray[img_gray < 210] = 0
        #img_gray[img_hsv[:, :, 1] > 30] = 0
        img_gray[img_gray > 0] = 255

        val_str = None
        val_str = self._number_recoginizer.read_char(img_gray)
        if self._debug:
            logger.debug('Read: %s' % val_str)

        return val_str

    def read_time(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        timestr = self._read_time(img)

        if not timestr:
            return False

        result = re.match(self.time_regexp, timestr)
        if not result:
            return False
        m = int(result.group(1))
        s = int(result.group(2))

        valid = (m <= 5) and (s <= 59)

        if valid:
            self._time_remaining = m * 60 + s

        return valid

    def match(self, img):
        img_timestr = img[y1: y2, 610:610 + 60]

        img_timer_black = matcher.MM_BLACK()(img_timestr)
        img_timer_white = matcher.MM_WHITE()(img_timestr)
        # img_timer_yellow = matcher.MM_COLOR_BY_HUE(
        #     hue=(27 - 5, 27 + 5), visibility=(100, 255))(img_timestr)

        img_test = img_timer_black | img_timer_white  # | img_timer_yellow
        orig_hist = cv2.calcHist([img_test], [0], None, [2], [0, 256])
        self._p = (orig_hist[1] / (orig_hist[0] + orig_hist[1]))

        time_valid = False
        if True or self._p > self._p_threshold:
            time_valid = self.read_time(255 - img_timer_black)

        return time_valid
        # return self.read_time(255 - img_timer_black)

    def __init__(self, debug=False):
        self._debug = debug
        self._time_remaining = 0
        self._number_recoginizer = TextReader()

    def get_time(self):
        return self._time_remaining


class Spl3GameTimer(StatefulScene):
    def reset(self):
        super(Spl3GameTimer, self).reset()

        self._coordinate = None

        self._last_event_msec = - 100 * 1000

        self._pending_timer_value = None  # timer value
        self._pending_timer_msec = None   # time the value was detected
        self._pending_timer_count = 5     # count of detection

        self._last_timer_value = None

    def _set_team_colors(self, context):
        """
        not reviewed for spl3
        """
        # FIXME: This file will only covers timer detection only.
        #      : More detections should be performed in another scene class.
        #      : ex) Spl3GameWeapons
        return

        # Set the team colors on first match
        # TODO Alecat - decide on this method vs team_color detection in start.py
        frame = context['engine']['frame']
        if 'game' in context and 'team_color_rgb' not in context['game']:
            context['game']['team_color_rgb'] = [
                (int(frame[68][565][2]), int(
                    frame[68][565][1]), int(frame[68][565][0])),
                (int(frame[68][730][2]), int(
                    frame[68][730][1]), int(frame[68][730][0])),
            ]

    def preview(self, context, s, color=(0, 255, 0)):
        coordinate = self._coordinate or TimeCoordinate

        preview = context['engine']['preview']
        cv2.putText(preview, f"t: {s}", (coordinate.left720p(), 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    def match_any_timer(self, context, preview=True):
        """
        Detect any time string on Splatoon 3 match, and returns the timestr and TimeCoordinate
        """
        img_preview720p = context['engine']['preview']

        for coordinate in (TimeCoordinate, TriColorTimeCoordinate):
            if preview:
                coordinate.to_720p().drawRect(img_preview720p)
            timestr = self.check_match(context, coordinate)
            if timestr:
                return timestr, coordinate
        return None, None

    def on_lobby_matching(self, context, params={}):
        pass  # self._switch_state(self._state_disabled)

    def on_lobby_matched(self, context, params={}):
        pass  # self._switch_state(self._state_default)

    def on_lobby_left_queue(self, context, params={}):
        pass  # self._switch_state(self._state_default)

    def _state_default(self, context):
        """
        Default State
        - No in-game timer is detected yet
        - look for both of typical battle (4v4) or tri-color (2:4:2)
        """

        timestr, coordinate = self.match_any_timer(context)
        self.preview(context, timestr)

        if timestr:
            #self._last_event_msec = context['engine']['msec']
            self._pending_timer_value = timestr
            self._pending_timer_msec = context['engine']['msec']
            self._coordinate = coordinate
            self._switch_state(self._state_pending)

        return False

    def _state_disabled(self, context):
        """
        Timer detection disabled
        """
        pass

    def _state_pending(self, context):
        """
        Pending State
        - in-game timer seems to be detected but pending
        """

        timestr = self.check_match(context, self._coordinate)
        self.preview(context, timestr, color=(0, 0, 255))

        if timestr == self._pending_timer_value:
            self._pending_timer_count -= 1
        else:
            self.reset()
            self._switch_state(self._state_default)

        cond = self._pending_timer_count <= 0
        if cond:
            params = {
                "timer_type": self._coordinate.id,
                "t": self._pending_timer_msec,
            }
            self._call_plugins("on_game_timer_detected", params)
            self._switch_state(self._state_tracking)
            self._set_team_colors(context)
            return True

        return False

    def _state_tracking(self, context):
        timestr = self.check_match(context, self._coordinate)
        self.preview(context, timestr)

        if timestr == self._last_timer_value:
            return False

        if timestr and timestr == self._pending_timer_value:
            self._pending_timer_count -= 1

        if timestr and timestr != self._pending_timer_value:
            self._pending_timer_count = 5
            self._pending_timer_msec = context['engine']['msec']
            self._pending_timer_value = timestr

        if timestr and self._pending_timer_count <= 0:
            self._last_timer_value = timestr
            # FIXME: overtime handling
            params = {
                "t": int(self._pending_timer_msec),
                "time_remaining": timestr,
            }
            self._call_plugins("on_game_timer_update", params)

        escaped = not self.matched_in(context, 10000)
        if escaped:
            self._call_plugins("on_game_timer_reset", {})
            self._switch_state(self._state_default)
            self.reset()

        return timestr

    def check_match(self, context, coordinate):
        """
        Detect and timer from a frame
        """
        # FIXME: return "overtime" if overtime is detected.
        # FIXME: detect time value in yellow, less than 1 minutes - not working now.
        #        Current classifier only works with white number

        img_timer = coordinate.crop(context['engine']['frame_hd'])
        #img_timer_gray = cv2.cvtColor(img_timer, cv2.COLOR_BGR2GRAY)
        # cv2.normalize(
        #    cv2.cvtColor(img_timer_gray, cv2.COLOR_GRAY2BGR),
        #    img_timer, 0, 255, norm_type=cv2.NORM_MINMAX)

        cv2.imshow("timer: %s" % coordinate.id, img_timer)
        s = number2.match(img_timer)

        m = re.match("^(\d).(\d{2,2})$", s)
        if m:
            minutes, seconds = int(m.group(1)), int(m.group(2))
            if (minutes > 5) or (seconds > 59):
                return None
            return "%s:%s" % (m.group(1), m.group(2))
        return None

    def _analyze(self, context):
        pass

    def dump(self, context):
        super(Spl3GameTimer, self).dump(context)
        print('--------')
        # print(self._overtime)
        # print(self._timer_reader.get_time())

    def _init_scene(self, debug=False):
        self._overtime = False

        self._mask_overtime = IkaMatcher(
            585, y1, 109, y2 - y1,
            img_file='v2_game_timer_overtime.png',
            threshold=0.95,
            orig_threshold=1.0,
            bg_method=matcher.MM_BLACK(visibility=(0, 100)),
            fg_method=matcher.MM_COLOR_BY_HUE(
                hue=(10 - 5, 10 + 5), visibility=(100, 255)),
            label='timer_overtime',
            debug=debug,
        )
        self._timer_reader = TimerReader(debug=debug)


if __name__ == "__main__":
    Spl3GameTimer.main_func()
