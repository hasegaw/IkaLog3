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

import time
import os
import traceback
import threading
import logging

from ikalog.utils import *
from obswebsocket import obsws, requests


_ = Localization.gettext_translation('video_recorder', fallback=True).gettext
logger = logging.getLogger()


class OBS(object):

    def on_config_reset(self, context=None):
        self.config_reset()
        self.refresh_ui()

    def config_reset(self):
        self.enabled = False
        self.auto_rename_enabled = False
        self.dir = ''

    def on_config_load_from_context(self, context):
        self.config_reset()
        try:
            conf = context['config']['obs']
        except:
            conf = {}

        if 'Enable' in conf:
            self.enabled = conf['Enable']

        if 'AutoRenameEnable' in conf:
            self.auto_rename_enabled = conf['AutoRenameEnable']

        if 'Dir' in conf:
            self.dir = conf['Dir']

        self.refresh_ui()
        return True

    def on_config_save_to_context(self, context):
        context['config']['obs'] = {
            'Enable': self.enabled,
            'AutoRenameEnable': self.auto_rename_enabled,
            'Dir': self.dir,
        }

    def start_recording(self):
        logger.debug("start recording")

        # FIXME: handle password securely
        ws = obsws('localhost', 4444, 'password')
        ws.connect()
        ws.call(requests.StartRecording())
        ws.disconnect()

    def stop_recording(self):
        logger.debug("stop recording")

        # FIXME: handle password securely
        ws = obsws('localhost', 4444, 'password')
        ws.connect()
        ws.call(requests.StopRecording())
        ws.disconnect()

    def on_lobby_matched(self, context, params={}):
        if not self.enabled:
            return
        self.start_recording()

    def on_lobby_matching(self, context, params={}):
        if not self.enabled:
            return
        self.stop_recording()

    def on_lobby_left_queue(self, context, params={}):
        if not self.enabled:
            return
        self.stop_recording()

    def __init__(self, dir=None):
        self.enabled = (not dir is None)
        self.auto_rename_enabled = (not dir is None)
        self.dir = dir


if __name__ == "__main__":
    from datetime import datetime
    import time

    context = {
        'game': {
            'map': {'name': 'mapname'},
            'rule': {'name': 'rulename'},
            'won': True,
            'timestamp': datetime.now(),
        }
    }

    obs = OBS(dir=os.getcwd())

    obs.on_lobby_matched(context, params={})
    time.sleep(5)
    obs.on_lobby_matching(context, params={})
    time.sleep(5)
    obs.on_lobby_matched(context, params={} )
    time.sleep(5)
    obs.on_lobby_left_queue(context, params={})
    time.sleep(5)
