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

from .game.beginning import Spl3GameBeginning
from .game.finish import Spl3GameFinish
from .game.paint_tracker import Spl3PaintTracker
from .game.kill import Spl3GameKill
from .game.kill_combo import Spl3GameKillCombo
from .game.dead import Spl3GameDead
from .game.timer import Spl3GameTimer
from .game.team_colors import Spl3GameTeamColors
from .game.weapons import Spl3GameWeapons

from .lobby import Spl3Lobby

from ikalog.scenes.blank import Blank


def initialize_scenes(engine):
    s = [
        Spl3PaintTracker(engine),
        Spl3Lobby(engine),
        Spl3GameBeginning(engine),
        Spl3GameFinish(engine),
        Spl3GameKill(engine),
#        Spl3GameDead(engine),
        Spl3GameKillCombo(engine),
        Spl3GameTeamColors(engine),
        Spl3GameTimer(engine),
        Spl3GameWeapons(engine),

        Blank(engine),
    ]
    return s
