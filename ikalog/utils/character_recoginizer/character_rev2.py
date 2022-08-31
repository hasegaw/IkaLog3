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

import cv2
import logging
import numpy as np
import pickle


#from ikalog.utils.character_recoginizer import *
logger = logging.getLogger()

# vertical_trim_policy
PER_CHARACTER = 1
PER_LINE = 2


class PerCharacter(object):

    def cut(self, img, img_hist_x):
        chars = []
        in_char = False
        x_start = None
        last_x = None

        if self.debug:
            print(img_hist_x)

        for x in range(len(img_hist_x)):
            if in_char:
                if img_hist_x[x] > self.threshold:
                    continue
                else:
                    char = (x_start, x)
                    if char[1] - char[0] > 2:
                        chars.append((x_start, x))
                    in_char = False
            else:
                if img_hist_x[x] > self.threshold:
                    x_start = x
                    in_char = True
                else:
                    continue
        return chars

    def __init__(self, threshold=0):
        self.threshold = threshold
        self.debug = False
        pass


class FixedWidth(object):

    def cut(self, img, img_hist_x):
        w = len(img_hist_x)

        if self.from_left:
            x1 = 0
            x2 = self.sample_width
        else:
            x2 = len(img_hist_x)
            x1 = x2 - self.sample_width

        chars = []

        if (x2 - x1) > 2:
            char_tuple = [x1, x2]
            chars.append(char_tuple)

        return chars

    def __init__(self, sample_width, from_left=None, from_right=None):
        if from_right:
            self.from_left = False
        else:
            self.from_left = True

        self.sample_width = sample_width
        pass


array0to1280 = np.array(range(1280), dtype=np.int32)


class CharacterRecoginizer_rev2(object):

    def WHITE_STRING(self, img_hsv):
        white_mask_s = cv2.inRange(img_hsv[:, :, 1], 0, 48)
        white_mask_v = cv2.inRange(img_hsv[:, :, 2], 224, 256)
        white_mask = white_mask_s & white_mask_v
        return white_mask

    def save_model_to_file(self, file):
        f = open(file, 'wb')
        pickle.dump([self.samples, self.responses], f)
        f.close()

    def load_model_from_file(self, file):
        f = open(file, 'rb')
        l = pickle.load(f)
        f.close()
        self.samples = l[0]
        self.responses = l[1]

    def add_sample(self, response, img):
        img = cv2.resize(
            img, (self.sample_width, self.sample_height), interpolation=cv2.INTER_NEAREST)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        sample = img.reshape((1, img.shape[0] * img.shape[1]))

        if self.samples is None:
            self.samples = np.empty((0, img.shape[0] * img.shape[1]))
            self.responses = []

        self.samples = np.append(self.samples, sample, 0)

        try:
            response = ord('0') + int(response)
        except:
            response = ord(response)
            pass

        self.responses.append(response)

    def train(self):
        samples = np.array(self.samples, np.float32)
        responses = np.array(self.responses, np.float32)
        responses = responses.reshape((responses.size, 1))
        responses = np.array(self.responses, np.float32)
        self.model.train(samples, cv2.ml.ROW_SAMPLE, responses)
        self.trained = True

    def extract_characters(self, img):
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        img_chars = self.WHITE_STRING(img_hsv)

        # 生成されたデータが文字色が255, それ以外が 0 なので
        # 平均 16 をきっているようなら 1/16 以下ということに
        # isString = np.sum(img_fes_title_mask) > img_fes_title_mask.shape[
        #    0] * img_fes_title_mask.shape[1] * 16

        # 文字と判断したところを 1 にして縦に足し算
        img_chars1 = np.sum(img_chars / 255, axis=0)  # 列毎の検出dot数

        array0to1280 = np.array(range(1280), dtype=np.int32)
        #img_chars1_hist_x = np.extract(img_chars1 > 0, array0to1280[0:len(img_chars1) -1])

        # FixMe: 255 px まで
        img_chars1_hist_x = np.minimum(
            img_chars1, array0to1280[0:len(img_chars1)])

        char_tuples = self.x_cutter.cut(img_chars, img_chars1_hist_x)

        characters = []
        if self.vertical_trim_policy == PER_LINE:
            img_chars_hist = np.sum(img_chars[:, :], axis=1)  # 行毎の検出dot数
            img_char_extract_y = np.extract(
                img_chars_hist > 0, array0to1280[0:len(img_chars_hist)])

        for t in char_tuples:
            if self.vertical_trim_policy == PER_CHARACTER:
                img_char = img_chars[:, t[0]: t[1]]
                img_char_hist = np.sum(
                    img_char[:, :], axis=1)  # 文字単位で行毎の検出dot数
                img_char_extract_y = np.extract(
                    img_char_hist > 0, array0to1280[0:len(img_char_hist)])

            y1 = y2 = 0
            if len(img_char_extract_y) > 1:
                y1 = np.amin(img_char_extract_y)
                y2 = np.amax(img_char_extract_y) + 1

            if (y2 - y1) > 2:  # 最低高さ4ドットなければサンプルとして認識しない
                img_char_final = img[y1:y2, t[0]: t[1]]
                characters.append(img_char_final)

        return characters

    def resize_sample(self, img_sample):
        """
        Scale the character to match with trained dataset.
        """
        shape = img_sample.shape
        # FIXME: get ndarray as dest buffer for performance reasons

        (in_h, in_w) = img_sample.shape[0:2]
        (out_h, out_w) = self.sample_height, self.sample_width

        # if not self.retain_aspect_ratio:
        #    return cv2.resize(img, (out_w, out_h), interpolation=cv2.INTER_NEAREST)

        scale_w = out_w / in_w
        scale_h = out_h / in_h

        scale = min(scale_w, scale_h)
        scaled_w = int(in_w * scale)
        scaled_h = int(in_h * scale)
        img_sample_resized = cv2.resize(
            img_sample, (scaled_w, scaled_h),
            interpolation=cv2.INTER_NEAREST)

        out_mat_shape = list(img_sample.shape)
        out_mat_shape[0] = out_h
        out_mat_shape[1] = out_w

        img_sample_resized_padded = np.zeros(out_mat_shape, dtype=np.uint8)
        img_sample_resized_padded[0: scaled_h,
                                  0: scaled_w] = img_sample_resized

        if 0:
            import time
            timestr = time.time()
            cv2.imwrite(f"resize_test_{timestr}.png",
                        img_sample_resized_padded)
        return img_sample_resized_padded

    def find_samples(self, img, num_digits=None, char_width=None, char_height=None):
        characters = self.extract_characters(img)
        samples = []
        for img in characters:
            # Validate character geometry
            if char_height is not None:
                if (img.shape[0] < char_height[0]) or (char_height[1] < img.shape[0]):
                    continue

            if char_width is not None:
                if (img.shape[1] < char_width[0]) or (char_width[1] < img.shape[1]):
                    continue

            # Scale the character to match with KNN trained dataset.
            # FIXME:
            try:
                img_scaled = self.resize_sample(img)
            except:
                return []

            samples.append(img_scaled)

        if num_digits is not None:
            if (len(samples) < num_digits[0]) or (num_digits[1] < len(samples)):
                return []

        return samples

    def match1(self, img):
        if (img.shape[0] != self.sample_width) or (img.shape[1] != self.sample_height):
            img = cv2.resize(
                img, (self.sample_width, self.sample_height), interpolation=cv2.INTER_NEAREST)

        if (len(img.shape) > 2):
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        ret, img = cv2.threshold(img, 200, 255, cv2.THRESH_BINARY)

        raito = np.sum(
            img) / (img.shape[0] * img.shape[1]) if np.sum(img) != 0 else 0.0

        if raito < 0.1:
            # ほぼ真っ黒
            return 0

        sample = img.reshape((1, img.shape[0] * img.shape[1]))
        sample = np.array(sample, np.float32)

        k = 3

        retval, results, neigh_resp, dists = self.model.findNearest(sample, k)

        # 学習データを集めたいときなど
        if self.training_mode:
            import time
            cv2.imwrite('training/numbers/%s.%s.png' %
                        (retval, time.time()), img)

        d = int(results.ravel())
        return d

    def match(self, img, num_digits=None, char_width=None, char_height=None):
        if not self.trained:
            return None

        samples = self.find_samples(
            img,
            num_digits=num_digits,
            char_width=char_width,
            char_height=char_height,
        )

        s = ''
        for sample in samples:
            c = chr(self.match1(sample))
            s = s + c

        return s

    def match_digits(self, img, num_digits=None, char_width=None, char_height=None):
        try:
            return int(self.match(img, num_digits=num_digits,
                                  char_width=char_width, char_height=char_height))
        except ValueError:
            return None

    def match_float(self, img, num_digits=None, char_width=None, char_height=None):
        try:
            return float(self.match(img, num_digits=num_digits,
                                    char_width=char_width, char_height=char_height))
        except ValueError:
            return None

    def __init__(self):
        self.trained = False
        self.training_mode = False
        self.vertical_trim_policy = PER_LINE

        # ToDo: フェスタイトルのように長さが決まっている場合は固定長で切り出す
        # 一文字単位で認識する場合はヒストグラムから文字の位置リストを作る
        self.x_cutter = PerCharacter()

        self.sample_width = 10
        self.sample_height = 17

        self.samples = None  # np.empty((0, 21 * 14))
        self.responses = []
        self.model = cv2.ml.KNearest_create()
