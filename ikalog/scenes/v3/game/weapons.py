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

import cv2
import logging
import time

from ikalog.scenes.stateful_scene import StatefulScene
from ikalog.utils import *


logger = logging.getLogger()


class Spl3GameWeapons(StatefulScene):
    """
    Detect weapon types
    """

    def reset(self):
        super(Spl3GameWeapons, self).reset()

    # event handlers
    def on_game_beginning(self, context, params):
        if self._state != self._state_default:
            return

        self.detect_weapons(context)
        self._switch_state(self._state_wait_for_timeout)

    def on_game_timer_reset(self, context, params):
        self.reset()
        self._switch_state(self._state_default)

    # states

    def _state_default(self, context):
        """
        State: Waiting for a match to detect.
        """
        return False

    def _state_wait_for_timeout(self, context):
        """
        Match on-going. Stay in this state until a match ends.
        """
        return False

    def detect_weapons(self, context):
        filename = 'screenshots/weapon_detect.%s.png' % time.time()

        cv2.imwrite(filename, context['engine']['frame'])
        logger.info("Weapon detection performed")

    def dump(self, context):
        pass

    def _analyze(self, context):
        pass

    def _init_scene(self, debug=False):
        pass


if __name__ == "__main__":
    Spl3GameWeapons.main_func()
