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
from __future__ import print_function
import sys
import time
import uuid

import cv2

from ikalog.scenes.scene import Scene
from ikalog.utils import *
from ikalog.utils.character_recoginizer.number2 import Number2Classifier
from ikalog.utils.image_filters import MM_WHITE

number2 = Number2Classifier()


class Spl3PaintTracker(Scene):
    """
    Paint Tracker for Splatoon 3
    """

    def reset(self):
        super(Spl3PaintTracker, self).reset()

    def extract_paint_score(self, context):
        """
        crop digits from input.
        """
        preview = context['engine']['preview']

        img_counter = context['engine']['frame_hd'][52: 52 + 67, 1496: 1496+167]
        img_counter_gray = MM_WHITE()(img_counter)
        img_counter_gray_bgr = cv2.cvtColor(img_counter_gray, cv2.COLOR_GRAY2BGR)
        cv2.imshow("paint counter", img_counter_gray_bgr)

#        number2.training_mode =  True
        s = number2.match(img_counter_gray_bgr, num_digits=(4, 5), char_height=(50, 60))
#        print(f"paint score {s}")

        if s:
            cv2.putText(preview, "%s" % s, (1000, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255) , 2)

        return []


        x0 = 1022
        w = 24
        stride = 22
        img_digits = []
        for i in range(4):
            x1 = x0 + stride * i
            n = img[42: 42 + 38, x1: x1 + w]
            img_digits.append(n)
        return img_digits

    def recognize_paint_score(self, img_digits):
        """
        Read number from img_digits.
        """
        #n = np.asarray(img_digits[0], dtype=np.uint8).reshape(-1).shape[0]
        x = np.asarray(img_digits, dtype=np.float32).reshape(
            len(img_digits), -1)
        y = self.model.predictor(x).data
        labels = np.argmax(y, axis=1)

        val = 0
        for label in labels:
            if label > 9:
                return None, labels
            val = val * 10 + label

        return val, labels

    def write_training_data(self, img_digits):
        x = np.asarray(img_digits, dtype=np.float32).reshape(
            len(img_digits), -1)
        y = self.model.predictor(x).data
        labels = np.argmax(y, axis=1)
        accuracy = 0.987

        for i in range(len(labels)):
            label = labels[i]

            inf = float("inf")
            if i < 3:
                t = time.time()
                cv2.imwrite('training/numbers/%d/%0.3f_%s.png' %
                            (label, accuracy, t), img_digits[i])

            cv2.imshow(str(label), img_digits[i])
            cv2.moveWindow(str(label), 10, label * 70)

    def match_no_cache(self, context):
        #if (not self.is_another_scene_matched(context, 'Spl2GameSession')):
        #    return False
        #frame = context['engine']['frame']
        #if frame is None:
        #    return False

        img_digits = self.extract_paint_score(context)


        return
        #val, labels = self.recognize_paint_score(img_digits)

        if val is not None:
            # Set latest paint_score to the context.
            last_paint_score = context['game'].get('paint_score', 0)
            if last_paint_score < val:
                context['game']['paint_score'] = val
                self._call_plugins('on_game_paint_score_update', {})
        if 0:
            self.write_training_data(img_digits)

        return True

    def dump(self, context):
        print('paint_score %s' % context['game'].get('paint_score', None))

    def _analyze(self, context):
        pass

    def _init_scene(self, debug=False):
        pass


if __name__ == "__main__":
    Spl3PaintTracker.main_func()
