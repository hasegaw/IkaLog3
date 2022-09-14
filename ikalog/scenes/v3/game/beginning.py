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

import cv2
import logging
import time

from ikalog.scenes.stateful_scene import StatefulScene
from ikalog.utils import *


logger = logging.getLogger()


class Spl3GameBeginning(StatefulScene):
    """
    Detect Beginning of the match.
    """

    def reset(self):
        super(Spl3GameBeginning, self).reset()

    # event handlers
    def on_game_timer_detected(self, context, params):
        self._switch_state(self._state_waiting)

    def on_game_timer_update(self, context, params):
        if self._state != self._state_waiting:
            return
        print("UPDATE", params)
        cond_timer_value = params['time_remaining'] in ('3:00', '5:00')

        if (cond_timer_value):
            self._call_plugins('on_game_beginning', params)
            self._switch_state(self._state_wait_for_timeout)
            return

        else:
            self._switch_state(self._state_wait_for_timeout)
            return

    def on_game_timer_reset(self, context, params):
        self.reset()
        self._switch_state(self._state_default)

    # states

    def _state_default(self, context):
        """
        State: Waiting for a match to detect.
        """
        return False

    def _state_waiting(self, context):
        """
        Timer Detected, waiting for next timer update
        """
        return False

    def _state_wait_for_timeout(self, context):
        """
        Match on-going. Stay in this state until a match ends.
        """
        return False

    def dump(self, context):
        pass

    def _analyze(self, context):
        pass

    def _init_scene(self, debug=False):
        pass


if __name__ == "__main__":
    Spl3GameBeginning.main_func()
