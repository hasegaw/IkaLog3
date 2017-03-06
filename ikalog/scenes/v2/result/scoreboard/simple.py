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

import traceback

from ikalog.scenes.stateful_scene import StatefulScene
from ikalog.inputs.filters import OffsetFilter
from ikalog.utils import *

from ikalog.scenes.v2.result.scoreboard.extract import extract_players


class ResultScoreboard(StatefulScene):

    def analyze(self, context):
        context['game']['players'] = []
        weapon_list = []

        return

    def reset(self):
        super(ResultScoreboard, self).reset()

        self._last_event_msec = - 100 * 1000
        self._match_start_msec = - 100 * 1000

        self._last_frame = None
        self._diff_pixels = []

    def _state_default(self, context):
        if self.matched_in(context, 30 * 1000):
            return False

        frame = context['engine']['frame']

        if frame is None:
            return False

        matched_r1 = self.mask_win_hook.match(frame)
        matched_r2 = self.mask_lose_hook.match(frame)

        matched = matched_r1 and matched_r2

        if matched:
            players = extract_players(frame)

            # won?
            me = list(filter(lambda x: x['myself'], players))[0]
            context['game']['won'] = (me['team'] == 0)


#        if matched:
#            self._match_start_msec = context['engine']['msec']
#            self._switch_state(self._state_tracking)
        return matched

    def dump(self, context):
        print('--------')
        print('won: ', context['game']['won'])

    def _init_scene(self, debug=True):
        self.mask_win_hook = IkaMatcher(
            920, 0, 100, 70,
            img_file='v2_result_scoreboard.png',
            threshold=0.90,
            orig_threshold=0.20,
            bg_method=matcher.MM_DARK(),
            fg_method=matcher.MM_NOT_DARK(),
            label='result_scoreboard:WIN',
            debug=debug,
        )

        self.mask_lose_hook = IkaMatcher(
            920, 340, 100, 70,
            img_file='v2_result_scoreboard.png',
            threshold=0.90,
            orig_threshold=0.20,
            bg_method=matcher.MM_DARK(),
            fg_method=matcher.MM_NOT_DARK(),
            label='result_scoreboard:LOSE',
            debug=debug,
        )

if __name__ == "__main__":
    ResultScoreboard.main_func()