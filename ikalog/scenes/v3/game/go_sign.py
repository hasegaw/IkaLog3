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

from ikalog.utils import *
from ikalog.scenes.scene import Scene


class GameGoSign(Scene):

    def reset(self):
        super(GameGoSign, self).reset()

        self._last_game_start_msec = - 100 * 1000
        self._last_event_msec = - 100 * 1000

    def match_no_cache(self, context):
        if self.matched_in(context, 60 * 1000, attr='_last_event_msec'):
            return False

        # if not self.is_another_scene_matched(context, 'GameTimerIcon'):
        #     return False

        if not self.matched_in(context, 60 * 1000, attr='_last_game_start_msec'):
            return False

        frame = context['engine']['frame']

        if not self.mask_go_sign.match(frame):
            return False

        context['game']['start_time'] = IkaUtils.getTime(context)
        context['game']['start_offset_msec'] = context['engine']['msec']
        print("SETTING OFFSET MSEC", context['game']['start_time'], context['engine'].get('msec'), context['game']['start_offset_msec'])

        self._call_plugins('on_game_go_sign', {})
        self._last_event_msec = context['engine']['msec']
        self._last_game_start_msec = -100 * 1000
        return True


    def _analyze(self, context):
        pass

    def on_game_start(self, context):
        self._last_game_start_msec = context['engine']['msec']

    def _init_scene(self, debug=False):
        self.mask_go_sign = IkaMatcher(
            384, 130, 478, 207,
            img_file='v2_game_go_sign.png',
            threshold=0.95,
            orig_threshold=0.05 ,
            label='GO!',
            bg_method=matcher.MM_NOT_WHITE(),
            fg_method=matcher.MM_WHITE(),
            call_plugins=self._call_plugins,
            debug=False,
        )

if __name__ == "__main__":
    GameGoSign.main_func()
