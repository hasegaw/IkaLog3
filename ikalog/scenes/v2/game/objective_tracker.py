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
import numpy as np

from ikalog.scenes.scene import Scene
from ikalog.utils import *

# Tracker the control tower (or rainmaker)


class ObjectiveTracker(Scene):
    # 720p サイズでの値
    tower_width = 610
    tower_left = int(1280 / 2 - tower_width / 2)
    tower_top = 92
    tower_height = 115

    tower_line_top = 100
    tower_line_height = 5

    # Called per Engine's reset.
    def reset(self):
        super(ObjectiveTracker, self).reset()
        self._last_update_msec = -100 * 1000

    def tower_pos(self, context):
        img = context['engine']['frame'][self.tower_line_top:self.tower_line_top +
                                         self.tower_line_height, self.tower_left:self.tower_left + self.tower_width]
        img2 = cv2.resize(img, (self.tower_width, 100))
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        for i in range(2):
            img2[20:40, :, i] = cv2.resize(
                img_hsv[:, :, 0], (self.tower_width, 20))
            img2[40:60, :, i] = cv2.resize(
                img_hsv[:, :, 1], (self.tower_width, 20))
            img2[60:80, :, i] = cv2.resize(
                img_hsv[:, :, 2], (self.tower_width, 20))

        # ゲージのうち信頼できる部分だけでマスクする
        img3 = img & self.ui_tower_mask
        # cv2.imwrite('img3.png', img3)

        # 白い部分にいまヤグラ/ホコがある
        img3_hsv = cv2.cvtColor(img3, cv2.COLOR_BGR2HSV)

        mask_tower_neutral = cv2.inRange(img3_hsv, (20, 0, 200), (35, 100, 255))
        cv2.imwrite('neutral.png', mask_tower_neutral)
        # replace the neutral tower colour with white
        img3_hsv[mask_tower_neutral > 0] = (0, 0, 255)

        # TODO: if too much of the mask is white, return early


        white_mask_v = cv2.inRange(img3_hsv, (0, 0, 230), (256, 20, 256))

        img4 = cv2.cvtColor(white_mask_v, cv2.COLOR_BGR2RGB)
        cv2.imwrite('img4.png', img4)

        x_list = np.arange(self.tower_width)
        tower_x = np.extract(white_mask_v[3, :] > 128, x_list)

        if tower_x.shape[0] == 0:
            return None

        tower_xPos = np.average(tower_x)

        # FixMe: マスクした関係が位置がずれている可能性があるので、適宜補正すべき

        xPos_pct = (tower_xPos - self.tower_width / 2) / \
            (self.tower_width * .97 / 2) * 100

        # あきらかにおかしい値が出たらとりあえず排除
        if xPos_pct < -120 or 120 < xPos_pct:
            xPos_pct = None

        return xPos_pct

    def match_no_cache(self, context):
        if self.is_another_scene_matched(context, 'GameTimerIcon') == False:
            pass
            # return False

        if self.is_another_scene_matched(context, 'Spl2GameMap') == True:
            return False

        # context['game']['rule'] = 'hoko'

        if context['game']['rule'] is None:
            return False

        rule_id = context['game']['rule']
        applicable_modes = ['yagura', 'hoko']
        if not (rule_id in applicable_modes):
            return False

        xPos_pct = self.tower_pos(context)
        if not 'tower' in context['game']:
            context['game']['tower'] = {
                'pos': 0,
                'max': 0,
                'min': 0,
            }

        if xPos_pct is None:
            # 値がとれていない
            xPos_pct = context['game']['tower']['pos']

        new_pos = int(xPos_pct)
        # 現在位置から飛びすぎている場合、1秒間は無視する
        if abs(new_pos - context['game']['tower']['pos']) > 30:
            if self.matched_in(context, 1000, attr='_last_update_msec'):
                return False

        new_min = min(new_pos, context['game']['tower']['min'])
        new_max = max(new_pos, context['game']['tower']['max'])

        old_pos = context['game']['tower']['pos']
        updated = (new_pos != context['game']['tower']['pos'])

        context['game']['tower']['pos'] = new_pos
        context['game']['tower']['min'] = new_min
        context['game']['tower']['max'] = new_max
        if updated:
            self._call_plugins('on_game_objective_position_update')
            IkaUtils.add_event(context, 'objective', new_pos)

        self._last_update_msec = context['engine']['msec']
        return True

    def dump(self, context):
        print('--------')
        print('pos: ', context['game']['tower'])

    # Called only once on initialization.
    def _init_scene(self):
        self.ui_tower_mask = imread('masks/v2_ui_tower.png')
        self.ui_tower_mask = self.ui_tower_mask[
            self.tower_line_top:self.tower_line_top + self.tower_line_height, self.tower_left:self.tower_left + self.tower_width]

if __name__ == "__main__":
    # target = cv2.imread(sys.argv[1])
    ObjectiveTracker.main_func()
