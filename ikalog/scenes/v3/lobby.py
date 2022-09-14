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
import logging
import sys

import cv2
import numpy as np

from ikalog.scenes.stateful_scene import StatefulScene
from ikalog.utils import *

from ikalog.ml.classifier import ImageClassifier

logger = logging.getLogger()

class Spl3Lobby(StatefulScene):
    """
    Splatoon 3 Lobby stuff
    based on World Premiere
    """

    def reset(self):
        super(Spl3Lobby, self).reset()

        self._last_matching_msec = - 100 * 1000
        self._last_matched_msec = - 100 * 1000

        self._last_matching_event_msec = - 100 * 1000
        self._last_matched_event_msec = - 100 * 1000

        try:
            self._switch_state(self._state_default)
        except:
            pass # ??

    def _state_default(self, context):
        frame = context['engine']['frame']

        r_yellow = self._mask_yellow_hud.match(frame)
        r_matching = self._mask_matching.match(frame)

        r_rule_nawabari = None
        r_rule_area = None
        r_rule_yagura = None
        r_rule_hoko = None
        r_rule_asari = None

        if r_yellow:
            r_rule_nawabari = self._mask_rule_nawabari.match(frame)
            r_rule_area = self._mask_rule_area.match(frame)
            r_rule_yagura = self._mask_rule_yagura.match(frame)
            r_rule_hoko = self._mask_rule_hoko.match(frame)
            r_rule_asari = self._mask_rule_asari.match(frame)

        r_rule_any = r_rule_nawabari or r_rule_area or r_rule_yagura \
                or r_rule_hoko or r_rule_asari

        if r_yellow and r_rule_any and r_matching:
            self._call_plugins('on_lobby_matching', {})
            self._switch_state(self._state_matching)

        elif r_yellow and r_rule_any:
            self._call_plugins('on_lobby_left_queue', {})
            self._switch_state(self._state_left_queue)

    def _state_left_queue(self, context):
        frame = context['engine']['frame']
        r_yellow = self._mask_yellow_hud.match(frame)

        if (r_yellow):
            self._last_matching_msec = context['engine']['msec']
            return True

        elif not self.matched_in(context, 3000, attr='_last_matching_msec'):
            self.reset()

        return False


    def _state_matching(self, context):
        frame = context['engine']['frame']

        r_matching = self._mask_matching.match(frame)

        if (r_matching):
            self._last_matching_msec = context['engine']['msec']
            return True

        elif not self.matched_in(context, 10000, attr='_last_matching_msec'):
            # state timeout
            self._call_plugins('on_lobby_matching_canceled', {})
            logger.info("lost in matchmaking. reset")
            self.reset()
            return False

        # r_matching == False

        r_matched = self._mask_matched.match(frame)
        if r_matched:
            self._call_plugins('on_lobby_matched', {})
            self._switch_state(self._state_matched)

    def _state_matched(self, context):
        frame = context['engine']['frame']

        r_matched = self._mask_matched.match(frame)
        if r_matched:
            self._last_matched_msec = context['engine']['msec']
            return True

        elif not self.matched_in(context, 10000, attr='_last_matched_msec'):
            logger.info("timeout after matched. reset")
            self.reset()
            return False


    def _analyze(self, context):
        pass

    def dump(self, context):
        lobby = context['lobby']
        print('%s: matched %s type %s spectator %s state %s team_members %s' % (
            self,
            self._matched,
            lobby.get('type', None),
            lobby.get('spectator', None),
            lobby.get('state', None),
            lobby.get('team_members', None),
        ))

    def _init_scene(self, debug=False):
        # TODO: move to scoreboard detection
        self._mask_yellow_hud = IkaMatcher(
            1174, 660, 83, 40,
            img_file='v3_scorebaord_yellow.png',
            threshold=0.90,
            orig_threshold=0.60,
            bg_method=matcher.MM_COLOR_BY_HUE(hue=(30, 35), visibility=(230, 255)),
            fg_method=matcher.MM_COLOR_BY_HUE(hue=(30, 35), visibility=(230, 255)),
            label="yellow_button",
            call_plugins=self._call_plugins,
            debug=debug,
        )

        self._mask_matching = IkaMatcher(
            41, 35, 127, 25,
            img_file='v3_lobby_matchmaking.png',
            threshold=0.95,
            orig_threshold=0.3,
            bg_method=matcher.MM_DARK(),
            fg_method=matcher.MM_WHITE(),
            label="lobby_matchmaking",
            call_plugins=self._call_plugins,
            debug=debug,
        )

        self._mask_matched = IkaMatcher(
            539, 368, 200, 36,
            img_file='v3_lobby_matched.png',
            threshold=0.95,
            orig_threshold=0.3,
            bg_method=matcher.MM_DARK(),
            fg_method=matcher.MM_WHITE(),
            label="lobby_matched",
            call_plugins=self._call_plugins,
            debug=debug,
        )

        self._mask_rule_nawabari = IkaMatcher(
            553, 59, 134, 25,
            img_file='v3_lobby_nawabari.png',
            threshold=0.93,
            orig_threshold=0.3,
            bg_method=matcher.MM_BLACK(),
            fg_method=matcher.MM_WHITE(),
            label="lobby_nawabari",
            call_plugins=self._call_plugins,
            debug=True,
        )

        self._mask_rule_area = IkaMatcher(
            553, 59, 134, 25,
            img_file='v3_lobby_area.png',
            threshold=0.93,
            orig_threshold=0.3,
            bg_method=matcher.MM_BLACK(),
            fg_method=matcher.MM_WHITE(),
            label="lobby_area",
            call_plugins=self._call_plugins,
            debug=True,
        )

        self._mask_rule_yagura = IkaMatcher(
            553, 59, 134, 25,
            img_file='v3_lobby_yagura.png',
            threshold=0.93,
            orig_threshold=0.3,
            bg_method=matcher.MM_BLACK(),
            fg_method=matcher.MM_WHITE(),
            label="lobby_yagura",
            call_plugins=self._call_plugins,
            debug=True,
        )

        self._mask_rule_hoko = IkaMatcher(
            553, 59, 134, 25,
            img_file='v3_lobby_hoko.png',
            threshold=0.93,
            orig_threshold=0.3,
            bg_method=matcher.MM_BLACK(),
            fg_method=matcher.MM_WHITE(),
            label="lobby_hoko",
            call_plugins=self._call_plugins,
            debug=True,
        )

        self._mask_rule_asari = IkaMatcher(
            553, 59, 134, 25,
            img_file='v3_lobby_asari.png',
            threshold=0.93,
            orig_threshold=0.3,
            bg_method=matcher.MM_BLACK(),
            fg_method=matcher.MM_WHITE(),
            label="lobby_asari",
            call_plugins=self._call_plugins,
            debug=True,
        )


if __name__ == "__main__":
    Spl3Lobby.main_func()
