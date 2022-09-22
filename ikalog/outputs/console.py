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

from datetime import datetime
import time

from ikalog.utils import *


# IkaLog Output Plugin: Show message on Console
#

_ = Localization.gettext_translation('console', fallback=True).gettext


class Console(object):

    ##
    # on_game_start Hook
    # @param self      The Object Pointer
    # @param context   IkaLog context
    #
    def on_game_start(self, context, params={}):
        stage = IkaUtils.map2text(context['game']['map'])
        rule = IkaUtils.rule2text(context['game']['rule'])
        print(_('Game Start. Stage: %(stage)s, Mode: %(rule)s') %
              {'rule': rule, 'stage': stage})
        power = context['game'].get('gachi_power')
        if power:
            print(_('Power estimated: %d') % power)


    def on_game_killed(self, context, params={}):
        print(_('Splatted an enemy! (%(streak)d streak)') %
              {'streak': context['game'].get('kill_streak', 1)})

    def on_game_chained_kill_combo(self, context, params={}):
        print(_('You chained %(combo)d kill combo(s)!') %
              {'combo': context['game'].get('kill_combo', 1)})

    def on_game_dead(self, context, params={}):
        print(_('You were splatted!'))

    def on_game_special_weapon(self, context, params={}):
        s = '%s, mine == %s' % (
            params['special_weapon'], params['me'])
        print(_('Special Weapon Activation: %s' % s))

    def on_game_death_reason_identified(self, context, params={}):
        s = _('Cause of death: %(cause_of_death)s') % \
            {'cause_of_death': context['game']['last_death_reason']}
        print(s)

    def on_game_go_sign(self, context, params={}):  # "Go!"
        print(_('Go!'))

    def on_game_finish(self, context, params={}):  # Finish tape
        print(_('Game End.'))

    # Ranked battle common events

    def on_game_ranked_we_lead(self, context, params={}):
        print(_('We\'ve taken the lead!'))

    def on_game_ranked_they_lead(self, context, params={}):
        print(_('We lost the lead!'))

    # Ranked, Splat Zone battles

    def on_game_splatzone_we_got(self, context, params={}):
        print(_('We\'re in control!'))

    def on_game_splatzone_we_lost(self, context, params={}):
        print(_('We lost control!'))

    def on_game_splatzone_they_got(self, context, params={}):
        print(_('They\'re in control!'))

    def on_game_splatzone_they_lost(self, context, params={}):
        print(_('They lost control!'))

    # Ranked, Rainmaker battles

    def on_game_rainmaker_we_got(self, context, params={}):
        print(_('We have the Rainmaker!'))

    def on_game_rainmaker_we_lost(self, context, params={}):
        print(_('We lost the Rainmaker!'))

    def on_game_rainmaker_they_got(self, context, params={}):
        print(_('They have the Rainmaker!'))

    def on_game_rainmaker_they_lost(self, context, params={}):
        print(_('They lost the Rainmaker!'))

    # Ranked, Tower Control battles

    def on_game_towercontrol_we_got(self, context, params={}):
        print(_('We took the tower!'))

    def on_game_towercontrol_we_lost(self, context, params={}):
        print(_('We lost the tower!'))

    def on_game_towercontrol_they_got(self, context, params={}):
        print(_('They took the tower!'))

    def on_game_towercontrol_they_lost(self, context, params={}):
        print(_('They lost the tower!'))

    # Ranked, Cram Blitz battles

    def on_game_cramblitz_we_broke(self, context, params={}):
        print(_('We broke the barrier!'))

    def on_game_cramblitz_we_back(self, context, params={}):
        print(_('We back the barrier!'))

    def on_game_cramblitz_they_broke(self, context, params={}):
        print(_('They broke the barrier!'))

    def on_game_cramblitz_they_back(self, context, params={}):
        print(_('They back the barrier!'))

    def on_game_session_end(self, context, params={}):
        print(_('Game Session end.'))
