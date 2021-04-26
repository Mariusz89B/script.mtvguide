#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2020 Mariusz89B
#   Copyright (C) 2016 Andrzej Mleczko
#   Copyright (C) 2014 Krzysztof Cebulski
#   Copyright (C) 2013 Szakalit
#   Copyright (C) 2013 Tommy Winther

#   Some implementations are modified and taken from "Fullscreen TVGuide" - thank you very much primaeval!

#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.

#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with this program. If not, see https://www.gnu.org/licenses.

#   MIT License

#   Permission is hereby granted, free of charge, to any person obtaining a copy
#   of this software and associated documentation files (the "Software"), to deal
#   in the Software without restriction, including without limitation the rights
#   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#   copies of the Software, and to permit persons to whom the Software is
#   furnished to do so, subject to the following conditions:

#   The above copyright notice and this permission notice shall be included in all
#   copies or substantial portions of the Software.

#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.

from __future__ import unicode_literals

import sys

if sys.version_info[0] < 3:
    from future.utils import bytes_to_native_str as native

if sys.version_info[0] > 2:
    import configparser
else:
    import ConfigParser

import re, os, datetime, time, platform, threading, zipfile, shutil, glob
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, xbmcvfs
import source as src
from notification import Notification
from strings import *
import strings as strings2
import streaming
import playService
import requests
import json
import urllib
from vosd import VideoOSD
from recordService import RecordService
from settingsImportExport import SettingsImp
from skins import Skin
from source import Program, Channel

from contextlib import contextmanager

MODE_EPG = 'EPG'
MODE_TV = 'TV'

ACTION_LEFT = 1
ACTION_RIGHT = 2
ACTION_UP = 3
ACTION_DOWN = 4
ACTION_PAGE_UP = 5
ACTION_PAGE_DOWN = 6
ACTION_SELECT_ITEM = 7
ACTION_PARENT_DIR = 9
ACTION_PREVIOUS_MENU = 10
ACTION_SHOW_INFO = 11
ACTION_STOP = 13
ACTION_NEXT_ITEM = 14
ACTION_PREV_ITEM = 15

ACTION_MOUSE_RIGHT_CLICK = 101
ACTION_MOUSE_MIDDLE_CLICK = 102
ACTION_MOUSE_WHEEL_UP = 104
ACTION_MOUSE_WHEEL_DOWN = 105
ACTION_MOUSE_MOVE = 107

KEY_NAV_BACK = 92
KEY_CONTEXT_MENU = 117
KEY_HOME = 159
KEY_END = 160

KEY_CODEC_INFO = 0

if sys.version_info[0] > 2:
    config = configparser.RawConfigParser()
else:
    config = ConfigParser.RawConfigParser()
config.read(os.path.join(Skin.getSkinPath(), 'settings.ini'))
ini_chan = config.getint("Skin", "CHANNELS_PER_PAGE")
ini_info = config.getboolean("Skin", "USE_INFO_DIALOG")

try:
    skin_separate_category = config.getboolean("Skin", "program_category_separated")
except:
    skin_separate_category = False
try:
    skin_separate_episode = config.getboolean("Skin", "program_episode_separated")
except:
    skin_separate_episode = False
try:
    skin_separate_allowed_age_icon = config.getboolean("Skin", "program_allowed_age_icon")
except:
    skin_separate_allowed_age_icon = False
try:
    skin_separate_director = config.getboolean("Skin", "program_director_separated")
except:
    skin_separate_director = False
try:
    skin_separate_year_of_production = config.getboolean("Skin", "program_year_of_production_separated")
except:
    skin_separate_year_of_production = False
try:
    skin_separate_program_progress = config.getboolean("Skin", "program_show_progress_bar")
except:
    skin_separate_program_progress = False
try:
    skin_separate_program_progress_epg = config.getboolean("Skin", "program_show_progress_bar_epg")
except:
    skin_separate_program_progress_epg = False
try:
    skin_separate_program_actors = config.getboolean("Skin", "program_show_actors")
except:
    skin_separate_program_actors = False
try:
    skin_resolution = config.get("Skin", "resolution")
except:
    skin_resolution = '720p'
try:
    cell_height = config.get("Skin", "cell_height")
except:
    cell_height = ''
try:
    cell_width = config.get("Skin", "cell_width")
except:
    cell_width = ''
try:
    skin_font = config.get("Skin", "font")
except:
    skin_font = 'NoFont'
try:
    skin_font_colour = config.get("Skin", "font_colour")
except:
    skin_font_colour = ''
try:
    skin_font_focused_colour = config.get("Skin", "font_focused_colour")
except:
    skin_font_focused_colour = ''
try:
    skin_timebarback_colour = config.get("Skin", "timebarback_colour")
except:
    skin_timebarback_colour = ''
try:
    skin_timebar_colour = config.get("Skin", "timebar_colour")
except:
    skin_timebar_colour = ''
try:
    skin_catchup_size = config.get("Skin", "skin_catchup_size")
except:
    skin_catchup_size = 'Default'

try:
    KEY_INFO = int(ADDON.getSetting('info_key'))
except:
    KEY_INFO = 0
try:
    KEY_STOP = int(ADDON.getSetting('stop_key'))
except:
    KEY_STOP = 0
try:
    KEY_PP = int(ADDON.getSetting('pp_key'))
except:
    KEY_PP = 0
try:
    KEY_PM = int(ADDON.getSetting('pm_key'))
except:
    KEY_PM = 0
try:
    KEY_VOL_UP = int(ADDON.getSetting('volume_up_key'))
except:
    KEY_VOL_UP = -1
try:
    KEY_VOL_DOWN = int(ADDON.getSetting('volume_down_key'))
except:
    KEY_VOL_DOWN = -1
try:
    KEY_HOME2 = int(ADDON.getSetting('home_key'))
except:
    KEY_HOME2 = 0
try:
    KEY_CONTEXT = int(ADDON.getSetting('context_key'))
except:
    KEY_CONTEXT = -1
try:
    KEY_RECORD = int(ADDON.getSetting('record_key'))
except:
    KEY_RECORD = -1
try:
    KEY_LIST = int(ADDON.getSetting('list_key'))
except:
    KEY_LIST = -1
try:
    KEY_SWITCH_TO_LAST = int(ADDON.getSetting('switch_to_last_key'))
except:
    KEY_SWITCH_TO_LAST = -1

CHANNELS_PER_PAGE = ini_chan

HALF_HOUR = datetime.timedelta(minutes=30)
AUTO_OSD = 666
REFRESH_STREAMS_TIME = 14400

PREDEFINED_CATEGORIES = [strings(30325), "Group: BE", "Group: CZ", "Group: DE", "Group: DK", "Group: FR", "Group: HR",
                    "Group: IT", "Group: NO", "Group: PL", "Group: SE", "Group: SRB", "Group: UK", "Group: US", "Group: RADIO"]


def category_formatting(label):  
    label = re.sub('^0$', '1.png', label)
    label = re.sub('^1$', '2.png', label)
    label = re.sub('^2$', '3.png', label)
    label = re.sub('^3$', '4.png', label)
    label = re.sub('^4$', '5.png', label)
    label = re.sub('^5$', '6.png', label)
    label = re.sub('^6$', '7.png', label)
    label = re.sub('^7$', '8.png', label)
    label = re.sub('^8$', '9.png', label)
    return label


def background_formatting(label): 
    label = re.sub('^0$', '9.png', label)
    return label


def focus_formatting(label): 
    label = re.sub('^0$', '10.png', label)
    label = re.sub('^1$', '13.png', label)
    label = re.sub('^2$', '14.png', label)
    label = re.sub('^3$', '15.png', label)
    label = re.sub('^4$', '16.png', label)
    return label


def notifications_formatting(label):
    label = re.sub('^0$', '11.png', label)
    label = re.sub('^1$', '13.png', label)
    label = re.sub('^2$', '14.png', label)
    label = re.sub('^3$', '15.png', label)
    return label


def recordings_formatting(label):
    label = re.sub('^0$', '12.png', label)
    label = re.sub('^1$', '13.png', label)
    label = re.sub('^2$', '14.png', label)
    label = re.sub('^3$', '15.png', label)
    return label


def replace_formatting(label):
    label = re.sub(r"\s\$ADDON\[script.mtvguide.*?\]\.", '', label)
    label = re.sub(r"\$ADDON\[script.mtvguide.*?\]", '[B]N/A', label)
    return label


def timedelta_total_seconds(timedelta):
    return (
                   timedelta.microseconds + 0.0 +
                   (timedelta.seconds + timedelta.days * 24 * 3600) * 10 ** 6) // 10 ** 6


class proxydt(datetime.datetime):
    @staticmethod
    def strptime(date_string, format):
        import time
        return datetime.datetime(*(time.strptime(date_string, format)[0:6]))

datetime.proxydt = proxydt

class Point(object):
    def __init__(self):
        self.x = self.y = 0

    def __repr__(self):
        return 'Point(x={}, y={})'.format(self.x, self.y)


class EPGView(object):
    def __init__(self):
        self.top = self.left = self.right = self.bottom = self.width = self.cellHeight = 0


class ControlAndProgram(object):
    def __init__(self, control, program):
        self.control = control
        self.program = program

class Event:
    def __init__(self):
        self.handlers = set()

    def handle(self, handler):
        self.handlers.add(handler)
        return self

    def unhandle(self, handler):
        try:
            self.handlers.remove(handler)
        except:
            raise ValueError("Handler is not handling this event, so cannot unhandle it.")
        return self

    def fire(self, *args, **kargs):
        for handler in self.handlers:
            handler(*args, **kargs)

    def getHandlerCount(self):
        return len(self.handlers)

    __iadd__ = handle
    __isub__ = unhandle
    __call__ = fire
    __len__ = getHandlerCount


class epgTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = threading.Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

    def is_alive(self):
        self._timer.is_alive()


class VideoPlayerStateChange(xbmc.Player):

    def __init__(self, *args, **kwargs):
        deb("################ Starting control VideoPlayer events")
        self.playerStateChanged = Event()
        self.updatePositionTimerData = {}
        self.recordedFilesPositions = {}
        self.updatePositionTimer = None
        self.stopped = False

    def setPlaylistPositionFile(self, recordedFilesPositions):
        self.recordedFilesPlaylistPositions = recordedFilesPositions

    def stopplaying(self):
        self.updatePositionTimerData['stop'] = True
        self.Stop()

    def onStateChange(self, state):
        self.playerStateChanged(state)

    def onPlayBackError(self):
        deb("################ PlayBackError")
        self.updatePositionTimerData['stop'] = True
        self.onStateChange("PlayBackError")
        ADDON.setSetting('vosd.arg', 'false')

    def onPlayBackPaused(self):
        deb("################ Im paused")
        # self.playerStateChanged("Paused")
        # threading.Timer(0.3, self.stopplaying).start()

    def onPlayBackResumed(self):
        deb("################ Im Resumed")
        # self.onStateChange("Resumed")

    def onPlayBackStarted(self):
        deb("################ Playback Started")
        self.updatePositionTimerData['stop'] = True
        self.onStateChange("Started")
        try:
            playedFile = xbmc.Player().getPlayingFile()
            if os.path.isfile(playedFile):
                try:
                    playlistFileName = re.sub('_part_\d*.mpeg', '.mpeg', playedFile)
                    currentPositionInPlaylist = int(xbmc.PlayList(xbmc.PLAYLIST_VIDEO).getposition())
                    self.recordedFilesPlaylistPositions[playlistFileName] = currentPositionInPlaylist
                    deb('onPlayBackStarted updating playlist position to: {} file: {}'.format(currentPositionInPlaylist,
                                                                                              playlistFileName))
                except:
                    pass
                try:
                    seek = int(self.recordedFilesPositions[playedFile])
                    deb('onPlayBackStarted seeking file: {}, for {} seconds'.format(playedFile, seek))
                    time.sleep(1)
                    xbmc.Player().seekTime(seek)
                except:
                    pass
                self.updatePositionTimerData = {'filename': playedFile, 'stop': False}
                self.updatePositionTimer = threading.Timer(10, self.updatePosition, [self.updatePositionTimerData])
                self.updatePositionTimer.start()
        except:
            pass

    def onPlayBackEnded(self):
        xbmc.sleep(100)
        deb("################# Playback Ended")
        self.updatePositionTimerData['stop'] = True
        self.onStateChange("Ended")
        ADDON.setSetting('vosd.arg', 'false')

    def onPlayBackStopped(self):
        xbmc.sleep(100)
        deb("################# Playback Stopped")
        self.updatePositionTimerData['stop'] = True
        self.onStateChange("Stopped")
        ADDON.setSetting('vosd.arg', 'false') 

    def updatePosition(self, updatePositionTimerData):
        try:
            fileName = updatePositionTimerData['filename']
            while updatePositionTimerData['stop'] == False:
                self.recordedFilesPositions[fileName] = xbmc.Player().getTime()
                for sleepTime in range(5):
                    if updatePositionTimerData['stop'] == True:
                        break
                    time.sleep(1)
        except:
            pass

    def close(self):
        self.updatePositionTimerData['stop'] = True
        if self.updatePositionTimer is not None:
            self.updatePositionTimer.cancel()


class mTVGuide(xbmcgui.WindowXML):
    C_MAIN_DATE = 4000

    C_MAIN_TIMEBAR = 4100
    C_MAIN_TIMEBAR_BACK = 4101
    C_MAIN_LOADING = 4200
    C_MAIN_LOADING_BACKGROUND = 4199
    C_MAIN_LOADING_PROGRESS = 4201
    C_MAIN_LOADING_TIME_LEFT = 4202
    C_MAIN_LOADING_CANCEL = 4203
    C_MAIN_MOUSEPANEL_CONTROLS = 4300
    C_MAIN_MOUSEPANEL_HOME = 4301
    C_MAIN_MOUSEPANEL_EPG_PAGE_LEFT = 4302
    C_MAIN_MOUSEPANEL_EPG_PAGE_UP = 4303
    C_MAIN_MOUSEPANEL_EPG_PAGE_DOWN = 4304
    C_MAIN_MOUSEPANEL_EPG_PAGE_RIGHT = 4305
    C_MAIN_MOUSEPANEL_EXIT = 4306
    C_MAIN_MOUSEPANEL_CURSOR_UP = 4307
    C_MAIN_MOUSEPANEL_CURSOR_DOWN = 4308
    C_MAIN_MOUSEPANEL_CURSOR_LEFT = 4309
    C_MAIN_MOUSEPANEL_CURSOR_RIGHT = 4310
    C_MAIN_MOUSEPANEL_SETTINGS = 4311

    C_MAIN_BACKGROUND = 4600
    C_MAIN_EPG = 5000
    C_MAIN_EPG_VIEW_MARKER = 5001
    C_MAIN_INFO = 7000
    C_MAIN_LIVE = 4944

    C_CHANNEL_LABEL_START_INDEX_SHORTCUT = 4010
    C_CHANNEL_IMAGE_START_INDEX_SHORTCUT = 4110
    C_CHANNEL_NUMBER_START_INDEX_SHORTCUT = 4410

    C_CHANNEL_LABEL_START_INDEX = 4510
    C_CHANNEL_IMAGE_START_INDEX = 4210

    C_DYNAMIC_COLORS = 4500
    C_MAIN_CATEGORY = 7900
    C_MAIN_CALC_TIME_EPG = 4232

    C_MAIN_DAY = 4960 
    C_MAIN_REAL_DATE = 4961         
    C_MAIN_CALC_TIME_EPG = 4232    

    def __new__(cls):
        return super(mTVGuide, cls).__new__(cls, 'script-tvguide-main.xml', Skin.getSkinBasePath(), Skin.getSkinName(), defaultRes=skin_resolution)

    def __init__(self):
        deb('')
        deb('###################################################################################')
        deb('')
        deb('m-TVGuide __init__ System: {}, ARH: {}, python: {}, version: {}, kodi: {}'.format(platform.system(),
                                                                                               platform.machine(),
                                                                                               platform.python_version(),
                                                                                               ADDON.getAddonInfo(
                                                                                                   'version'),
                                                                                               xbmc.getInfoLabel(
                                                                                                   'System.BuildVersion')))
        deb('')
        deb('###################################################################################')
        deb('')
        super(mTVGuide, self).__init__()
        self.database = None
        self.notification = None
        self.infoDialog = None
        self.currentChannel = None
        self.lastChannel = None
        self.program = None
        self.onFocusTimer = None
        self.updateTimebarTimer = None
        self.rssFeed = None
        self.timer = None
        self.initialized = False
        self.redrawingEPG = False
        self.isClosing = False
        self.redrawagain = False
        self.info = False
        self.osd = None
        self.timebar = None
        self.timebarBack = None
        self.dontBlockOnAction = False
        self.playingRecordedProgram = False
        self.blockInputDueToRedrawing = False
        self.channelIdx = 0
        self.focusPoint = Point()
        self.epgView = EPGView()
        self.a = {}
        self.mode = MODE_EPG
        self.channel_number_input = False
        self.channel_number = ADDON.getSetting('channel.arg')
        self.current_channel_id = None
        self.controlAndProgramList = list()
        self.ignoreMissingControlIds = list()
        self.recordedFilesPlaylistPositions = {}
        self.streamingService = streaming.StreamsService()
        self.playService = playService.PlayService()
        self.recordService = RecordService(self)
        self.getListLenght = list()
        self.catchupDays = None

        # find nearest half hour
        self.viewStartDate = datetime.datetime.today() + datetime.timedelta(
            minutes=int(ADDON.getSetting('timebar_adjust')))
        self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)

        self.lastKeystroke = datetime.datetime.now()
        self.lastCloseKeystroke = datetime.datetime.now()
        # monitorowanie zmiany stanu odtwarzacza
        threading.Timer(0.3, self.playerstate).start()
        self.autoUpdateCid = ADDON.getSetting('AutoUpdateCid')

        self.archiveService = ''
        self.archivePlaylist = ''

        self.ignoreMissingControlIds.append(C_MAIN_CHAN_NAME)
        self.ignoreMissingControlIds.append(C_MAIN_CHAN_PLAY)
        self.ignoreMissingControlIds.append(C_MAIN_PROG_PLAY)
        self.ignoreMissingControlIds.append(C_MAIN_TIME_PLAY)
        self.ignoreMissingControlIds.append(C_MAIN_NUMB_PLAY)
        self.ignoreMissingControlIds.append(self.C_MAIN_CALC_TIME_EPG)
        self.ignoreMissingControlIds.append(self.C_MAIN_CATEGORY)
        self.ignoreMissingControlIds.append(self.C_DYNAMIC_COLORS)

        if sys.version_info[0] > 2:
            try:
                self.profilePath  = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
            except:
                self.profilePath  = xbmcvfs.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')
        else:
            try:
                self.profilePath  = xbmc.translatePath(ADDON.getAddonInfo('profile'))
            except:
                self.profilePath  = xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')

        if sys.version_info[0] > 2:
            self.kodiPath = xbmcvfs.translatePath("special://home/")
            self.kodiPathMain = xbmcvfs.translatePath("special://xbmc/")
            self.kodiSkinPath = xbmcvfs.translatePath("special://skin/")
        else:
            self.kodiPath = xbmc.translatePath("special://home/")
            self.kodiPathMain = xbmc.translatePath("special://xbmc/")
            self.kodiSkinPath = xbmc.translatePath("special://skin/")

        if ADDON.getSetting('refresh_streams') == 'true':
            self.refreshStreamsTimer = threading.Timer(REFRESH_STREAMS_TIME, self.refreshStreamsLoop)
            self.refreshStreamsTimer.start()
        else:
            self.refreshStreamsTimer = None
        
        if ADDON.getSetting('skin_fontpack') == 'true':
            self.skinsFix()
            self.changeFonts()

        self.loadSettings()
        self.tutorialExec()

        self.cat_index = 0
        
        self.interval = 0

    def tutorialGetEPG(self):
        res = xbmcgui.Dialog().select(strings(59940), [strings(59906), strings(59908)])

        if res < 0:
            res = xbmcgui.Dialog().yesno(strings(59924), strings(59938))
            if res:
                ADDON.setSetting('m-TVGuide', 'http://mods-kodi.pl/')
                ADDON.setSetting('xmltv_file', '')
                ADDON.setSetting('tutorial', 'true')
                exit()
            else:
                self.tutorialGetEPG()

        if res == 0:
            ADDON.setSetting('source', '1')
            kb = xbmc.Keyboard('','')
            kb.setHeading(strings(59941))
            kb.setHiddenInput(False)
            kb.doModal()
            c = kb.getText() if kb.isConfirmed() else None
            if c == '': c = None

            ADDON.setSetting('m-TVGuide', c)
            
            if c is not None:
                self.tutorialGetCountry()
            else:
                self.tutorialGetEPG()


        elif res == 1:
            ADDON.setSetting('source', '0')
            fn = xbmcgui.Dialog().browse(1, strings(59942), '')
            ADDON.setSetting('xmltv_file', fn)
            if fn != '':
                self.tutorialGetCountry()
            else:
                self.tutorialGetEPG()


    def tutorialGetCountry(self):
        progExec = False

        res = xbmcgui.Dialog().multiselect(strings(59943),
                    [strings(59925), strings(59926), strings(59927), strings(59928), strings(59929), strings(59930),
                 strings(59931), strings(59932), strings(59933), strings(59934), strings(59935), strings(59936), strings(59937), 'Radio'])

        if not res:
            resBack = xbmcgui.Dialog().yesno(strings(59924), strings(59938), yeslabel=strings(59939), nolabel=strings(30308))

            if resBack:
                self.tutorialGetEPG()

            else:
                ADDON.setSetting('tutorial', 'true')
                exit()

        if set(res):
            resExtra = xbmcgui.Dialog().yesno(strings(59924), strings(59962))

        if 0 in res:
            label = strings(59963)
            ADDON.setSetting('country_code_be', 'true')
            if resExtra:
                response = xbmcgui.Dialog().yesno(strings(59924), strings(59944).format(label))
                if response:
                    ADDON.setSetting('source', 'm-TVGuide')
                    kb = xbmc.Keyboard('','')
                    kb.setHeading(strings(59945).format(label))
                    kb.setHiddenInput(False)
                    kb.doModal()
                    c = kb.getText() if kb.isConfirmed() else None
                    if c == '': c = None
                    
                    ADDON.setSetting('epg_be', c)
                    if c is not None:
                        progExec = True

                    else:
                        ADDON.setSetting('country_code_be', 'false')
                        self.tutorialGetCountry()

                else:
                    progExec = True

            else:
                progExec = True

        if 1 in res:
            label = strings(59964)
            ADDON.setSetting('country_code_cz', 'true')
            if resExtra:
                response = xbmcgui.Dialog().yesno(strings(59924), strings(59944).format(label))
                if response:
                    ADDON.setSetting('source', 'm-TVGuide')
                    kb = xbmc.Keyboard('','')
                    kb.setHeading(strings(59945).format(label))
                    kb.setHiddenInput(False)
                    kb.doModal()
                    c = kb.getText() if kb.isConfirmed() else None
                    if c == '': c = None
                    
                    ADDON.setSetting('epg_cz', c)
                    if c is not None:
                        progExec = True

                    else:
                        ADDON.setSetting('country_code_cz', 'false')
                        self.tutorialGetCountry()
                else:
                    progExec = True

            else:
                progExec = True

        if 2 in res:
            label = strings(59965)
            ADDON.setSetting('country_code_de', 'true')
            if resExtra:
                response = xbmcgui.Dialog().yesno(strings(59924), strings(59944).format(label))
                if response:
                    ADDON.setSetting('source', 'm-TVGuide')
                    kb = xbmc.Keyboard('','')
                    kb.setHeading(strings(59945).format(label))
                    kb.setHiddenInput(False)
                    kb.doModal()
                    c = kb.getText() if kb.isConfirmed() else None
                    if c == '': c = None
                    
                    ADDON.setSetting('epg_de', c)
                    if c is not None:
                        progExec = True

                    else:
                        ADDON.setSetting('country_code_de', 'false')
                        self.tutorialGetCountry()
                else:
                    progExec = True

            else:
                progExec = True

        if 3 in res:
            label = strings(59966)
            ADDON.setSetting('country_code_dk', 'true')
            if resExtra:
                response = xbmcgui.Dialog().yesno(strings(59924), strings(59944).format(label))
                if response:
                    ADDON.setSetting('source', 'm-TVGuide')
                    kb = xbmc.Keyboard('','')
                    kb.setHeading(strings(59945).format(label))
                    kb.setHiddenInput(False)
                    kb.doModal()
                    c = kb.getText() if kb.isConfirmed() else None
                    if c == '': c = None
                    
                    ADDON.setSetting('epg_dk', c)
                    if c is not None:
                        progExec = True

                    else:
                        ADDON.setSetting('country_code_dk', 'false')
                        self.tutorialGetCountry()
                else:
                    progExec = True

            else:
                progExec = True

        if 4 in res:
            label = strings(59967)
            ADDON.setSetting('country_code_fr', 'true')
            if resExtra:
                response = xbmcgui.Dialog().yesno(strings(59924), strings(59944).format(label))
                if response:
                    ADDON.setSetting('source', 'm-TVGuide')
                    kb = xbmc.Keyboard('','')
                    kb.setHeading(strings(59945).format(label))
                    kb.setHiddenInput(False)
                    kb.doModal()
                    c = kb.getText() if kb.isConfirmed() else None
                    if c == '': c = None
                    
                    ADDON.setSetting('epg_fr', c)
                    if c is not None:
                        progExec = True

                    else:
                        ADDON.setSetting('country_code_fr', 'false')
                        self.tutorialGetCountry()
                else:
                    progExec = True

            else:
                progExec = True

        if 5 in res:
            label = strings(59968)
            ADDON.setSetting('country_code_hr', 'true')
            if resExtra:
                response = xbmcgui.Dialog().yesno(strings(59924), strings(59944).format(label))
                if response:
                    ADDON.setSetting('source', 'm-TVGuide')
                    kb = xbmc.Keyboard('','')
                    kb.setHeading(strings(59945).format(label))
                    kb.setHiddenInput(False)
                    kb.doModal()
                    c = kb.getText() if kb.isConfirmed() else None
                    if c == '': c = None
                    
                    ADDON.setSetting('epg_hr', c)
                    if c is not None:
                        progExec = True

                    else:
                        ADDON.setSetting('country_code_hr', 'false')
                        self.tutorialGetCountry()
                else:
                    progExec = True

            else:
                progExec = True

        if 6 in res:
            label = strings(59969)
            ADDON.setSetting('country_code_it', 'true')
            if resExtra:
                response = xbmcgui.Dialog().yesno(strings(59924), strings(59944).format(label))
                if response:
                    ADDON.setSetting('source', 'm-TVGuide')
                    kb = xbmc.Keyboard('','')
                    kb.setHeading(strings(59945).format(label))
                    kb.setHiddenInput(False)
                    kb.doModal()
                    c = kb.getText() if kb.isConfirmed() else None
                    if c == '': c = None
                    
                    ADDON.setSetting('epg_it', c)
                    if c is not None:
                        progExec = True

                    else:
                        ADDON.setSetting('country_code_it', 'false')
                        self.tutorialGetCountry()
                else:
                    progExec = True

            else:
                progExec = True

        if 7 in res:
            label = strings(59970)
            ADDON.setSetting('country_code_no', 'true')
            if resExtra:
                response = xbmcgui.Dialog().yesno(strings(59924), strings(59944).format(label))
                if response:
                    ADDON.setSetting('source', 'm-TVGuide')
                    kb = xbmc.Keyboard('','')
                    kb.setHeading(strings(59945).format(label))
                    kb.setHiddenInput(False)
                    kb.doModal()
                    c = kb.getText() if kb.isConfirmed() else None
                    if c == '': c = None
                    
                    ADDON.setSetting('epg_no', c)
                    if c is not None:
                        progExec = True

                    else:
                        ADDON.setSetting('country_code_no', 'false')
                        self.tutorialGetCountry()
                else:
                    progExec = True

            else:
                progExec = True

        if 8 in res:
            label = strings(59971)
            ADDON.setSetting('country_code_pl', 'true')
            if resExtra:
                response = xbmcgui.Dialog().yesno(strings(59924), strings(59944).format(label))
                if response:
                    ADDON.setSetting('source', 'm-TVGuide')
                    kb = xbmc.Keyboard('','')
                    kb.setHeading(strings(59945).format(label))
                    kb.setHiddenInput(False)
                    kb.doModal()
                    c = kb.getText() if kb.isConfirmed() else None
                    if c == '': c = None
                    
                    ADDON.setSetting('m-TVGuide', c)
                    if c is not None:
                        progExec = True

                    else:
                        ADDON.setSetting('country_code_pl', 'false')
                        self.tutorialGetCountry()
                else:
                    progExec = True

            else:
                progExec = True

        if 9 in res:
            label = strings(59972)
            ADDON.setSetting('country_code_se', 'true')
            if resExtra:
                response = xbmcgui.Dialog().yesno(strings(59924), strings(59944).format(label))
                if response:
                    ADDON.setSetting('source', 'm-TVGuide')
                    kb = xbmc.Keyboard('','')
                    kb.setHeading(strings(59945).format(label))
                    kb.setHiddenInput(False)
                    kb.doModal()
                    c = kb.getText() if kb.isConfirmed() else None
                    if c == '': c = None
                    
                    ADDON.setSetting('epg_se', c)
                    if c is not None:
                        progExec = True

                    else:
                        ADDON.setSetting('country_code_se', 'false')
                        self.tutorialGetCountry()
                else:
                    progExec = True

            else:
                progExec = True

        if 10 in res:
            label = strings(59973)
            ADDON.setSetting('country_code_srb', 'true')
            if resExtra:
                response = xbmcgui.Dialog().yesno(strings(59924), strings(59944).format(label))
                if response:
                    ADDON.setSetting('source', 'm-TVGuide')
                    kb = xbmc.Keyboard('','')
                    kb.setHeading(strings(59945).format(label))
                    kb.setHiddenInput(False)
                    kb.doModal()
                    c = kb.getText() if kb.isConfirmed() else None
                    if c == '': c = None
                    
                    ADDON.setSetting('epg_srb', c)
                    if c is not None:
                        progExec = True

                    else:
                        ADDON.setSetting('country_code_srb', 'false')
                        self.tutorialGetCountry()
                else:
                    progExec = True

            else:
                progExec = True

        if 11 in res:
            label = strings(59974)
            ADDON.setSetting('country_code_uk', 'true')
            if resExtra:
                response = xbmcgui.Dialog().yesno(strings(59924), strings(59944).format(label))
                if response:
                    ADDON.setSetting('source', 'm-TVGuide')
                    kb = xbmc.Keyboard('','')
                    kb.setHeading(strings(59945).format(label))
                    kb.setHiddenInput(False)
                    kb.doModal()
                    c = kb.getText() if kb.isConfirmed() else None
                    if c == '': c = None
                    
                    ADDON.setSetting('epg_uk', c)
                    if c is not None:
                        progExec = True

                    else:
                        ADDON.setSetting('country_code_uk', 'false')
                        self.tutorialGetCountry()
                else:
                    progExec = True

            else:
                progExec = True

        if 12 in res:
            label = strings(59975)
            ADDON.setSetting('country_code_us', 'true')
            if resExtra:
                response = xbmcgui.Dialog().yesno(strings(59924), strings(59944).format(label))
                if response:
                    ADDON.setSetting('source', 'm-TVGuide')
                    kb = xbmc.Keyboard('','')
                    kb.setHeading(strings(59945).format(label))
                    kb.setHiddenInput(False)
                    kb.doModal()
                    c = kb.getText() if kb.isConfirmed() else None
                    if c == '': c = None
                    
                    ADDON.setSetting('epg_us', c)
                    if c is not None:
                        progExec = True

                    else:
                        ADDON.setSetting('country_code_us', 'false')
                        self.tutorialGetCountry()
                else:
                    progExec = True

            else:
                progExec = True


        if 13 in res:
            label = 'Radio'
            ADDON.setSetting('country_code_radio', 'true')
            if resExtra:
                response = xbmcgui.Dialog().yesno(strings(59924), strings(59944).format(label))
                if response:
                    ADDON.setSetting('source', 'm-TVGuide')
                    kb = xbmc.Keyboard('','')
                    kb.setHeading(strings(59945).format(label))
                    kb.setHiddenInput(False)
                    kb.doModal()
                    c = kb.getText() if kb.isConfirmed() else None
                    if c == '': c = None
                    
                    ADDON.setSetting('epg_radio', c)
                    if c is not None:
                        progExec = True

                    else:
                        ADDON.setSetting('country_code_radio', 'false')
                        self.tutorialGetCountry()
                else:
                    progExec = True

            else:
                progExec = True

        if progExec is True:
            self.tutorialGetService()

    def tutorialGetService(self):
        progExec = False

        res = xbmcgui.Dialog().select(strings(59946),
                    [strings(59947), strings(59948)])

        if res < 0:
            resBack = xbmcgui.Dialog().yesno(strings(59924), strings(59938), yeslabel=strings(59939), nolabel=strings(30308))
            if resBack:
                self.tutorialGetCountry()

            else:
                ADDON.setSetting('tutorial', 'true')
                exit()

        if res == 0:
            res = xbmcgui.Dialog().multiselect(strings(59949), 
                    [strings(59920), strings(59921), strings(59922), strings(80006), strings(59923), strings(30903), strings(30904), strings(80005)])


            if not res:
                resBack = xbmcgui.Dialog().yesno(strings(59924), strings(59938), yeslabel=strings(59939), nolabel=strings(30308))
                if resBack:
                    self.tutorialGetService()

                else:
                    ADDON.setSetting('tutorial', 'true')
                    exit()

            if 0 in res:
                label = 'C More'
                xbmcgui.Dialog().ok(label, strings(59950).format(label))
                ADDON.setSetting('cmore_enabled', 'true')
                response = xbmcgui.Dialog().yesno(label, strings(59951))

                if response:
                    ADDON.setSetting('cmore_tv_provider_login', 'true')
                    progExec = True

                else:
                    kb = xbmc.Keyboard('','')
                    kb.setHeading(strings(59952) + ' ({})'.format(label))
                    kb.setHiddenInput(False)
                    kb.doModal()
                    login = kb.getText() if kb.isConfirmed() else self.tutorialGetService()
                    if login == '': login = self.tutorialGetService()

                    if login != '':
                        ADDON.setSetting('cmore_username', login)
                        kb = xbmc.Keyboard('','')
                        kb.setHeading(strings(59953) + ' ({})'.format(label))
                        kb.setHiddenInput(True)
                        kb.doModal()
                        pswd = kb.getText() if kb.isConfirmed() else self.tutorialGetService()
                        if pswd == '': pswd = self.tutorialGetService()

                        ADDON.setSetting('cmore_password', pswd)
                        if pswd != '':
                            progExec = True

                        else:
                            ADDON.setSetting('cmore_enabled', 'false')
                            self.tutorialGetService()

                    else:
                        ADDON.setSetting('cmore_enabled', 'false')
                        self.tutorialGetService()

            if 1 in res:
                label = 'Cyfrowy Polsat GO'
                xbmcgui.Dialog().ok(label, strings(59950).format(label))
                ADDON.setSetting('cpgo_enabled', 'true')
                kb = xbmc.Keyboard('','')
                kb.setHeading(strings(59952) + ' ({})'.format(label))
                kb.setHiddenInput(False)
                kb.doModal()
                login = kb.getText() if kb.isConfirmed() else self.tutorialGetService()
                if login == '': login = self.tutorialGetService()

                if login != '':
                    ADDON.setSetting('cpgo_username', login)
                    kb = xbmc.Keyboard('','')
                    kb.setHeading(strings(59953) + ' ({})'.format(label))
                    kb.setHiddenInput(True)
                    kb.doModal()
                    pswd = kb.getText() if kb.isConfirmed() else self.tutorialGetService()
                    if pswd == '': pswd = self.tutorialGetService()

                    ADDON.setSetting('cpgo_password', pswd)
                    if pswd != '':
                        progExec = True

                    else:
                        ADDON.setSetting('cpgo_enabled', 'false')
                        self.tutorialGetService()

                else:
                    ADDON.setSetting('cpgo_enabled', 'false')
                    self.tutorialGetService()

            if 2 in res:
                label = 'FranceTV'
                xbmcgui.Dialog().ok(label, strings(59950).format(label))
                ADDON.setSetting('francetv_enabled', 'true')

            if 3 in res:
                label = 'Ipla'
                xbmcgui.Dialog().ok(label, strings(59950).format(label))
                ADDON.setSetting('ipla_enabled', 'true')
                kb = xbmc.Keyboard('','')
                kb.setHeading(strings(59952) + ' ({})'.format(label))
                kb.setHiddenInput(False)
                kb.doModal()
                login = kb.getText() if kb.isConfirmed() else self.tutorialGetService()
                if login == '': login = self.tutorialGetService()

                if login != '':
                    ADDON.setSetting('ipla_username', login)
                    kb = xbmc.Keyboard('','')
                    kb.setHeading(strings(59953) + ' ({})'.format(label))
                    kb.setHiddenInput(True)
                    kb.doModal()
                    pswd = kb.getText() if kb.isConfirmed() else self.tutorialGetService()
                    if pswd == '': pswd = self.tutorialGetService()

                    ADDON.setSetting('ipla_password', pswd)
                    if pswd != '':
                        progExec = True

                    else:
                        ADDON.setSetting('ipla_enabled', 'false')
                        self.tutorialGetService()

                else:
                    ADDON.setSetting('ipla_enabled', 'false')
                    self.tutorialGetService()

            if 4 in res:
                label = 'nc+ GO'
                xbmcgui.Dialog().ok(label, strings(59950).format(label))
                ADDON.setSetting('ncplusgo_enabled', 'true')
                kb = xbmc.Keyboard('','')
                kb.setHeading(strings(59952) + ' ({})'.format(label))
                kb.setHiddenInput(False)
                kb.doModal()
                login = kb.getText() if kb.isConfirmed() else self.tutorialGetService()
                if login == '': login = self.tutorialGetService()

                if login != '':
                    ADDON.setSetting('ncplusgo_username', login)
                    kb = xbmc.Keyboard('','')
                    kb.setHeading(strings(59953) + ' ({})'.format(label))
                    kb.setHiddenInput(True)
                    kb.doModal()
                    pswd = kb.getText() if kb.isConfirmed() else self.tutorialGetService()
                    if pswd == '': pswd = self.tutorialGetService()

                    ADDON.setSetting('ncplusgo_password', pswd)
                    if pswd != '':
                        progExec = True

                    else:
                        ADDON.setSetting('ncplusgo_enabled', 'false')
                        self.tutorialGetService()

                else:
                    ADDON.setSetting('ncplusgo_enabled', 'false')
                    self.tutorialGetService()

            if 5 in res:
                label = 'PlayerPL'
                xbmcgui.Dialog().ok(label, strings(59950).format(label))
                ADDON.setSetting('playerpl_enabled', 'true')

            if 6 in res:
                label = 'Telia Play'
                xbmcgui.Dialog().ok(label, strings(59950).format(label))
                ADDON.setSetting('teliaplay_enabled', 'true')
                kb = xbmc.Keyboard('','')
                kb.setHeading(strings(59952) + ' ({})'.format(label))
                kb.setHiddenInput(False)
                kb.doModal()
                login = kb.getText() if kb.isConfirmed() else self.tutorialGetService()
                if login == '': login = self.tutorialGetService()

                if login != '':
                    ADDON.setSetting('teliaplay_username', login)
                    kb = xbmc.Keyboard('','')
                    kb.setHeading(strings(59953) + ' ({})'.format(label))
                    kb.setHiddenInput(True)
                    kb.doModal()
                    pswd = kb.getText() if kb.isConfirmed() else self.tutorialGetService()
                    if pswd == '': pswd = self.tutorialGetService()

                    ADDON.setSetting('teliaplay_password', pswd)
                    if pswd != '':
                        progExec = True

                    else:
                        ADDON.setSetting('teliaplay_enabled', 'false')
                        self.tutorialGetService()

                else:
                    ADDON.setSetting('teliaplay_enabled', 'false')
                    self.tutorialGetService()

            if 7 in res:
                label = 'WP Pilot'
                xbmcgui.Dialog().ok(label, strings(59950).format(label))
                ADDON.setSetting('videostar_enabled', 'true')
                kb = xbmc.Keyboard('','')
                kb.setHeading(strings(59952) + ' ({})'.format(label))
                kb.setHiddenInput(False)
                kb.doModal()
                login = kb.getText() if kb.isConfirmed() else self.tutorialGetService()
                if login == '': login = self.tutorialGetService()

                if login != '':
                    ADDON.setSetting('videostar_username', login)
                    kb = xbmc.Keyboard('','')
                    kb.setHeading(strings(59953) + ' ({})'.format(label))
                    kb.setHiddenInput(True)
                    kb.doModal()
                    pswd = kb.getText() if kb.isConfirmed() else self.tutorialGetService()
                    if pswd == '': pswd = self.tutorialGetService()

                    ADDON.setSetting('videostar_password', pswd)
                    if pswd != '':
                        progExec = True

                    else:
                        ADDON.setSetting('videostar_enabled', 'false')
                        self.tutorialGetService()

                else:
                    ADDON.setSetting('videostar_enabled', 'false')
                    self.tutorialGetService()

            if progExec is True:
                self.tutorialGetRecording()

        elif res == 1:
            ADDON.setSetting('nr_of_playlists', '1')
            ADDON.setSetting('playlist_1_enabled', 'true')
            res = xbmcgui.Dialog().select(strings(59954),
                    [strings(59906), strings(59908)])

            if res < 0:
                res = xbmcgui.Dialog().yesno(strings(59924), strings(59938), yeslabel=strings(59939), nolabel=strings(30308))
                if res: 
                    ADDON.setSetting('nr_of_playlists', '0')
                    ADDON.setSetting('playlist_1_enabled', 'false')
                    ADDON.setSetting('playlist_1_file', '')
                    ADDON.setSetting('tutorial', 'true')
                    exit()
                else:
                    self.tutorialGetService()

            elif res == 0:
                ADDON.setSetting('playlist_1_source', '0')
                kb = xbmc.Keyboard('','')
                kb.setHeading(strings(59955))
                kb.setHiddenInput(False)
                kb.doModal()
                c = kb.getText() if kb.isConfirmed() else None
                if c == '': c = None
                
                ADDON.setSetting('playlist_1_url', c)
                if c is not None:
                    self.tutorialGetRecording()

                else:
                    self.tutorialGetService()

            elif res == 1:
                ADDON.setSetting('playlist_1_source', '1')
                fn = xbmcgui.Dialog().browse(1, strings(59956), '')
                ADDON.setSetting('playlist_1_file', fn)
                if fn != '':
                    self.tutorialGetRecording()
                else:
                    self.tutorialGetService()

    def tutorialGetRecording(self):
        res = xbmcgui.Dialog().yesno(strings(59924), strings(59957))
        if res:
            fn = xbmcgui.Dialog().browse(3, strings(59958), '')
            ADDON.setSetting('record_folder', fn)
            if fn == '':
                res = xbmcgui.Dialog().yesno(strings(59924), strings(59938), yeslabel=strings(59939), nolabel=strings(30308))
                if res: 
                    self.tutorialGetRecording()

                else:
                    xbmcgui.Dialog().ok(strings(59924), strings(59961))
                    ADDON.setSetting('record_folder', '')
                    ADDON.setSetting('tutorial', 'false')
                    xbmcgui.Dialog().ok(strings(70100), strings(70102))
                    xbmc.executebuiltin("Quit")
                    
            else:
                run = SettingsImp().downloadRecordApp()
                ADDON.setSetting('tutorial', 'false')
                xbmcgui.Dialog().ok(strings(70100), strings(70102))
                xbmc.executebuiltin("Quit")

        else:
            ADDON.setSetting('tutorial', 'false')
            xbmcgui.Dialog().ok(strings(70100), strings(70102))
            xbmc.executebuiltin("Quit")

    def tutorialExec(self):
        if ADDON.getSetting('tutorial') == 'false':
            if ADDON.getSetting('source') == '0':
                if ADDON.getSetting('xmltv_file') == '':
                    ADDON.setSetting('tutorial', 'true')
                else:
                    ADDON.setSetting('tutorial', 'false')

            if ADDON.getSetting('source') == '1':
                if ADDON.getSetting('m-TVGuide') == 'http://mods-kodi.pl/' or ADDON.getSetting('m-TVGuide') == '':
                    ADDON.setSetting('tutorial', 'true')
                else:
                    ADDON.setSetting('tutorial', 'false')
        
        if ADDON.getSetting('tutorial') == 'true':
            res = xbmcgui.Dialog().yesno(strings(59924), strings(59959))
            if res == False:
                ADDON.setSetting('tutorial', 'false')
                exit()
            elif res == True:
                res = xbmcgui.Dialog().ok(strings(59924), strings(59960))
                if res == False:
                    xbmcgui.Dialog().ok(strings(59924), strings(59938))
                    ADDON.setSetting('tutorial', 'true')
                    exit()
                else:
                    self.tutorialGetEPG()
                        
            else:
                ADDON.setSetting('tutorial', 'true')
                exit()

    def changeFonts(self):
        addonSkin = ADDON.getSetting('Skin')
        currentSkin = xbmc.getSkinDir()

        chkSkin = ADDON.getSetting('Skin')
        if chkSkin =='skin.default':
            chkSkin = 'skin.estuary'

        if chkSkin != currentSkin:
            xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Settings.SetSettingValue","id":1,"params":{"setting":"lookandfeel.font","value":"'+addonSkin+' Default"}}')

    def skinsFix(self):
        addonSkin = ADDON.getSetting('Skin')
        currentSkin = xbmc.getSkinDir()
        c1 = str(currentSkin)
        c2 = ''

        # Check files
        checkDirProfile = xbmcvfs.listdir(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, 'fonts'))
        for item in checkDirProfile:
            r = re.compile('(.*?).ttf')
            if sys.version_info[0] > 2:
                checkProfileFonts = list(filter(r.match, item))
            else:
                checkProfileFonts = filter(r.match, item)

        checkDirKodi = xbmcvfs.listdir(os.path.join(self.kodiSkinPath, 'fonts', addonSkin))
        for item in checkDirKodi:
            r = re.compile('(.*?).ttf')
            if sys.version_info[0] > 2:
                checkKodiFonts = list(filter(r.match, item))
            else:
                checkKodiFonts = filter(r.match, item)

        try:
            if xbmcvfs.exists(os.path.join(self.profilePath, 'fonts.list')) == 0:
                file = xbmcvfs.File(os.path.join(self.profilePath, 'fonts.list'), 'w+')
                file.write(str(''))
                file.close()
            else:
                file_add = xbmcvfs.File(os.path.join(self.profilePath, 'fonts.list'), 'r')
                checkCurrentSkin = file_add.read()
                c2 = str(checkCurrentSkin)

        except:
            deb('obsolete fonts.list is missing')

        chkSkinProfile = addonSkin

        estuary = ['skin.default']
        confluence = ['skin.xx']

        if chkSkinProfile in estuary:
            chkSkinProfile = 'skin.estuary'
        elif chkSkinProfile in confluence:
            chkSkinProfile = 'skin.confluence'
        chkSkinKodi = currentSkin

        try:
            # Check path
            if xbmcvfs.exists(os.path.join(self.kodiPath, 'addons', chkSkinKodi, 'xml/')):
                path0 = 'xml'
            elif xbmcvfs.exists(os.path.join(self.kodiPath, 'addons', chkSkinKodi, '720p/')):
                path0 = '720p'
            elif xbmcvfs.exists(os.path.join(self.kodiPath, 'addons', chkSkinKodi, '1080i/')):
                path0 = '1080i'
            elif xbmcvfs.exists(os.path.join(self.kodiPath, 'addons', chkSkinKodi, '16x9/')):
                path0 = '16x9'

            if xbmcvfs.exists(os.path.join(self.kodiSkinPath, 'xml/')):
                path1 = 'xml'
            elif xbmcvfs.exists(os.path.join(self.kodiSkinPath, '720p/')):
                path1 = '720p'
            elif xbmcvfs.exists(os.path.join(self.kodiSkinPath, '1080i/')):
                path1 = '1080i'
            elif xbmcvfs.exists(os.path.join(self.kodiSkinPath, '16x9/')):
                path1 = '16x9'

            try:
                file_check = xbmcvfs.File(os.path.join(self.kodiPath, 'addons', chkSkinKodi, path0, 'Font.xml'), 'r')
            except:
                file_check = xbmcvfs.File(os.path.join(self.kodiSkinPath, path1, 'Font.xml'), 'r')
            font_check = file_check.read().find('fontset id="'+addonSkin)
        except:
            font_check = 0

        # Check skins
        match = re.search(c1, c2)
        if match:
            match = True
        else:
            match = False

        if font_check < 0:
            font = False
        if font_check == 0:
            font = True
        elif font_check > 0:
            font = True

        try:
            file_check.close()
        except:
            None

        # Final check
        if chkSkinProfile != chkSkinKodi:
            if sys.version_info[0] > 2:
                import functools 
                check = functools.reduce(lambda i, j : i and j, map(lambda m, k: m == k, checkProfileFonts, checkKodiFonts), True)
            else:
                check = set(checkProfileFonts) == set(checkKodiFonts)

            if check is False or font is False or match is False:
                # Background
                self.black = xbmcgui.ControlImage(0, 0, 1920, 1080, os.path.join(self.profilePath, 'resources', 'skins', addonSkin, 'media', 'osd', 'black.png')) 
                self.addControl(self.black)
                self.black.setVisibleCondition('True')

                # Information
                xbmcgui.Dialog().ok(strings(70100), strings(70101))

                # Skin change or install font pack
                res = xbmcgui.Dialog().contextmenu([strings(70105), strings(70104)])
                if res < 0:
                    exit()

                if res == 0:
                    # Check non-writeable skins
                    if chkSkinKodi == 'skin.estuary':
                        if xbmc.getSkinDir() == "skin.estuary":
                            sk = xbmcaddon.Addon(id="skin.estuary")
                            skinpath = sk.getAddonInfo("path")

                            if xbmcgui.Dialog().yesno(strings(70105), strings(70118).format(chkSkinKodi)):
                                if sys.version_info[0] > 2:
                                    dest = xbmcvfs.translatePath("special://home/")
                                else:
                                    dest = xbmc.translatePath("special://home/")
                                dest2 = os.path.join(dest, 'addons', 'skin.estuary/')
                                deb("checking for obsolete skin.estuary copy")
                                if xbmcvfs.exists(dest2) == False:
                                    deb("making a writeable skin.estuary copy")
                                    shutil.copytree(skinpath, dest2)

                            else:
                                xbmcgui.Dialog().ok(strings(70105), strings(70103))
                                exit()

                    if chkSkinKodi == 'skin.estouchy':
                        if xbmc.getSkinDir() == "skin.estouchy":
                            sk = xbmcaddon.Addon(id="skin.estouchy")
                            skinpath = sk.getAddonInfo("path")

                            if xbmcvfs.listdir(os.path.join(self.kodiPath, 'addons', 'skin.estouchy')) == False:
                                if xbmcgui.Dialog().yesno(strings(70105), strings(70118).format(chkSkinKodi)):
                                    if sys.version_info[0] > 2:
                                        dest = xbmcvfs.translatePath("special://home/")
                                    else:
                                        dest = xbmc.translatePath("special://home/")
                                    dest2 = os.path.join(dest, 'addons', 'skin.estouchy/')
                                    deb("checking for obsolete skin.estouchy copy")
                                    if xbmcvfs.exists(dest2) == False:
                                        deb("making a writeable skin.estouchy copy")
                                        shutil.copytree(skinpath, dest2)

                                else:
                                    xbmcgui.Dialog().ok(strings(70105), strings(70103))
                                    exit()

                    # Check path
                    if xbmcvfs.exists(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, 'xml/')):
                        path2 = 'xml'
                    elif xbmcvfs.exists(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, '720p/')):
                        path2 = '720p'
                    elif xbmcvfs.exists(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, '1080i/')):
                        path2 = '1080i'
                    elif xbmcvfs.exists(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, '16x9/')):
                        path2 = '16x9'

                    if xbmcvfs.exists(os.path.join(self.kodiPath, 'addons', chkSkinKodi, 'xml/')):
                        path3 = 'xml'
                    elif xbmcvfs.exists(os.path.join(self.kodiPath, 'addons', chkSkinKodi, '720p/')):
                        path3 = '720p'
                    elif xbmcvfs.exists(os.path.join(self.kodiPath, 'addons', chkSkinKodi, '1080i/')):
                        path3 = '1080i'
                    elif xbmcvfs.exists(os.path.join(self.kodiPath, 'addons', chkSkinKodi, '16x9/')):
                        path3 = '16x9'

                    # Kodi
                    if xbmcvfs.exists(os.path.join(self.kodiSkinPath, 'xml/')):
                        path4 = 'xml'
                    elif xbmcvfs.exists(os.path.join(self.kodiSkinPath, '720p/')):
                        path4 = '720p'
                    elif xbmcvfs.exists(os.path.join(self.kodiSkinPath, '1080i/')):
                        path4 = '1080i'
                    elif xbmcvfs.exists(os.path.join(self.kodiSkinPath, '16x9/')):
                        path4 = '16x9'
                    
                    #Backup Font.xml
                    check = xbmcvfs.exists(os.path.join(self.kodiPath, 'addons', chkSkinKodi, path3, 'Font.backup'))

                    if chkSkinKodi == 'skin.estuary' or chkSkinKodi == 'skin.estouchy':
                        source = os.path.join(self.kodiPathMain, 'addons', chkSkinKodi , path4, 'Font.xml')
                        destination = os.path.join(self.kodiPath, 'addons', chkSkinKodi, path3, 'Font.backup')
                        xbmcvfs.copy(source, destination)

                        sourcex = os.path.join(self.kodiPath, 'addons', chkSkinKodi, path3)
                        xbmcvfs.copy(os.path.join(sourcex, 'Font.backup'), os.path.join(sourcex, 'Font.xml'))
                        deb('creating backup Font.xml from non-writeable skin')

                    if chkSkinKodi != 'skin.estuary' or chkSkinKodi != 'skin.estouchy':
                        if check == 0:
                            source = os.path.join(self.kodiSkinPath, path4, 'Font.xml')
                            destination = os.path.join(self.kodiPath, 'addons', chkSkinKodi, path3, 'Font.backup')
                            xbmcvfs.copy(source, destination)
                            deb('creating backup Font.xml')

                    
                    source = os.path.join(self.kodiPath, 'addons', chkSkinKodi, path3)
                    xbmcvfs.copy(os.path.join(source, 'Font.backup'), os.path.join(source, 'Font.xml'))
                    deb('replacing Font.xml with backup')

                    # Check resolution
                    profile_xml = xbmcvfs.exists(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, 'xml', 'Font.xml'))
                    profile_720p = xbmcvfs.exists(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, '720p', 'Font.xml'))
                    profile_1080i = xbmcvfs.exists(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, '1080i', 'Font.xml'))
                    profile_16x9 = xbmcvfs.exists(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, '16x9', 'Font.xml'))

                    kodi_xml = xbmcvfs.exists(os.path.join(self.kodiSkinPath, 'xml', 'Font.xml'))
                    kodi_720p = xbmcvfs.exists(os.path.join(self.kodiSkinPath, '720p', 'Font.xml'))
                    kodi_1080i = xbmcvfs.exists(os.path.join(self.kodiSkinPath, '1080i', 'Font.xml'))
                    kodi_16x9 = xbmcvfs.exists(os.path.join(self.kodiSkinPath, '16x9', 'Font.xml'))

                    # Prepare Font.xml
                    try:
                        file_font_read = open(os.path.join(self.kodiSkinPath, path3, 'Font.xml'), 'r')
                        ext = file_font_read.read()

                        file_font_write = open(os.path.join(self.kodiPath, 'addons', chkSkinKodi, path3, 'Font.xml'), 'w')
                        ext = re.sub(r'\n</fonts>', '', str(ext))
                        file_font_write.write(ext)
                        file_font_write.close()
                        file_font_read.close()
                    except:
                        deb('IOError: [Errno 13] Permission denied')

                    # Font resize
                    file = xbmcvfs.File(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, path2, 'Font.xml'), 'r')
                    fileContent = file.read()
                    
                    if profile_1080i == 1 and kodi_720p == 1:
                        newSize = re.sub(r"(?s)(?<=<size>)\d+(?=</size>)",
                                   lambda m: str(int(m.group(0)) // 1.488), fileContent)
                        file_font_size = xbmcvfs.File(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, path2, 'Font.temp'), 'w+')
                        file_font_size.write(newSize)
                        file_font_size.close()

                    elif profile_xml == 1 and kodi_720p == 1:
                        newSize = re.sub(r"(?s)(?<=<size>)\d+(?=</size>)",
                                   lambda m: str(int(m.group(0)) // 1.488), fileContent)
                        file_font_size = xbmcvfs.File(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, path2, 'Font.temp'), 'w+')
                        file_font_size.write(newSize)
                        file_font_size.close()

                    elif profile_16x9 == 1 and kodi_720p == 1:
                        newSize = re.sub(r"(?s)(?<=<size>)\d+(?=</size>)",
                                   lambda m: str(int(m.group(0)) // 1.488), fileContent)
                        file_font_size = xbmcvfs.File(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, path2, 'Font.temp'), 'w+')
                        file_font_size.write(newSize)
                        file_font_size.close()

                    elif profile_720p == 1 and kodi_1080i == 1:
                        newSize = re.sub(r"(?s)(?<=<size>)\d+(?=</size>)", 
                                    lambda m: str(int(m.group(0)) * 1.488), fileContent)
                        file_font_size = xbmcvfs.File(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, path2, 'Font.temp'), 'w+')
                        file_font_size.write(newSize)
                        file_font_size.close()

                    elif profile_720p == 1 and kodi_xml == 1:
                        newSize = re.sub(r"(?s)(?<=<size>)\d+(?=</size>)",
                                    lambda m: str(int(m.group(0)) * 1.488), fileContent)
                        file_font_size = xbmcvfs.File(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, path2, 'Font.temp'), 'w+')
                        file_font_size.write(newSize)
                        file_font_size.close()

                    elif profile_720p == 1 and kodi_16x9 == 1:
                        newSize = re.sub(r"(?s)(?<=<size>)\d+(?=</size>)",
                                    lambda m: str(int(m.group(0)) * 1.488), fileContent)
                        file_font_size = xbmcvfs.File(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, path2, 'Font.temp'), 'w+')
                        file_font_size.write(newSize)
                        file_font_size.close()

                    else:
                        newSize = re.sub(r"(?s)(?<=<size>)\d+(?=</size>)",
                                    lambda m: str(int(m.group(0)) * 1.0), fileContent)
                        file_font_size = xbmcvfs.File(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, path2, 'Font.temp'), 'w+')
                        file_font_size.write(newSize)
                        file_font_size.close()

                    # Create Font.temp
                    if xbmcvfs.exists(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, path2, 'Font.temp')):
                        file_remove = open(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, path2, 'Font.temp'), 'r')
                        removeContent = file_remove.read()
                        file_remove.close()

                        file_temp = open(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, path2, 'Font.temp'), 'w')
                        removeContent = re.sub('<.*encoding=".*>', '', str(removeContent))
                        removeContent = re.sub('<fonts>', '', str(removeContent))
                        removeContent = re.sub(r'\n\n\t<fontset', '\t<fontset', str(removeContent))
                        removeContent = re.sub(r'\n\t<fontset', '\t<fontset', str(removeContent))
                        file_temp.write(removeContent)
                        file_temp.close()

                        file_temp_read = open(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, path2, 'Font.temp'), 'r')
                        append = file_temp_read.read()

                        try:
                            with open(os.path.join(self.kodiPath, 'addons', chkSkinKodi, path3, 'Font.xml'), 'a') as file_notemp_read:
                                file_notemp_read.write(append)
                        except:
                            deb('IOError: [Errno 13] Permission denied')
                        
                        file_temp_read.close()

                        # Removes Font.temp file
                        os.remove(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, path2, 'Font.temp'))

                        # Try deleting addon fonts folder in kodi skin
                        try:
                            source = os.path.join(self.kodiPath, 'addons', chkSkinKodi, 'fonts', addonSkin)
                            shutil.rmtree(source)
                        except:
                            deb('obsolete fonts missing')

                        # Fonts install
                        xbmc.sleep(1000)

                        source = os.path.join(self.profilePath, 'resources', 'skins', addonSkin, 'fonts')
                        destination = os.path.join(self.kodiPath, 'addons', chkSkinKodi, 'fonts', addonSkin)

                        try:
                            shutil.copytree(source, destination)
                        except:
                            deb('IOError: [Errno 13] Permission denied')

                        with open(os.path.join(self.profilePath, 'fonts.list'), 'w') as file_add:
                            file_add.write(currentSkin + '\n')
                            file_add.close()

                        # Backup colors
                        check = xbmcvfs.exists(os.path.join(self.kodiPath, 'addons', chkSkinKodi, 'colors', 'defaults.backup'))

                        if chkSkinKodi == 'skin.estuary' or chkSkinKodi == 'skin.estouchy':
                            source = os.path.join(self.kodiPathMain, 'addons', chkSkinKodi , 'colors', 'defaults.xml')
                            destination = os.path.join(self.kodiPath, 'addons', chkSkinKodi, 'colors', 'defaults.backup')
                            xbmcvfs.copy(source, destination)

                            sourcex = os.path.join(self.kodiPath, 'addons', chkSkinKodi, 'colors')
                            xbmcvfs.copy(os.path.join(sourcex, 'defaults.backup'), os.path.join(sourcex, 'defaults.xml'))
                            deb('creating backup colors from non-writeable skin')

                        if chkSkinKodi != 'skin.estuary' or chkSkinKodi != 'skin.estouchy':
                            if check == 0:
                                source = os.path.join(self.kodiSkinPath, 'colors', 'defaults.xml')
                                destination = os.path.join(self.kodiPath, 'addons', chkSkinKodi, 'colors', 'defaults.backup')
                                xbmcvfs.copy(source, destination)
                                deb('creating backup colors')

                        
                        source = os.path.join(self.kodiPath, 'addons', chkSkinKodi, 'colors')
                        xbmcvfs.copy(os.path.join(source, 'defaults.backup'), os.path.join(source, 'defaults.xml'))
                        deb('replacing colors with backup')

                        # Colors
                        skin = xbmc.getInfoLabel('$INFO[Skin.CurrentColourTheme]')
                        if skin == 'SKINDEFAULT':
                            skin = 'defaults'
                        
                        f1 = xbmcvfs.File(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, 'colors', 'defaults.xml'))
                        f1_content = f1.read()
                        f1_content = re.sub('</colors>', '', f1_content).strip()
                        f1.close()

                        f2 = xbmcvfs.File('special://skin/colors/' + skin + '.xml')
                        f2_content = f2.read()
                        try:
                            f2_content = re.sub('<.*encoding=".*>', '', f2_content).strip()
                        except:
                            None

                        f2_content = re.sub('<colors>', '', f2_content)
                        f2.close()

                        f3 = xbmcvfs.File('special://skin/colors/' + skin + '.xml', 'w')
                        f3.write(str(f1_content) + str(f2_content))
                        f3.close()

                        lines_seen = set()
                        for line in f3, 'w':
                            if line not in lines_seen:
                                f3.write(str(line))
                                lines_seen.add(line)
                                f3.close()

                        xbmcgui.Dialog().ok(strings(70100), strings(70102))
                        xbmc.executebuiltin("Quit")
                        exit()
                    else:
                        xbmcgui.Dialog().ok(strings(70105), strings(70103))
                        exit()

                elif res == 1:
                    if addonSkin in estuary:
                        addonSkin = 'skin.estuary'
                    elif addonSkin in confluence:
                        addonSkin = 'skin.confluence'

                    xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Settings.SetSettingValue","id":1,"params":{"setting":"lookandfeel.skin","value":"' + addonSkin + '"}}')
                    xbmc.executebuiltin('SendClick(11)')
                    xbmc.sleep(500)

                    currentSkinNew = xbmc.getSkinDir()
                    if addonSkin != currentSkinNew:
                        xbmcgui.Dialog().ok(strings(70100), strings(70107).format(str(addonSkin)))
                        #xbmc.executebuiltin("Quit")
                        exit()


    def loadSettings(self):
        # Cache textures used to redraw EPG
        self.moviesTexture = "default.png"
        self.seriesTexture = "default.png"
        self.informationTexture = "default.png"
        self.entertainmentTexture = "default.png"
        self.documentsTexture = "default.png"
        self.kidsTexture = "default.png"
        self.sportsTexture = "default.png"
        self.interactiveTexture = "default.png"
        self.backgroundTexture = "default.png"

        skin = xbmc.getInfoLabel('$INFO[Skin.CurrentColourTheme]')
        if skin == 'SKINDEFAULT':
            skin = 'defaults'

        focusButton = 'focus/' + skin + '.png'

        focusPath = xbmcvfs.exists(os.path.join(Skin.getSkinPath(), 'media', 'focus', skin + '.png'))

        if ADDON.getSetting('color_focus') != '':
            if focusPath and ADDON.getSetting('color_focus') == '0':
                self.focusTexture = focusButton
            else:
                self.focusTexture = focus_formatting(ADDON.getSetting('color_focus'))
        else:
            ADDON.setSetting('color_focus', '0')

        if ADDON.getSetting('color_movies') != '':
            self.moviesTexture = category_formatting(ADDON.getSetting('color_movies'))
        else:
            ADDON.setSetting('color_movies', '0')

        if ADDON.getSetting('color_series') != '':
            self.seriesTexture = category_formatting(ADDON.getSetting('color_series'))
        else:
            ADDON.setSetting('color_series', '1')

        if ADDON.getSetting('color_information') != '':
            self.informationTexture = category_formatting(ADDON.getSetting('color_information'))
        else:
            ADDON.setSetting('color_information', '2')

        if ADDON.getSetting('color_entertainment') != '':
            self.entertainmentTexture = category_formatting(ADDON.getSetting('color_entertainment'))
        else:
            ADDON.setSetting('color_entertainment', '3')

        if ADDON.getSetting('color_documents') != '':
            self.documentsTexture = category_formatting(ADDON.getSetting('color_documents'))
        else:
            ADDON.setSetting('color_documents', '4')

        if ADDON.getSetting('color_kids') != '':
            self.kidsTexture = category_formatting(ADDON.getSetting('color_kids'))
        else:
            ADDON.setSetting('color_kids', '5')

        if ADDON.getSetting('color_sports') != '':
            self.sportsTexture = category_formatting(ADDON.getSetting('color_sports'))
        else:
            ADDON.setSetting('color_sports', '6')

        if ADDON.getSetting('color_interactive') != '':
            self.interactiveTexture = category_formatting(ADDON.getSetting('color_interactive'))
        else:
            ADDON.setSetting('color_interactive', '7')

        if ADDON.getSetting('color_background') != '':
            self.backgroundTexture = background_formatting(ADDON.getSetting('color_background'))
        else:
            ADDON.setSetting('color_background', '0')

    def createOSD(self, program, urlList):
        try:
            if self.osd:
                try:
                    self.osd.closeOSD()
                except:
                    pass

            osd = Pla(program, self.database, urlList, self.archiveService, self.archivePlaylist, self)
                
            self.osd = osd
            osd.doModal()
            osd.close()
            del osd
        except:
            deb('createOSD exception: {}'.format(getExceptionString()))

    def getCategories(self):
        categories = None
        try:
            for serviceName in list(playService.SERVICES.keys()):
                categories = playService.SERVICES[serviceName].getCategoriesFromMap()
                break
        except:
            pass

        if categories is None or categories == {}:
            categories = {'Movie': {}, 'Series': {}, 'Information': {}, 'Entertainment': {}, 'Document': {}, 'Kids': {},
                          'Sport': {}, 'Interactive Entertainment': {}}
        # deb('Categories: {}'.format(str(categories)))
        return categories

    def playerstate(self):
        vp = VideoPlayerStateChange()
        vp.setPlaylistPositionFile(self.recordedFilesPlaylistPositions)
        vp.playerStateChanged += self.onPlayerStateChanged
        while not self.isClosing:
            xbmc.sleep(500)
        vp.close()
        return

    def onPlayerStateChanged(self, pstate):
        deb("########### onPlayerStateChanged {} {}".format(pstate, ADDON.getSetting('info_osd')))
        if self.isClosing:
            return

        if (pstate == "Stopped" or pstate == "Ended" or pstate == "PlayBackError"):
            if self.playService.isWorking() or xbmc.Player().isPlaying():
                while self.playService.isWorking() == True and not self.isClosing:
                    time.sleep(0.1)
                if self.isClosing:
                    return
                if xbmc.Player().isPlaying():
                    debug('onPlayerStateChanged - was able to recover playback - dont show EPG!')
                    return

            self._showEPG()

            if pstate == "Ended" and self.playingRecordedProgram and self.recordService.isProgramRecordScheduled(self.program) == False:
                time.sleep(0.1)
                if xbmc.Player().isPlaying() == False:
                    deleteFiles = False
                    if ADDON.getSetting('ask_to_delete_watched') == '1':
                        deleteFiles = xbmcgui.Dialog().yesno(strings(69026), '{}?'.format(strings(69027)))
                    elif ADDON.getSetting('ask_to_delete_watched') == '2':
                        deleteFiles = True
                    if deleteFiles == True:
                        self.recordService.removeRecordedProgram(self.program)
        else:
            self._hideEpg()

    def getControl(self, controlId):
        # debug('getControl')
        try:
            return super(mTVGuide, self).getControl(controlId)
        except:
            if controlId in self.ignoreMissingControlIds:
                return None
            if not self.isClosing:
                self.close()
        return None

    def deleteFiles(self):
        try:
            if sys.version_info[0] > 2:
                f = os.path.join(self.profilePath, 'catchup.list')
            else:
                f = os.path.join(self.profilePath, 'catchup.list').decode('utf-8')
            os.remove(f)
        except:
            None

        try:
            if sys.version_info[0] > 2:
                f = os.path.join(self.profilePath, 'playlist_ts.list')
            else:
                f = os.path.join(self.profilePath, 'playlist_ts.list').decode('utf-8')
            os.remove(f)
        except:
            None

        try:
            if sys.version_info[0] > 2:
                f = os.path.join(self.profilePath, 'cmore_ts.list')
            else:
                f = os.path.join(self.profilePath, 'cmore_ts.list').decode('utf-8')
            os.remove(f)
        except:
            None
            
        try:
            if sys.version_info[0] > 2:
                f = os.path.join(self.profilePath, 'cpgo_ts.list')
            else:
                f = os.path.join(self.profilePath, 'cpgo_ts.list').decode('utf-8')
            os.remove(f)
        except:
            None

        try:
            if sys.version_info[0] > 2:
                f = os.path.join(self.profilePath, 'ipla_ts.list')
            else:
                f = os.path.join(self.profilePath, 'ipla_ts.list').decode('utf-8')
            os.remove(f)
        except:
            None

        #try:
            #if sys.version_info[0] > 2:
                #f = os.path.join(self.profilePath, 'playerpl_ts.list')
            #else:
                #f = os.path.join(self.profilePath, 'playerpl_ts.list').decode('utf-8')
            #os.remove(f)
        #except:
            #None

        try:
            if sys.version_info[0] > 2:
                f = os.path.join(self.profilePath, 'teliaplay_ts.list')
            else:
                f = os.path.join(self.profilePath, 'teliaplay_ts.list').decode('utf-8')
            os.remove(f)
        except:
            None
            
        try:
            if sys.version_info[0] > 2:
                f = os.path.join(self.profilePath, 'stream_url.list')
            else:
                f = os.path.join(self.profilePath, 'stream_url.list').decode('utf-8')
            os.remove(f)
        except:
            None
            
        try:
            if ADDON.getSetting('skin_fontpack') == 'true':
                xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Settings.SetSettingValue","id":1,"params":{"setting":"lookandfeel.font","value":"Default"}}')
        except:
            None

    def close(self, background=''):
        deb('close')
        if not self.isClosing:
            if not background:
                if self.recordService.isRecordOngoing():
                    ret = xbmcgui.Dialog().yesno(strings(69000), '{}'.format(strings(69011)))
                    if ret == False:
                        return
                elif self.recordService.isRecordScheduled():
                    ret = xbmcgui.Dialog().yesno(strings(69000), '{}'.format(strings(69015)))
                    if ret == False:
                        return

                elif self.recordService.isDownloadOngoing():
                    ret = xbmcgui.Dialog().yesno(strings(69056), '{}'.format(strings(69058)))
                    if ret == False:
                        return
            
            self.isClosing = True
            strings2.M_TVGUIDE_CLOSING = True
            if self.refreshStreamsTimer:
                self.refreshStreamsTimer.cancel()
            if self.timer and self.timer.is_alive():
                self.timer.cancel()

            try:
                if self.updateEpgTimer:
                    self.updateEpgTimer.stop()
            except:
                pass

            if self.osd:
                try:
                    self.osd.closeOSD()
                except:
                    pass
            if not background:
                self.playService.close()
                self.recordService.close()
            else:
                while xbmc.Monitor().abortRequested():
                    self.playService.close()
                    self.recordService.close()

            if self.notification:
                self.notification.close()
            if self.updateTimebarTimer:
                self.updateTimebarTimer.cancel()
            self._clearEpg()
            if self.rssFeed:
                self.rssFeed.close()
            if self.database:
                self.deleteFiles()
                self.database.close(super(mTVGuide, self).close)
            else:
                super(mTVGuide, self).close()

    def onInit(self):
        deb('onInit')

        if self.initialized:
            # onInit(..) is invoked again by XBMC after a video addon exits after being invoked by XBMC.RunPlugin(..)
            deb("[{}] TVGuide.onInit(..) invoked, but we're already initialized!".format(ADDON_ID))
            self.onSourceUpdate = True
            self.redrawagain = True
            self._showEPG()
            return

        self.initialized = True
        self._hideControl(self.C_MAIN_MOUSEPANEL_CONTROLS)
        self._showControl(self.C_MAIN_LOADING)
        self._hideControl(self.C_MAIN_LOADING_BACKGROUND)
        self.setControlLabel(self.C_MAIN_LOADING_TIME_LEFT, strings(BACKGROUND_UPDATE_IN_PROGRESS))
        self.setFocusId(self.C_MAIN_LOADING_CANCEL)

        time.sleep(2)
        self._showControl(self.C_MAIN_EPG)
        

        control = self.getControl(self.C_MAIN_EPG_VIEW_MARKER)
        if control:
            left, top = control.getPosition()

            self.focusPoint.x = left
            self.focusPoint.y = top
            self.epgView.left = left
            self.epgView.top = top
            self.epgView.right = left + control.getWidth()
            self.epgView.bottom = top + control.getHeight()
            self.epgView.width = control.getWidth()
            self.epgView.cellHeight = control.getHeight() // CHANNELS_PER_PAGE

        try:
            self.database = src.Database()
        except src.SourceNotConfiguredException:
            self.onSourceNotConfigured()
            self.close()
            return

        self.database.initialize(self.onSourceInitialized, self.isSourceInitializationCancelled)

        self.updateTimebar()

        self.interval = 300
        self.updateEpgTimer = epgTimer(self.interval, self.updateEpg)

    def updateEpg(self):
        epgSize = ADDON.getSetting('epg_size')
        epgDbSize = ADDON.getSetting('epg_dbsize')
        if epgSize != epgDbSize:
            self.onRedrawEPG(self.channelIdx, self.viewStartDate, self._getCurrentProgramFocus)

        self.updateEpgTimer.stop()
        time.sleep(self.interval)
        self.updateEpgTimer.start()

        
    def getStreamsCid(self):
        streamsList = list()
        CMoreStreamsList = list()
        CPGOStreamsList = list()
        IplaStreamsList = list()
        NCGOStreamsList = list()
        #PlayerPLStreamsList = list()
        TeliaPlayStreamsList = list()

        streams = self.database.getAllStreamUrlList() 
        #deb('getStreams: {}'.format(streams))


        # Catchup days
        catchupList = list()

        p = re.compile('.*_TS_(.*?)(_.*)?$', re.DOTALL)
        c = re.compile('^(.*?),.*', re.DOTALL)

        for item in streams:
            if p.match(item):
                days = p.search(item).group(1)
                channel = c.search(item).group(1)
                catchupList.append(channel.upper() + '=' + days)

        file_name = os.path.join(self.profilePath, 'catchup.list')
        with open(file_name, 'w+') as f:
            if sys.version_info[0] > 2:
                f.write('\n'.join(sorted(catchupList)))
            else:
                f.write(bytearray('\n'.join(sorted(catchupList)), 'utf-8'))
        
        # Playlist
        for item in streams:
            try:
                item = re.findall('^(.+?),.*CID=\d+_TS.*$', str(item))
            except:
                item = re.findall('^(.+?),.*CID=\d+_TS.*$', str(item.encode('ascii', 'ignore').decode('ascii')))
            
            if len(item) > 0:
                streamsList.append(item[0].upper())

        if streamsList:
            file_name = os.path.join(self.profilePath, 'playlist_ts.list')
            with open(file_name, 'w+') as f:
                if sys.version_info[0] > 2:
                    f.write('\n'.join(streamsList))
                else:
                    f.write(bytearray('\n'.join(streamsList), 'utf-8'))

        # C More
        for item in streams:
            try:
                item = re.findall('^(.+?), SERVICE=C MORE&CID=\d+$', str(item))
            except:
                item = re.findall('^(.+?), SERVICE=C MORE&CID=\d+$', str(item.encode('ascii', 'ignore').decode('ascii')))

            if len(item) > 0:
                CMoreStreamsList.append(item[0].upper())

        if CMoreStreamsList:
            file_name = os.path.join(self.profilePath, 'cmore_ts.list')
            with open(file_name, 'w+') as f:
                if sys.version_info[0] > 2:
                    f.write('\n'.join(CMoreStreamsList))
                else:
                    f.write(bytearray('\n'.join(CMoreStreamsList), 'utf-8'))

        # Cyfrowy Polsat GO
        for item in streams:
            try:
                item = re.findall('^(.+?), SERVICE=CYFROWY POLSAT GO&CID=\d+$', str(item))
            except:
                item = re.findall('^(.+?), SERVICE=CYFROWY POLSAT GO&CID=\d+$', str(item.encode('ascii', 'ignore').decode('ascii')))

            if len(item) > 0:
                CPGOStreamsList.append(item[0].upper())

        if CPGOStreamsList:
            file_name = os.path.join(self.profilePath, 'cpgo_ts.list')
            with open(file_name, 'w+') as f:
                if sys.version_info[0] > 2:
                    f.write('\n'.join(CPGOStreamsList))
                else:
                    f.write(bytearray('\n'.join(CPGOStreamsList), 'utf-8'))

        # Ipla
        for item in streams:
            try:
                item = re.findall('^(.+?), SERVICE=IPLA&CID=\d+$', str(item))
            except:
                item = re.findall('^(.+?), SERVICE=IPLA&CID=\d+$', str(item.encode('ascii', 'ignore').decode('ascii')))

            if len(item) > 0:
                IplaStreamsList.append(item[0].upper())

        if IplaStreamsList:
            file_name = os.path.join(self.profilePath, 'ipla_ts.list')
            with open(file_name, 'w+') as f:
                if sys.version_info[0] > 2:
                    f.write('\n'.join(IplaStreamsList))
                else:
                    f.write(bytearray('\n'.join(IplaStreamsList), 'utf-8'))

        # PlayerPL
        #for item in streams:
            #try:
                #item = re.findall('^(.+?), SERVICE=PLAYERPL&CID=\d+:KANAL$', str(item))
            #except:
                #item = re.findall('^(.+?), SERVICE=PLAYERPL&CID=\d+:KANAL$', str(item.encode('ascii', 'ignore').decode('ascii')))

            #if len(item) > 0:
                #PlayerPLStreamsList.append(item[0].upper())

        #if PlayerPLStreamsList:
            #file_name = os.path.join(self.profilePath, 'playerpl_ts.list')
            #with open(file_name, 'w+') as f:
                #if sys.version_info[0] > 2:
                    #f.write('\n'.join(PlayerPLStreamsList))
                #else:
                    #f.write(bytearray('\n'.join(PlayerPLStreamsList), 'utf-8'))

        # Telia Play
        for item in streams:
            try:
                item = re.findall('^(.+?), SERVICE=TELIA PLAY&CID=\d+$', str(item))
            except:
                item = re.findall('^(.+?), SERVICE=TELIA PLAY&CID=\d+$', str(item.encode('ascii', 'ignore').decode('ascii')))

            if len(item) > 0:
                TeliaPlayStreamsList.append(item[0].upper())

        if TeliaPlayStreamsList:
            file_name = os.path.join(self.profilePath, 'teliaplay_ts.list')
            with open(file_name, 'w+') as f:
                if sys.version_info[0] > 2:
                    f.write('\n'.join(TeliaPlayStreamsList))
                else:
                    f.write(bytearray('\n'.join(TeliaPlayStreamsList), 'utf-8'))

        # nc+ GO
        for item in streams:
            try:
                item = re.findall('^(.+?), SERVICE=NC+ GO&CID=\d+$', str(item))
            except:
                item = re.findall('^(.+?), SERVICE=NC+ GO&CID=\d+$', str(item.encode('ascii', 'ignore').decode('ascii')))

            if len(item) > 0:
                NCGOStreamsList.append(item[0].upper())

        if NCGOStreamsList:
            file_name = os.path.join(self.profilePath, 'ncgo_ts.list')
            with open(file_name, 'w+') as f:
                if sys.version_info[0] > 2:
                    f.write('\n'.join(NCGOStreamsList))
                else:
                    f.write(bytearray('\n'.join(NCGOStreamsList), 'utf-8'))

        return streamsList

    def catchupEPG(self, program, cellWidth):
        archive = ''

        archivePlaylist = self.getPlaylist() + self.getTeliaPlay()
        archiveList = self.getCmore() + self.getPolsatGo() + self.getIpla()# + self.getPlayerPL()

        catchupList = list()

        catchupList = self.getCatchupDays()

        catchupDays = None

        if program.channel.title.upper() in catchupList:
            catchupDays = re.findall('.*=(.*?)$', catchupList)

        if catchupDays:
            self.catchupDays = catchupDays[0]
        else:
            self.catchupDays = ADDON.getSetting('archive_reverse_days')

        if ADDON.getSetting('archive_reverse_auto') == '0' and self.catchupDays != '' or self.catchupDays !='0':
            try:
                reverseTime = datetime.datetime.now() - datetime.timedelta(hours = int(self.catchupDays)) * 24 - datetime.timedelta(minutes = 5)
            except:
                reverseTime = datetime.datetime.now() - datetime.timedelta(hours = int(1)) * 24 - datetime.timedelta(minutes = 5)
        else:
            try:
                reverseTime = datetime.datetime.now() - datetime.timedelta(hours = int(ADDON.getSetting('archive_manual_days'))) * 24 - datetime.timedelta(minutes = 5)
            except:
                reverseTime = datetime.datetime.now() - datetime.timedelta(hours = int(1)) * 24 - datetime.timedelta(minutes = 5)

        reverseArchiveService = datetime.datetime.now() - datetime.timedelta(hours = int(3)) - datetime.timedelta(minutes = 5)

        addonSkin = ADDON.getSetting('Skin')

        if ADDON.getSetting('archive_support') == 'true': 
            if ADDON.getSetting('archive_finished_program') == 'true': 
                if program.channel.title.upper() in archivePlaylist and program.endDate < datetime.datetime.now():
                    #Download
                    if cellWidth < 35:
                        archive  = ''
                    else:
                        if skin_catchup_size == '1':
                            archive = '[UPPERCASE][COLOR FF01cdfe][B]• [/B][/COLOR][/UPPERCASE]'
                        else:
                            archive = '[UPPERCASE][COLOR FF01cdfe][B]● [/B][/COLOR][/UPPERCASE]'
                
                if program.channel.title.upper() in archivePlaylist:
                    #Catchup
                    if program.endDate < datetime.datetime.now():
                        if program.startDate > reverseTime:
                            if cellWidth < 35:
                                archive  = ''
                            else:
                                if skin_catchup_size == '1':
                                    archive = '[UPPERCASE][COLOR FF0cbe24][B]• [/B][/COLOR][/UPPERCASE]'
                                else:
                                    archive = '[UPPERCASE][COLOR FF0cbe24][B]● [/B][/COLOR][/UPPERCASE]'

                if program.channel.title.upper() in archiveList:
                    #Catchup
                    if program.endDate < datetime.datetime.now():
                        if program.startDate > reverseArchiveService:
                            if cellWidth < 35:
                                archive  = ''
                            else:
                                if skin_catchup_size == '1':
                                    archive = '[UPPERCASE][COLOR FF0cbe24][B]• [/B][/COLOR][/UPPERCASE]'
                                else:
                                    archive = '[UPPERCASE][COLOR FF0cbe24][B]● [/B][/COLOR][/UPPERCASE]'

            else:
                if program.channel.title.upper() in archivePlaylist and program.startDate < datetime.datetime.now():
                    #Download
                    if cellWidth < 35:
                        archive  = ''
                    else:
                        if skin_catchup_size == '1':
                            archive = '[UPPERCASE][COLOR FF01cdfe][B]• [/B][/COLOR][/UPPERCASE]'
                        else:
                            archive = '[UPPERCASE][COLOR FF01cdfe][B]● [/B][/COLOR][/UPPERCASE]'
                
                if program.channel.title.upper() in archivePlaylist:
                    #Catchup
                    if program.startDate < datetime.datetime.now():
                        if program.startDate > reverseTime:
                            if cellWidth < 35:
                                archive  = ''
                            else:
                                if skin_catchup_size == '1':
                                    archive = '[UPPERCASE][COLOR FF0cbe24][B]• [/B][/COLOR][/UPPERCASE]'
                                else:
                                    archive = '[UPPERCASE][COLOR FF0cbe24][B]● [/B][/COLOR][/UPPERCASE]'

                if program.channel.title.upper() in archiveList:
                    #Catchup
                    if program.startDate < datetime.datetime.now():
                        if program.startDate > reverseArchiveService:
                            if cellWidth < 35:
                                archive  = ''
                            else:
                                if skin_catchup_size == '1':
                                    archive = '[UPPERCASE][COLOR FF0cbe24][B]• [/B][/COLOR][/UPPERCASE]'
                                else:
                                    archive = '[UPPERCASE][COLOR FF0cbe24][B]● [/B][/COLOR][/UPPERCASE]'
        else:
            archive = ''


        return archive

    def getChannelListLenght(self):
        channelList = self.database.getChannelList(onlyVisible=True)
        indexList = len(channelList)
        return indexList

    def getChannelNumber(self):
        try:
            channelList = self.database.getChannelList(onlyVisible=True)
            controlInFocus = self.getFocus()
            program = self._getProgramFromControl(controlInFocus)
            index = channelList.index(program.channel) + 1
            return index
        except:
            pass

    def AutoPlayByNumber(self):
        self.viewStartDate = datetime.datetime.today() + datetime.timedelta(
            minutes=int(ADDON.getSetting('timebar_adjust')))
        self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)
        channelList = self.database.getChannelList(onlyVisible=True)
        self.channelIdx = int(ADDON.getSetting('autostart_channel_number')) - 1
        channel = Channel(id='', title='', logo='', streamUrl='', visible='', weight='')
        try:
            program = Program(channel=channelList[self.channelIdx], title='', startDate='', endDate='', description='', productionDate='', director='', actor='', episode='', 
                            imageLarge='', imageSmall='', categoryA='', categoryB='')
        except:
            program = Program(channel=channelList[0], title='', startDate='', endDate='', description='', productionDate='', director='', actor='', episode='',
                            imageLarge='', imageSmall='', categoryA='', categoryB='')
        xbmc.sleep(350)
        self.playChannel(program.channel)

    def AutoPlayLastChannel(self):
        self.viewStartDate = datetime.datetime.today() + datetime.timedelta(
            minutes=int(ADDON.getSetting('timebar_adjust')))
        self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)
        channelList = self.database.getChannelList(onlyVisible=True)
        f = xbmcvfs.File(os.path.join(self.profilePath, 'autoplay.list'), "r")
        lines = f.read()
        self.channelIdx = int(lines.split(',')[0])
        try:
            program = Program(channel=channelList[self.channelIdx], title='', startDate='', endDate='', description='', productionDate='', director='', actor='', episode='',
                              imageLarge='', imageSmall='', categoryA='', categoryB='')
        except:
            program = Program(channel=channelList[0], title='', startDate='', endDate='', description='', productionDate='', director='', actor='', episode='',
                              imageLarge='', imageSmall='', categoryA='', categoryB='')
        xbmc.sleep(350)
        self.playChannel(program.channel)

    def Info(self, program, playChannel2, recordProgram, notification, ExtendedInfo, onRedrawEPG, channelIdx,
             viewStartDate):
        deb('Info')
        self.infoDialog = InfoDialog(program, playChannel2, recordProgram, notification, ExtendedInfo, onRedrawEPG,
                                     channelIdx, viewStartDate)
        self.infoDialog.setChannel(program)
        self.infoDialog.doModal()
        del self.infoDialog
        self.infoDialog = None

    def scriptChkExtendedInfo(self):
        if sys.version_info[0] > 2:
            return xbmc.getCondVisibility('System.AddonIsEnabled({id})'.format(id='script.extendedinfo'))
        else:
            return xbmc.getCondVisibility('System.HasAddon({id})'.format(id='script.extendedinfo'))

    @contextmanager
    def busyDialog(self):
        xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
        try:
            yield
        finally:
            xbmc.executebuiltin('Dialog.Close(busydialognocancel)')

    def ExtendedInfo(self, program):
        check = self.scriptChkExtendedInfo()

        if check == False:
            try:
                res = xbmc.executebuiltin('InstallAddon(script.extendedinfo)')
                if res is None:
                    xbmcgui.Dialog().ok(strings(69062), strings(31021).format('script.extendedinfo')+'.')
            except:
                None
            if res is True:
                xbmcgui.Dialog().ok(strings(57051), strings(30979))
                exit()

        elif check == True:
            title = program.title
            match = re.search('(.*?)\([0-9]{4}\)$', title)
            if match:
                program.title = match.group(1).strip()
                program.title = "Movie"
            if program.title == "Movie":
                selection = 0
            elif program.title == "":
                selection = 1
            else:
                selection = xbmcgui.Dialog().select(strings(30359), [strings(30357), strings(30358)])
                if selection == -1:
                    return

            where = ["movie", "tv"]

            key = '4d7b67222e47d5d8a6176fcacbfe9240'

            if sys.version_info[0] > 2:
                url = 'https://api.themoviedb.org/3/search/{where}?query={query}&api_key={key}&include_adult=false&page=1'.format(where=where[selection], query=title, key=key).encode()
            else:
                url = 'https://api.themoviedb.org/3/search/{where}?query={query}&api_key={key}&include_adult=false&page=1'.format(where=where[selection], query=title, key=key)

            r = requests.get(url)
            data = json.loads(r.content)
            results = data.get('results')
            id = ''
            with self.busyDialog():
                if results:
                    if len(results) > 0:
                        names = ["{} ({})".format(x.get('name') or x.get('title'), x.get('first_air_date') or x.get('release_date'))
                                 for x in results]
                        what = xbmcgui.Dialog().select(title, names)
                        if what > -1:
                            id = results[what].get('id')
                            ttype = results[what].get('media_ttype')
                            if ttype not in ["movie", "tv"]:
                                if selection == 0:
                                    ttype = "movie"
                                else:
                                    ttype = "tv"
                            if ttype == 'movie':
                                xbmc.executebuiltin('RunScript(script.extendedinfo,info=extendedinfo,name={title},id={id})'.format(title=title.encode('unicode_escape'), id=id))
                            elif ttype == 'tv':
                                xbmc.executebuiltin('RunScript(script.extendedinfo,info=extendedtvinfo,name={title},id={id})'.format(title=program.title.encode('unicode_escape'), id=id))
                            else:
                                xbmcgui.Dialog().notification(strings(30353), strings(30361).format(title))

                    else:
                        if selection == 0:
                            xbmcgui.Dialog().notification(strings(30353), strings(30362).format(title))
                            search = xbmcgui.Dialog().input(strings(30322), program.title)
                            if search:
                                xbmc.executebuiltin('RunScript(script.extendedinfo,info=extendedinfo,name={title})'.format(title=search.encode('unicode_escape')))
                            else:
                                return
                        elif selection == 1:
                            xbmcgui.Dialog().notification(strings(30353), strings(30363).format(title))
                            search = xbmcgui.Dialog().input(strings(30322), title)
                            if search:
                                xbmc.executebuiltin('RunScript(script.extendedinfo,info=extendedtvinfo,name={title})'.format(title=search.encode('unicode_escape')))
                            else:
                                return
                        else:
                            xbmcgui.Dialog().notification(strings(30353), strings(30361).format(title))
                else:
                    if selection == 0:
                        xbmcgui.Dialog().notification(strings(30353), strings(30362).format(title))
                        search = xbmcgui.Dialog().input(strings(30322), program.title)
                        if search:
                            xbmc.executebuiltin('RunScript(script.extendedinfo,info=extendedinfo,name={title})'.format(title=search.encode('unicode_escape')))
                        else:
                            return
                    elif selection == 1:
                        xbmcgui.Dialog().notification(strings(30353), strings(30363).format(title))
                        search = xbmcgui.Dialog().input(strings(30322), title)
                        if search:
                            xbmc.executebuiltin('RunScript(script.extendedinfo,info=extendedtvinfo,name={title})'.format(title=search.encode('unicode_escape')))
                        else:
                            return
                    else:
                        xbmcgui.Dialog().notification(strings(30353), strings(30361).format(title))

    def playShortcut(self):
        self.channel_number_input = False
        self.viewStartDate = datetime.datetime.today() + datetime.timedelta(minutes=int(ADDON.getSetting('timebar_adjust')))
        self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)
        channelList = self.database.getChannelList(onlyVisible=True)
        if ADDON.getSetting('channel_shortcut') == 'false':
            for i in range(len(channelList)):
                if self.channel_number == channelList[i].id:
                    self.channelIdx = i
                    break
        else:
            self.channelIdx = (int(self.channel_number) - 1)
            self.channel_number = ""
            self.getControl(9999).setLabel(self.channel_number)

        behaviour = int(ADDON.getSetting('channel_shortcut_behaviour'))
        if (self.mode != MODE_EPG) and (behaviour > 0):
            program = Program(channel=channelList[self.channelIdx], title='', startDate=None, endDate=None, description='', productionDate='', director='', actor='', episode='', categoryA='', categoryB='')
            self.playChannel2(program)
        elif (behaviour == 1) or (behaviour == 1 and self.mode != MODE_EPG):
            self.focusPoint.y = self.epgView.top
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)
            xbmc.executebuiltin('Action(Select)')
        else:
            self.focusPoint.y = self.epgView.top
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)

    def onAction(self, action):
        if not self.isClosing:
            self.lastKeystroke = datetime.datetime.now()
            if self.mode == MODE_TV:
                self.onActionTVMode(action)
            elif self.mode == MODE_EPG:
                self.onActionEPGMode(action)

        if (ADDON.getSetting('channel_shortcut') != 'false'):
            digit = None
            if not self.channel_number_input:
                code = action.getButtonCode() - 61488
                action_code = action.getId() - 58
                action_code_2 = action.getId() - 140
                if (code >= 0 and code <= 9) or (action_code >= 0 and action_code <= 9) or (action_code_2 >= 0 and action_code_2 <= 9):
                    digit = None
                    if (code >= 0 and code <= 9):
                        digit = code
                    elif (action_code_2 >= 0 and action_code_2 <= 9):
                        digit = action_code_2
                    else:
                        digit = action_code
                    self.channel_number_input = True
                    self.channel_number = str(digit)
                    self.getControl(9999).setLabel(self.channel_number)
                    if self.timer and self.timer.is_alive():
                        self.timer.cancel()
                    self.timer = threading.Timer(2, self.playShortcut)
                    self.timer.start()

            if self.channel_number_input:
                if digit == None:
                    code = action.getButtonCode() - 61488
                    action_code = action.getId() - 58
                    action_code_2 = action.getId() - 140
                    if (code >= 0 and code <= 9) or (action_code >= 0 and action_code <= 9) or (action_code_2 >= 0 and action_code_2 <= 9):
                        digit = None
                        if (code >= 0 and code <= 9):
                            digit = code
                        elif (action_code_2 >= 0 and action_code_2 <= 9):
                            digit = action_code_2
                        else:
                            digit = action_code
                    if digit != None:
                        self.channel_number = "{}{}".format(self.channel_number.strip('_'), digit)
                        self.getControl(9999).setLabel(self.channel_number)
                        if self.timer and self.timer.is_alive():
                            self.timer.cancel()
                        self.timer = threading.Timer(2, self.playShortcut)
                        self.timer.start()

        if (ADDON.getSetting('channel_shortcut') == 'false'):
            digit = None
            if not self.channel_number_input:
                code = action.getButtonCode() - 61488
                action_code = action.getId() - 58
                action_code_2 = action.getId() - 140
                if (code >= 0 and code <= 9) or (action_code >= 0 and action_code <= 9) or (action_code_2 >= 0 and action_code_2 <= 9):
                    digit = None
                    if (code >= 0 and code <= 9):
                        digit = code
                    elif (action_code_2 >= 0 and action_code_2 <= 9):
                        digit = action_code_2
                    else:
                        digit = action_code
                    xbmcgui.Dialog().notification(strings(30353), strings(30354))
                    return

            if self.channel_number_input:
                if digit == None:
                    code = action.getButtonCode() - 61488
                    action_code = action.getId() - 58
                    action_code_2 = action.getId() - 140
                    if (code >= 0 and code <= 9) or (action_code >= 0 and action_code <= 9) or (action_code_2 >= 0 and action_code_2 <= 9):
                        digit = None
                        if (code >= 0 and code <= 9):
                            digit = code
                        elif (action_code_2 >= 0 and action_code_2 <= 9):
                            digit = action_code_2
                        else:
                            digit = action_code
                    if digit != None:
                        xbmcgui.Dialog().notification(strings(30353), strings(30354))
                        return

    def onActionTVMode(self, action):
        debug('onActionTVMode actId {}, buttonCode {}'.format(action.getId(), action.getButtonCode()))
        if action.getId() == ACTION_PAGE_UP:
            self._channelUp()

        elif action.getId() == ACTION_PAGE_DOWN:
            self._channelDown()

        elif action.getId() == KEY_CONTEXT_MENU or action.getButtonCode() == KEY_CONTEXT:
            if not self.playingRecordedProgram:
                self.playService.playNextStream()

        elif action.getId() in [ACTION_PARENT_DIR, KEY_NAV_BACK, ACTION_PREVIOUS_MENU]:
            self.onRedrawEPG(self.channelIdx, self.viewStartDate, self._getCurrentProgramFocus)

        elif action.getId() == ACTION_STOP or (action.getButtonCode() == KEY_STOP and KEY_STOP != 0):
            self.playService.stopPlayback()

    def onActionEPGMode(self, action):
        debug('onActionEPGMode keyId {}, buttonCode {}'.format(action.getId(), action.getButtonCode()))
        if ADDON.getSetting('background_services') == 'true':
            background = True
        else:
            background = False

        if action.getId() in [ACTION_PARENT_DIR, KEY_NAV_BACK, ACTION_PREVIOUS_MENU]:
            if not background:
                if xbmc.Player().isPlaying() or self.playService.isWorking():
                    self.playService.stopPlayback()
                    
            if action.getButtonCode() != 0 or action.getId() == ACTION_SELECT_ITEM:
                if ADDON.getSetting('exit') == '0':
                    # Ask to close
                    ret = xbmcgui.Dialog().yesno(strings(30963), '{}?'.format(strings(30981)))
                    if ret == False:
                        return
                    elif ret == True:
                        self.close(background=background)
                else:
                    # Close by two returns
                    if (datetime.datetime.now() - self.lastCloseKeystroke).seconds < 3:
                        self.close(background=background)
                    else:
                        self.lastCloseKeystroke = datetime.datetime.now()
                        xbmcgui.Dialog().notification(strings(30963), strings(30964), time=3000, sound=False)

        elif action.getId() == ACTION_MOUSE_MOVE:
            if ADDON.getSetting('touch_panel') == 'true':
                self._showControl(self.C_MAIN_MOUSEPANEL_CONTROLS)
            return

        if not self.dontBlockOnAction and self.blockInputDueToRedrawing:  # Workaround for occasional gui freeze caused by muliple buttons pressed
            debug('Ignoring action')
            return

        elif action.getId() == ACTION_SHOW_INFO or (action.getButtonCode() == KEY_INFO and KEY_INFO != 0) or (
                action.getId() == KEY_INFO and KEY_INFO != 0):
            if not ini_info:
                return
            try:
                controlInFocus = self.getFocus()
                program = self._getProgramFromControl(controlInFocus)
                if program is not None:
                    d = xbmcgui.Dialog()
                    list = d.select(strings(31009), [strings(58000), strings(30356)])

                    if list == 0:
                        self.Info(program, self.playChannel2, self.recordProgram, self.notification, self.ExtendedInfo,
                                  self.onRedrawEPG, self.channelIdx, self.viewStartDate)
                    elif list == 1:
                        self.ExtendedInfo(program)
            except:
                pass
            return

        elif action.getId() == KEY_CONTEXT_MENU or action.getButtonCode() == KEY_CONTEXT or action.getId() == ACTION_MOUSE_RIGHT_CLICK:

            if self.currentChannel is None:
                chann, prog, idx = self.getLastPlayingChannel()
                self.currentChannel = chann

            if xbmc.Player().isPlaying():
                if ADDON.getSetting('start_video_minimalized') == 'false' or self.playingRecordedProgram or self.currentChannel is None:
                    xbmc.executebuiltin("Action(FullScreen)")
                self._hideEpg()
                if ADDON.getSetting('info_osd') == "true" and not self.playingRecordedProgram and self.currentChannel is not None:
                    if ADDON.getSetting('archive_support') == "true" and (self.archiveService != '' or self.archivePlaylist != ''):
                        self.createOSD(self.program, '')
                    else:
                        self.createOSD(None, None)
                return

        elif action.getId() == ACTION_STOP or (action.getButtonCode() == KEY_STOP and KEY_STOP != 0):
            self.playService.stopPlayback()

        controlInFocus = None
        currentFocus = self.focusPoint
        try:
            controlInFocus = self.getFocus()
            if controlInFocus.getId() in [elem.control.getId() for elem in self.controlAndProgramList]:
                (left, top) = controlInFocus.getPosition()
                currentFocus = Point()
                currentFocus.x = left + (controlInFocus.getWidth() // 2)
                currentFocus.y = top + (controlInFocus.getHeight() // 2)

        except Exception:
            control = self._findControlAt(self.focusPoint)
            if control is None and len(self.controlAndProgramList) > 0:
                control = self.controlAndProgramList[0].control
            if control is not None:
                self.setFocus(control)
                if action.getId() == ACTION_MOUSE_WHEEL_UP:
                    pass
                elif action.getId() == ACTION_MOUSE_WHEEL_DOWN:
                    pass
                else:
                    return

        if action.getId() == ACTION_LEFT and self.getFocusId() != 7900:
            self._left(currentFocus)
        elif action.getId() == ACTION_RIGHT and self.getFocusId() != 7900:
            self._right(currentFocus)
        elif action.getId() == ACTION_UP:
            if self.getFocusId() == 7900:
                self.focusPoint.y = self.epgView.bottom
                self.onRedrawEPG(0 - CHANNELS_PER_PAGE, self.viewStartDate,
                             focusFunction=self._findControlAbove)
            else:
                self._up(currentFocus)
        elif action.getId() == ACTION_DOWN:
            if self.getFocusId() == 7900:
                self.focusPoint.y = self.epgView.top
                self.onRedrawEPG(0, self.viewStartDate,
                             focusFunction=self._findControlAbove)
            else:
                self._down(currentFocus)
        elif action.getId() == ACTION_NEXT_ITEM:
            self._nextDay()
        elif action.getId() == ACTION_PREV_ITEM:
            self._previousDay()
        elif action.getId() == ACTION_PAGE_UP:
            self._moveUp(CHANNELS_PER_PAGE)
        elif action.getId() == ACTION_PAGE_DOWN:
            self._moveDown(CHANNELS_PER_PAGE)
        elif action.getId() == ACTION_MOUSE_WHEEL_UP and self.getFocusId() != 7900:
            self._moveUp(scrollEvent=True)
        elif action.getId() == ACTION_MOUSE_WHEEL_DOWN and self.getFocusId() != 7900:
            self._moveDown(scrollEvent=True)
        elif action.getId() == KEY_HOME or (action.getButtonCode() == KEY_HOME2 and KEY_HOME2 != 0) or (action.getId() == KEY_HOME2 and KEY_HOME2 != 0):
            self.viewStartDate = datetime.datetime.today() + datetime.timedelta(minutes=int(ADDON.getSetting('timebar_adjust')))
            self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)
            self.onRedrawEPG(0, self.viewStartDate)
        elif action.getId() == KEY_END:
            self.viewStartDate = datetime.datetime.today() + datetime.timedelta(minutes=int(ADDON.getSetting('timebar_adjust')))
            self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)
            self.onRedrawEPG(-1, self.viewStartDate)
        elif (action.getId() in [KEY_CONTEXT_MENU, ACTION_MOUSE_RIGHT_CLICK] or action.getButtonCode() in [KEY_CONTEXT]) and controlInFocus is not None:
            program = self._getProgramFromControl(controlInFocus)
            if program is not None:
                self._showContextMenu(program)
                return
        elif action.getButtonCode() == KEY_RECORD:
            program = self._getProgramFromControl(controlInFocus)
            self.recordProgram(program)
            return

        elif action.getButtonCode() == KEY_LIST:
            program = self._getProgramFromControl(controlInFocus)
            d = xbmcgui.Dialog()
            list = d.select(strings(30309), [strings(30310), strings(30311), strings(30312), strings(30336), strings(30337), strings(30315)])

            if list < 0:
                self.onRedrawEPG(self.channelIdx, self.viewStartDate)
            if list == 0:
                index = self.database.getCurrentChannelIdx(program.channel)
                programList = self.database.getChannelListing(program.channel)
                self.showListing(program.channel)
            elif list == 1:
                index = self.database.getCurrentChannelIdx(program.channel)
                programList = self.database.getChannelListing(program.channel)
                self.showNow(program.channel)
            elif list == 2:
                index = self.database.getCurrentChannelIdx(program.channel)
                programList = self.database.getChannelListing(program.channel)
                self.showNext(program.channel)
            elif list == 3:
                self.showFullReminders(program.channel)
            elif list == 4:
                self.showFullRecordings(program.channel)
            elif list == 5:
                self.programSearchSelect(program.channel)
            return

        elif action.getId() == ACTION_MOUSE_MIDDLE_CLICK:
            program = self._getProgramFromControl(controlInFocus)
            if ADDON.getSetting('channel_shortcut') == 'false':
                xbmcgui.Dialog().notification(strings(30353), strings(30354))
            else:
                if ADDON.getSetting('channel_shortcut') == 'true':
                    d = xbmcgui.Dialog()
                    number = d.input(strings(30346), type=xbmcgui.INPUT_NUMERIC)
                    if number:
                        self.channel_number = number
                        if self.timer and self.timer.is_alive():
                            self.timer.cancel()
                        self.playShortcut()

        elif action.getButtonCode() == KEY_SWITCH_TO_LAST:
            channel = self.getLastChannel()
            if channel:
                program = self.database.getCurrentProgram(channel)
                if program:
                    deb('Playling last program')
                    self.playChannel2(program)

    def onClick(self, controlId):
        debug('onClick')
        if self.isClosing:
            return
        self.lastKeystroke = datetime.datetime.now()
        channel = None

        if controlId == self.C_MAIN_CATEGORY:
            cList = self.getControl(self.C_MAIN_CATEGORY)
            item = cList.getSelectedItem()
            if item:
                self.category = item.getLabel()
                if sys.version_info[0] < 3:
                    self.category = self.category.decode('utf-8')

            self.database.setCategory(self.category)
            ADDON.setSetting('category', self.category)
            with self.busyDialog():
                self.onRedrawEPG(self.channelIdx == 1, self.viewStartDate)

        if controlId in [self.C_MAIN_LOADING_CANCEL, self.C_MAIN_MOUSEPANEL_EXIT]:
            if ADDON.getSetting('background_services') == 'true':
                background = True
            else:
                background = False

            if ADDON.getSetting('exit') == '0':
                # Ask to close
                ret = xbmcgui.Dialog().yesno(strings(30963), '{}?'.format(strings(30981)))
                if ret == False:
                    return
                elif ret == True:
                    self.close(background=background)
            else:
                # Close by two returns
                if (datetime.datetime.now() - self.lastCloseKeystroke).seconds < 3:
                    self.close(background=background)
                else:
                    self.lastCloseKeystroke = datetime.datetime.now()
                    xbmcgui.Dialog().notification(strings(30963), strings(30964), time=3000, sound=False)

        if self.isClosing:
            return

        if controlId == self.C_MAIN_MOUSEPANEL_HOME:
            self.viewStartDate = datetime.datetime.today() + datetime.timedelta(
                minutes=int(ADDON.getSetting('timebar_adjust')))
            self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)
            return
        elif controlId == self.C_MAIN_MOUSEPANEL_EPG_PAGE_LEFT:
            self.viewStartDate -= datetime.timedelta(hours=2)
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)
            return
        elif controlId == self.C_MAIN_MOUSEPANEL_EPG_PAGE_UP:
            self._moveUp(count=CHANNELS_PER_PAGE)
            return
        elif controlId == self.C_MAIN_MOUSEPANEL_EPG_PAGE_DOWN:
            self._moveDown(count=CHANNELS_PER_PAGE)
            return
        elif controlId == self.C_MAIN_MOUSEPANEL_EPG_PAGE_RIGHT:
            self.viewStartDate += datetime.timedelta(hours=2)
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)
            return
        elif controlId == self.C_MAIN_MOUSEPANEL_CURSOR_UP:
            self._moveUp(scrollEvent=True)
            return
        elif controlId == self.C_MAIN_MOUSEPANEL_CURSOR_DOWN:
            self._moveDown(scrollEvent=True)
            return
        elif controlId == self.C_MAIN_MOUSEPANEL_CURSOR_RIGHT:
            return
        elif controlId == self.C_MAIN_MOUSEPANEL_CURSOR_LEFT:
            return
        elif controlId == self.C_MAIN_MOUSEPANEL_SETTINGS:
            xbmcaddon.Addon(id=ADDON_ID).openSettings()
            return
        elif controlId >= 9010 and controlId <= 9021:
            o = controlId - 9010
            try:
                channel = self.a[o]
            except Exception as ex:
                deb('RecordAppImporter Error: {}'.format(getExceptionString()))

        program = self._getProgramFromControl(self.getControl(controlId))
        if channel is not None:
            if not self.playChannel(channel, program):
                result = self.streamingService.detectStream(channel)
                if not result:
                    return
                elif type(result) == str:
                    # one single stream detected, save it and start streaming
                    self.database.setCustomStreamUrl(channel, result)
                    self.playChannel(channel, program)

                else:
                    # multiple matches, let user decide

                    d = ChooseStreamAddonDialog(result)
                    d.doModal()
                    if d.stream is not None:
                        self.database.setCustomStreamUrl(channel, d.stream)
                        self.playChannel(channel, program)
            return

        if program is None:
            return

        if ADDON.getSetting('info_osd') == "true":

            if not self.playChannel2(program):
                result = self.streamingService.detectStream(program.channel)
                if not result:
                    # could not detect stream, show context menu
                    self._showContextMenu(program)
                elif type(result) == str:
                    # one single stream detected, save it and start streaming
                    self.database.setCustomStreamUrl(program.channel, result)
                    self.playChannel2(program)

                else:
                    # multiple matches, let user decide

                    d = ChooseStreamAddonDialog(result)
                    d.doModal()
                    if d.stream is not None:
                        self.database.setCustomStreamUrl(program.channel, d.stream)
                        self.playChannel2(program)

        else:
            if not self.playChannel(program.channel, program):
                result = self.streamingService.detectStream(program.channel)
                if not result:
                    # could not detect stream, show context menu
                    self._showContextMenu(program)
                elif type(result) == str:
                    # one single stream detected, save it and start streaming
                    self.database.setCustomStreamUrl(program.channel, result)
                    self.playChannel(program.channel)

                else:
                    # multiple matches, let user decide

                    d = ChooseStreamAddonDialog(result)
                    d.doModal()
                    if d.stream is not None:
                        self.database.setCustomStreamUrl(program.channel, d.stream)
                        self.playChannel(program.channel)

    def showListing(self, channel):
        programList = self.database.getChannelListing(channel)
        title = channel.title
        d = ProgramListDialog(title, programList, 0)
        d.doModal()
        index = d.index
        action = d.action
        if action == ACTION_RIGHT:
            self.showNow(programList[index].channel)
        elif action == ACTION_LEFT:
            self.showNext(programList[index].channel)
        elif action == KEY_NAV_BACK:
            self.index = -1
            d = xbmcgui.Dialog()
            list = d.select(strings(30309), [strings(30310), strings(30311), strings(30312), strings(30336), strings(30337), strings(30315)])

            if list < 0:
                self.onRedrawEPG(self.channelIdx, self.viewStartDate)
            if list == 0:
                self.showListing(programList[index].channel)
            elif list == 1:
                self.showNow(programList[index].channel)
            elif list == 2:
                self.showNext(programList[index].channel)
            elif list == 3:
                self.showFullReminders(channel)
            elif list == 4:
                self.showFullRecordings(channel)
            elif list == 5:
                self.programSearchSelect(channel)
        elif action == ACTION_SHOW_INFO:
            try:
                d = xbmcgui.Dialog()
                list = d.select(strings(31009), [strings(58000), strings(30356)])

                if list == 0:
                    self.Info(programList[index], self.playChannel2, self.recordProgram, self.notification, self.ExtendedInfo, self.onRedrawEPG, self.channelIdx, self.viewStartDate)
                    self.showListing(programList[index].channel)
                elif list == 1:
                    self.ExtendedInfo(programList[index])
                    self.showListing(programList[index].channel)
            except:
                pass
            return
        elif action == KEY_CONTEXT_MENU and xbmc.Player().isPlaying() == False:
            if index > -1:
                self.index = 1
                channelIdx = int(self.database.getCurrentChannelIdx(programList[index].channel))
                self.viewStartDate = programList[index].startDate
                self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 1, seconds=self.viewStartDate.second)
                self.onRedrawEPG(channelIdx, self.viewStartDate)
                #self._showContextMenu(programList[index])
        else:
            if index > -1:
                program = programList[index]
                now = datetime.datetime.now()
                start = program.startDate
                end = program.endDate
                self.playChannel2(program)

    def showNow(self, channel):
        programList = self.database.getNowList(channel)
        title = strings(30311)

        currentChannel = None
        for programInList in programList:
            if programInList.channel == channel:
                currentChannel = programList.index(programInList)

        d = ProgramListDialog(title, programList, currentChannel)
        d.doModal()
        index = d.index
        action = d.action
        if action == ACTION_RIGHT:
            self.showNext(programList[index].channel)
        elif action == ACTION_LEFT:
            self.showListing(programList[index].channel)
        elif action == KEY_NAV_BACK:
            self.index = -1
            d = xbmcgui.Dialog()
            list = d.select(strings(30309), [strings(30310), strings(30311), strings(30312), strings(30336), strings(30337), strings(30315)])

            if list < 0:
                self.onRedrawEPG(self.channelIdx, self.viewStartDate)
            if list == 0:
                self.showListing(programList[index].channel)
            elif list == 1:
                self.showNow(programList[index].channel)
            elif list == 2:
                self.showNext(programList[index].channel)
            elif list == 3:
                self.showFullReminders(channel)
            elif list == 4:
                self.showFullRecordings(channel)
            elif list == 5:
                self.programSearchSelect(channel)
        elif action == ACTION_SHOW_INFO:
            try:
                d = xbmcgui.Dialog()
                list = d.select(strings(31009), [strings(58000), strings(30356)])

                if list == 0:
                    self.Info(programList[index], self.playChannel2, self.recordProgram, self.notification, self.ExtendedInfo, self.onRedrawEPG, self.channelIdx, self.viewStartDate)
                    self.showNow(programList[index].channel)
                elif list == 1:
                    self.ExtendedInfo(programList[index])
                    self.showNow(programList[index].channel)
            except:
                pass
            return
        elif action == KEY_CONTEXT_MENU and xbmc.Player().isPlaying() == False:
            if index > -1:
                self.index = 1
                channelIdx = int(self.database.getCurrentChannelIdx(programList[index].channel))
                self.viewStartDate = programList[index].startDate
                self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 1, seconds=self.viewStartDate.second)
                self.onRedrawEPG(channelIdx, self.viewStartDate)
                #self._showContextMenu(programList[index])
        else:
            if index > -1:
                program = programList[index]
                now = datetime.datetime.now()
                start = program.startDate
                end = program.endDate
                self.playChannel2(program)

    def showNext(self, channel):
        programList = self.database.getNextList(channel)
        title = strings(30312)

        currentChannel = None
        for programInList in programList:
            if programInList.channel == channel:
                currentChannel = programList.index(programInList)

        d = ProgramListDialog(title, programList, currentChannel)
        d.doModal()
        index = d.index
        action = d.action
        if action == ACTION_LEFT:
            self.showNow(programList[index].channel)
        elif action == ACTION_RIGHT:
            self.showListing(programList[index].channel)
        elif action == KEY_NAV_BACK:
            self.index = -1
            d = xbmcgui.Dialog()
            list = d.select(strings(30309), [strings(30310), strings(30311), strings(30312), strings(30336), strings(30337), strings(30315)])

            if list < 0:
                self.onRedrawEPG(self.channelIdx, self.viewStartDate)
            if list == 0:
                self.showListing(programList[index].channel)
            elif list == 1:
                self.showNow(programList[index].channel)
            elif list == 2:
                self.showNext(programList[index].channel)
            elif list == 3:
                self.showFullReminders(channel)
            elif list == 4:
                self.showFullRecordings(channel)
            elif list == 5:
                self.programSearchSelect(channel)
        elif action == ACTION_SHOW_INFO:
            try:
                d = xbmcgui.Dialog()
                list = d.select(strings(31009), [strings(58000), strings(30356)])

                if list == 0:
                    self.Info(programList[index], self.playChannel2, self.recordProgram, self.notification, self.ExtendedInfo, self.onRedrawEPG, self.channelIdx, self.viewStartDate)
                    self.showNext(programList[index].channel)
                elif list == 1:
                    self.ExtendedInfo(programList[index])
                    self.showNext(programList[index].channel)
            except:
                pass
            return
        elif action == KEY_CONTEXT_MENU and xbmc.Player().isPlaying() == False:
            if index > -1:
                self.index = 1
                channelIdx = int(self.database.getCurrentChannelIdx(programList[index].channel))
                self.viewStartDate = programList[index].startDate
                self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 1, seconds=self.viewStartDate.second)
                self.onRedrawEPG(channelIdx, self.viewStartDate)
                #self._showContextMenu(programList[index])
        else:
            if index > -1:
                program = programList[index]
                now = datetime.datetime.now()
                start = program.startDate
                end = program.endDate
                self.playChannel2(program)

    def programSearchSelect(self, channel):
        d = xbmcgui.Dialog()
        what = d.select(strings(30315), [strings(30316), strings(30317), strings(30318), strings(30343), strings(30319)])

        if what == -1:
            d = xbmcgui.Dialog()
            list = d.select(strings(30309), [strings(30310), strings(30311), strings(30312), strings(30336), strings(30337), strings(30315)])

            if list < 0:
                self.onRedrawEPG(self.channelIdx, self.viewStartDate)
            if list == 0:
                index = self.database.getCurrentChannelIdx(channel)
                programList = self.database.getChannelListing(channel)
                self.showListing(programList[index].channel)
            elif list == 1:
                index = self.database.getCurrentChannelIdx(channel)
                programList = self.database.getChannelListing(channel)
                self.showNow(programList[index].channel)
            elif list == 2:
                index = self.database.getCurrentChannelIdx(channel)
                programList = self.database.getChannelListing(channel)
                self.showNext(programList[index].channel)
            elif list == 3:
                self.showFullReminders(channel)
            elif list == 4:
                self.showFullRecordings(channel)
            elif list == 5:
                self.programSearchSelect(channel)

        if what == 0:
            self.programSearch()
            if self.index < 0:
                self.index = -1
                self.programSearchSelect(channel)

        elif what == 1:
            self.descriptionSearch()
            if self.index < 0:
                self.index = -1
                self.programSearchSelect(channel)
        elif what == 2:
            self.categorySearchInput()
            if self.index < 0:
                self.index = -1
                self.programSearchSelect(channel)
        elif what == 3:
            self.categorySearch()
            if self.index < 0:
                self.index = -1
                self.programSearchSelect(channel)
        elif what == 4:
            self.channelSearch()
            if self.index < 0:
                self.index = -1
                self.programSearchSelect(channel)

    def programSearch(self):
        d = xbmcgui.Dialog()
        title = ''
        try:
            controlInFocus = self.getFocus()
            if controlInFocus:
                program = self._getProgramFromControl(controlInFocus)
                if program:
                    title = program.title
        except:
            if self.program:
                title = self.program.title
        file_name = os.path.join(self.profilePath, 'title_search.list')
        f = xbmcvfs.File(file_name, "rb")
        searches = sorted(f.read().splitlines())
        f.close()
        actions = [strings(30320), strings(30321)] + searches
        action = d.select(strings(30327).format(title), actions)
        if action == -1:
            return
        elif action == 0:
            pass
        elif action == 1:
            which = d.select(strings(30321), searches)
            if which == -1:
                return
            else:
                del searches[which]
                f = xbmcvfs.File(file_name, "wb")
                if sys.version_info[0] < 3:
                    searches = [x.decode('utf-8') for x in searches]
                f.write(bytearray('\n'.join(searches), 'utf-8'))
                f.close()
                return
        else:
            title = searches[action - 2]
        search = d.input(strings(30322), title)
        if not search:
            return
        searches = (set([search] + searches))
        f = xbmcvfs.File(file_name, "wb")
        if sys.version_info[0] < 3:
            searches = [x.decode('utf-8') for x in searches]
        f.write(bytearray('\n'.join(searches), 'utf-8'))
        f.close()
        programList = self.database.programSearch(search)
        title = strings(30322)
        d = ProgramListDialog(title, programList, ADDON.getSetting('listing_sort_time') == 'true')
        d.doModal()
        index = d.index
        action = d.action
        if action == ACTION_RIGHT:
            self.showNext(programList[index].channel)
        elif action == ACTION_LEFT:
            self.showListing(programList[index].channel)
        elif action == KEY_NAV_BACK:
            self.index = -1
        elif action == ACTION_SHOW_INFO:
            try:
                d = xbmcgui.Dialog()
                list = d.select(strings(31009), [strings(58000), strings(30356)])

                if list == 0:
                    self.Info(programList[index], self.playChannel2, self.recordProgram, self.notification, self.ExtendedInfo, self.onRedrawEPG, self.channelIdx, self.viewStartDate)
                    return
                elif list == 1:
                    self.ExtendedInfo(programList[index])
                    return
            except:
                pass
            return
        elif action == KEY_CONTEXT_MENU and xbmc.Player().isPlaying() == False:
            if index > -1:
                self.index = 1
                channelIdx = int(self.database.getCurrentChannelIdx(programList[index].channel))
                self.viewStartDate = programList[index].startDate
                self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 1, seconds=self.viewStartDate.second)
                self.onRedrawEPG(channelIdx, self.viewStartDate)
                #self._showContextMenu(programList[index])
        else:
            if index > -1:
                program = programList[index]
                now = datetime.datetime.now()
                start = program.startDate
                end = program.endDate
                self.playChannel2(program)

    def descriptionSearch(self):
        d = xbmcgui.Dialog()
        title = ''
        file_name = os.path.join(self.profilePath, 'synopsis_search.list')
        f = xbmcvfs.File(file_name, "rb")
        searches = sorted(f.read().splitlines())
        f.close()
        actions = [strings(30320), strings(30321)] + searches
        action = d.select(strings(30328), actions)
        if action == -1:
            return
        elif action == 0:
            pass
        elif action == 1:
            which = d.select(strings(30321), searches)
            if which == -1:
                return
            else:
                del searches[which]
                f = xbmcvfs.File(file_name, "wb")
                if sys.version_info[0] < 3:
                    searches = [x.decode('utf-8') for x in searches]
                f.write(bytearray('\n'.join(searches), 'utf-8'))
                f.close()
                return
        else:
            title = searches[action - 2]
        search = d.input(strings(30323), title)
        if not search:
            return
        searches = (set([search] + searches))
        f = xbmcvfs.File(file_name, "wb")
        if sys.version_info[0] < 3:
            searches = [x.decode('utf-8') for x in searches]
        f.write(bytearray('\n'.join(searches), 'utf-8'))
        f.close()
        programList = self.database.descriptionSearch(search)
        title = strings(30322)
        d = ProgramListDialog(title, programList, ADDON.getSetting('listing_sort_time') == 'true')
        d.doModal()
        index = d.index
        action = d.action
        if action == ACTION_RIGHT:
            self.showNext(programList[index].channel)
        elif action == ACTION_LEFT:
            self.showListing(programList[index].channel)
        elif action == KEY_NAV_BACK:
            self.index = -1
        elif action == ACTION_SHOW_INFO:
            exlist = list
            try:
                d = xbmcgui.Dialog()
                exlist = d.select(strings(31009), [strings(58000), strings(30356)])

                if exlist == 0:
                    self.Info(programList[index], self.playChannel2, self.recordProgram, self.notification, self.ExtendedInfo, self.onRedrawEPG, self.channelIdx, self.viewStartDate)
                    return
                elif exlist == 1:
                    self.ExtendedInfo(programList[index])
                    return
            except:
                pass
            return
        elif action == KEY_CONTEXT_MENU and xbmc.Player().isPlaying() == False:
            if index > -1:
                self.index = 1
                channelIdx = int(self.database.getCurrentChannelIdx(programList[index].channel))
                self.viewStartDate = programList[index].startDate
                self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 1, seconds=self.viewStartDate.second)
                self.onRedrawEPG(channelIdx, self.viewStartDate)
                #self._showContextMenu(programList[index])
        else:
            if index > -1:
                program = programList[index]
                now = datetime.datetime.now()
                start = program.startDate
                end = program.endDate
                self.playChannel2(program)

    def categorySearchInput(self):
        d = xbmcgui.Dialog()
        title = ''
        file_name = os.path.join(self.profilePath, 'category_search.list')
        f = xbmcvfs.File(file_name, "rb")
        searches = sorted(f.read().splitlines())
        f.close()
        actions = [strings(30320), strings(30321)] + searches
        action = d.select(strings(30345), actions)
        if action == -1:
            return
        elif action == 0:
            pass
        elif action == 1:
            which = d.select(strings(30321), searches)
            if which == -1:
                return
            else:
                del searches[which]
                f = xbmcvfs.File(file_name, "wb")
                if sys.version_info[0] < 3:
                    searches = [x.decode('utf-8') for x in searches]
                f.write(bytearray('\n'.join(searches), 'utf-8'))
                f.close()
                return
        else:
            title = searches[action - 2]
        search = d.input(strings(30344), title)
        if not search:
            return
        searches = (set([search] + searches))
        f = xbmcvfs.File(file_name, "wb")
        if sys.version_info[0] < 3:
            searches = [x.decode('utf-8') for x in searches]
        f.write(bytearray('\n'.join(searches), 'utf-8'))
        f.close()
        programList = self.database.programCategorySearch(search)
        title = strings(30344)
        d = ProgramListDialog(title, programList, ADDON.getSetting('listing_sort_time') == 'true')
        d.doModal()
        index = d.index
        action = d.action
        if action == ACTION_RIGHT:
            self.showNext(programList[index].channel)
        elif action == ACTION_LEFT:
            self.showListing(programList[index].channel)
        elif action == KEY_NAV_BACK:
            self.index = -1
        elif action == ACTION_SHOW_INFO:
            exlist = list
            try:
                d = xbmcgui.Dialog()
                exlist = d.select(strings(31009), [strings(58000), strings(30356)])
                if exlist == 0:
                    self.Info(programList[index], self.playChannel2, self.recordProgram, self.notification, self.ExtendedInfo, self.onRedrawEPG, self.channelIdx, self.viewStartDate)
                    return
                elif exlist == 1:
                    self.ExtendedInfo(programList[index])
                    return
            except:
                pass
            return
        elif action == KEY_CONTEXT_MENU and xbmc.Player().isPlaying() == False:
            if index > -1:
                self.index = 1
                channelIdx = int(self.database.getCurrentChannelIdx(programList[index].channel))
                self.viewStartDate = programList[index].startDate
                self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 1, seconds=self.viewStartDate.second)
                self.onRedrawEPG(channelIdx, self.viewStartDate)
                #self._showContextMenu(programList[index])
        else:
            if index > -1:
                program = programList[index]
                now = datetime.datetime.now()
                start = program.startDate
                end = program.endDate
                self.playChannel2(program)

    def categorySearch(self):
        d = xbmcgui.Dialog()
        f = xbmcvfs.File(os.path.join(self.profilePath, 'category_count.list'))
        if sys.version_info[0] > 2:
            category_count = [x.split("=", 1) for x in f.read().splitlines()]
        else:
            category_count = [x.split(b"=", 1) for x in f.readBytes().splitlines()]
        f.close()
        categories = []
        for (c, v) in category_count:
            if not self.database.category or self.database.category == "All Channels":
                s = "{} ({})".format(c, v)
            else:
                s = c
            if sys.version_info[0] > 2:
                categories.append(s)
            else:
                categories.append(s.decode("utf-8"))
        which = d.select(strings(30324), categories)
        if which == -1:
            return
        category = category_count[which][0]
        programList = self.database.programCategorySearch(category)
        title = "{}".format(category)
        d = ProgramListDialog(title, programList, ADDON.getSetting('listing_sort_time') == 'true')
        d.doModal()
        index = d.index
        action = d.action
        if action == ACTION_RIGHT:
            self.showNext(programList[index].channel)
        elif action == ACTION_LEFT:
            self.showListing(programList[index].channel)
        elif action == KEY_NAV_BACK:
            self.index = -1
        elif action == ACTION_SHOW_INFO:
            try:
                d = xbmcgui.Dialog()
                list = d.select(strings(31009), [strings(58000), strings(30356)])
                if list == 0:
                    self.Info(programList[index], self.playChannel2, self.recordProgram, self.notification, self.ExtendedInfo, self.onRedrawEPG, self.channelIdx, self.viewStartDate)
                    return
                elif list == 1:
                    self.ExtendedInfo(programList[index])
                    return
            except:
                pass
            return
        elif action == KEY_CONTEXT_MENU and xbmc.Player().isPlaying() == False:
            if index > -1:
                self.index = 1
                channelIdx = int(self.database.getCurrentChannelIdx(programList[index].channel))
                self.viewStartDate = programList[index].startDate
                self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 1, seconds=self.viewStartDate.second)
                self.onRedrawEPG(channelIdx, self.viewStartDate)
                #self._showContextMenu(programList[index])
        else:
            if index > -1:
                program = programList[index]
                now = datetime.datetime.now()
                start = program.startDate
                end = program.endDate
                self.playChannel2(program)

    def channelSearch(self):
        d = xbmcgui.Dialog()
        search = d.input(strings(30326))
        if not search:
            return
        programList = self.database.channelSearch(search)
        title = strings(30326)
        d = ProgramListDialog(title, programList, self.currentChannel, ADDON.getSetting('listing_sort_time') == 'true')
        d.doModal()
        index = d.index
        action = d.action
        if action == ACTION_RIGHT:
            self.showNext(programList[index].channel)
        elif action == ACTION_LEFT:
            self.showListing(programList[index].channel)
        elif action == KEY_NAV_BACK:
            self.index = -1
        elif action == ACTION_SHOW_INFO:
            try:
                d = xbmcgui.Dialog()
                list = d.select(strings(31009), [strings(58000), strings(30356)])
                if list == 0:
                    self.Info(programList[index], self.playChannel2, self.recordProgram, self.notification, self.ExtendedInfo, self.onRedrawEPG, self.channelIdx, self.viewStartDate)
                    return
                elif list == 1:
                    self.ExtendedInfo(programList[index])
                    return
            except:
                pass
            return
        elif action == KEY_CONTEXT_MENU and xbmc.Player().isPlaying() == False:
            if index > -1:
                self.index = 1
                channelIdx = int(self.database.getCurrentChannelIdx(programList[index].channel))
                self.viewStartDate = programList[index].startDate
                self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 1, seconds=self.viewStartDate.second)
                self.onRedrawEPG(channelIdx, self.viewStartDate)
                #self._showContextMenu(programList[index])
        else:
            if index > -1:
                program = programList[index]
                now = datetime.datetime.now()
                start = program.startDate
                end = program.endDate
                self.playChannel2(program)

    def showReminders(self, channel):
        programList = self.database.getNotifications()
        title = (strings(30336))
        d = ProgramListDialog(title, programList, self.currentChannel, ADDON.getSetting('listing_sort_time') == 'true')
        d.doModal()
        index = d.index
        action = d.action
        if action == ACTION_RIGHT:
            self.showNext(programList[index].channel)
        elif action == ACTION_LEFT:
            self.showListing(programList[index].channel)
        elif action == KEY_NAV_BACK:
            self.index = -1
            d = xbmcgui.Dialog()
            list = d.select(strings(30309), [strings(30310), strings(30311), strings(30312), strings(30336), strings(30337), strings(30315)])
            if list < 0:
                self.onRedrawEPG(self.channelIdx, self.viewStartDate)
            if list == 0:
                index = self.database.getCurrentChannelIdx(channel)
                programList = self.database.getChannelListing(channel)
                self.showListing(programList[index].channel)
            elif list == 1:
                index = self.database.getCurrentChannelIdx(channel)
                programList = self.database.getChannelListing(channel)
                self.showNow(programList[index].channel)
            elif list == 2:
                index = self.database.getCurrentChannelIdx(channel)
                programList = self.database.getChannelListing(channel)
                self.showNext(programList[index].channel)
            elif list == 3:
                self.showFullReminders(channel)
            elif list == 4:
                self.showFullRecordings(channel)
            elif list == 5:
                self.programSearchSelect(channel)
        elif action == KEY_CONTEXT_MENU and xbmc.Player().isPlaying() == False:
            if index > -1:
                self.index = 1
                channelIdx = int(self.database.getCurrentChannelIdx(programList[index].channel))
                self.viewStartDate = programList[index].startDate
                self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 1, seconds=self.viewStartDate.second)
                self.onRedrawEPG(channelIdx, self.viewStartDate)
                #self._showContextMenu(programList[index])
        elif action == ACTION_SHOW_INFO:
            try:
                d = xbmcgui.Dialog()
                list = d.select(strings(31009), [strings(58000), strings(30356)])
                if list == 0:
                    self.Info(programList[index], self.playChannel2, self.recordProgram, self.notification, self.ExtendedInfo, self.onRedrawEPG, self.channelIdx, self.viewStartDate)
                    self.showReminders(programList[index].channel)
                elif list == 1:
                    self.ExtendedInfo(programList[index])
                    self.showReminders(programList[index].channel)
            except:
                pass
            return
        else:
            if index > -1:
                program = programList[index]
                now = datetime.datetime.now()
                start = program.startDate
                end = program.endDate
                self.playChannel2(program)

    def showFullReminders(self, channel):
        programList = self.database.getFullNotifications(int(ADDON.getSetting('listing_days')))
        title = (strings(30336))
        d = ProgramListDialog(title, programList, self.currentChannel, ADDON.getSetting('listing_sort_time') == 'true')
        d.doModal()
        index = d.index
        action = d.action
        if action == ACTION_RIGHT:
            self.showNext(programList[index].channel)
        elif action == ACTION_LEFT:
            self.showListing(programList[index].channel)
        elif action == KEY_NAV_BACK:
            self.index = -1
            d = xbmcgui.Dialog()
            list = d.select(strings(30309), [strings(30310), strings(30311), strings(30312), strings(30336), strings(30337), strings(30315)])
            if list < 0:
                self.onRedrawEPG(self.channelIdx, self.viewStartDate)
            if list == 0:
                index = self.database.getCurrentChannelIdx(channel)
                programList = self.database.getChannelListing(channel)
                self.showListing(programList[index].channel)
            elif list == 1:
                index = self.database.getCurrentChannelIdx(channel)
                programList = self.database.getChannelListing(channel)
                self.showNow(programList[index].channel)
            elif list == 2:
                index = self.database.getCurrentChannelIdx(channel)
                programList = self.database.getChannelListing(channel)
                self.showNext(programList[index].channel)
            elif list == 3:
                self.showFullReminders(channel)
            elif list == 4:
                self.showFullRecordings(channel)
            elif list == 5:
                self.programSearchSelect(channel)
        elif action == KEY_CONTEXT_MENU and xbmc.Player().isPlaying() == False:
            if index > -1:
                self.index = 1
                channelIdx = int(self.database.getCurrentChannelIdx(programList[index].channel))
                self.viewStartDate = programList[index].startDate
                self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 1, seconds=self.viewStartDate.second)
                self.onRedrawEPG(channelIdx, self.viewStartDate)
                #self._showContextMenu(programList[index])
        elif action == ACTION_SHOW_INFO:
            try:
                d = xbmcgui.Dialog()
                list = d.select(strings(31009), [strings(58000), strings(30356)])
                if list == 0:
                    self.Info(programList[index], self.playChannel2, self.recordProgram, self.notification, self.ExtendedInfo, self.onRedrawEPG, self.channelIdx, self.viewStartDate)
                    self.showFullReminders(programList[index].channel)
                elif list == 1:
                    self.ExtendedInfo(programList[index])
                    self.showFullReminders(programList[index].channel)
            except:
                pass
            return
        else:
            if index > -1:
                program = programList[index]
                now = datetime.datetime.now()
                start = program.startDate
                end = program.endDate
                self.playChannel2(program)

    def showFullRecordings(self, channel):
        programList = self.database.getFullRecordings(int(ADDON.getSetting('listing_days')))
        title = (strings(30337))
        d = ProgramListDialog(title, programList, self.currentChannel, ADDON.getSetting('listing_sort_time') == 'true')
        d.doModal()
        index = d.index
        action = d.action
        if action == ACTION_RIGHT:
            self.showNext(programList[index].channel)
        elif action == ACTION_LEFT:
            self.showListing(programList[index].channel)
        elif action == KEY_NAV_BACK:
            self.index = -1
            d = xbmcgui.Dialog()
            list = d.select(strings(30309), [strings(30310), strings(30311), strings(30312), strings(30336), strings(30337), strings(30315)])
            if list < 0:
                self.onRedrawEPG(self.channelIdx, self.viewStartDate)
            if list == 0:
                index = self.database.getCurrentChannelIdx(channel)
                programList = self.database.getChannelListing(channel)
                self.showListing(programList[index].channel)
            elif list == 1:
                index = self.database.getCurrentChannelIdx(channel)
                programList = self.database.getChannelListing(channel)
                self.showNow(programList[index].channel)
            elif list == 2:
                index = self.database.getCurrentChannelIdx(channel)
                programList = self.database.getChannelListing(channel)
                self.showNext(programList[index].channel)
            elif list == 3:
                self.showFullReminders(channel)
            elif list == 4:
                self.showFullRecordings(channel)
            elif list == 5:
                self.programSearchSelect(channel)
        elif action == KEY_CONTEXT_MENU and xbmc.Player().isPlaying() == False:
            if index > -1:
                self.index = 1
                channelIdx = int(self.database.getCurrentChannelIdx(programList[index].channel))
                self.viewStartDate = programList[index].startDate
                self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 1, seconds=self.viewStartDate.second)
                self.onRedrawEPG(channelIdx, self.viewStartDate)
                #self._showContextMenu(programList[index])
        elif action == ACTION_SHOW_INFO:
            try:
                d = xbmcgui.Dialog()
                list = d.select(strings(31009), [strings(58000), strings(30356)])
                if list == 0:
                    self.Info(programList[index], self.playChannel2, self.recordProgram, self.notification, self.ExtendedInfo, self.onRedrawEPG, self.channelIdx, self.viewStartDate)
                    self.showFullRecordings(programList[index].channel)
                elif list == 1:
                    self.ExtendedInfo(programList[index])
                    self.showFullRecordings(programList[index].channel)
            except:
                pass
            return
        else:
            if index > -1:
                program = programList[index]
                now = datetime.datetime.now()
                start = program.startDate
                end = program.endDate
                self.playChannel2(program)

    def channelsSelect(self):
        res = xbmcgui.Dialog().select(strings(59994), [strings(30325), strings(59995), strings(60005)])

        if res < 0:
            return

        if res == 0:
            channels = 0
            self.letterSort(channels)

        elif res == 1:
            channels = 1
            self.letterSort(channels)

        #elif res == 2:
            #kb = xbmc.Keyboard('','')
            #kb.setHeading('Create channel')
            #kb.setHiddenInput(False)
            #kb.doModal()
            #c = kb.getText() if kb.isConfirmed() else None
            #if c == '': c = None

            #epgChann = c

        elif res == 2:
            p = re.compile('\s<channel id="(.*?)"', re.DOTALL)

            with open(os.path.join(self.profilePath, 'basemap_extra.xml'), 'r') as f:
                base = f.read()

                channList = p.findall(base)

                res = xbmcgui.Dialog().multiselect(strings(60006), channList)
                if res:
                    for item in res:
                        p = re.compile('<channel id="{}".*/>\n'.format(channList[item]))
                        base = p.sub('', base)
                    
                    with open(os.path.join(self.profilePath, 'basemap_extra.xml'), 'w') as f:
                        f.write(base)

                    xbmcgui.Dialog().ok(strings(57051), strings(60007))
                    self.onRedrawEPG(self.channelIdx, self.viewStartDate)

                else:
                    self.channelsSelect()
        
        
    def letterSort(self, channels):
        epgList = list()

        v = ([channel.title.upper() for channel in self.database.getChannelList()])
        n = ([channel.title.upper() for channel in self.database.getAllChannelList()])

        if channels < 2:
            if channels == 0:
                res = xbmcgui.Dialog().select(strings(59994), [strings(30988), strings(59997)])

                if res < 0:
                    self.channelsSelect()

                if res == 0:
                    epgList = v + n
                    epgList = sorted(epgList)

                elif res == 1:
                    letterList = [chr(chNum) for chNum in list(range(ord('A'), ord('Z')+1))]
                    res = xbmcgui.Dialog().select(strings(59994), letterList)

                    if res < 0:
                        self.letterSort(channels)

                    else:
                        check = letterList[res]
                        epgList = [idx for idx in v + n if idx[0].lower() == check.lower()] 
                        epgList = sorted(epgList)
                
                if epgList:
                    self.channelsFromEPG(epgList, channels)

            elif channels == 1:
                res = xbmcgui.Dialog().select(strings(59994), [strings(30988), strings(59997)])

                if res < 0:
                    self.channelsSelect()

                if res == 0:
                    epgList = [idx for idx in n if not idx in v]
                    epgList = sorted(epgList)

                elif res == 1:
                    letterList = [chr(chNum) for chNum in list(range(ord('A'), ord('Z')+1))]
                    res = xbmcgui.Dialog().select(strings(59994), letterList)
                    
                    if res < 0:
                        self.letterSort(channels)

                    else:
                        check = letterList[res]
                        epgList = [idx for idx in n if idx[0].lower() == check.lower()]
                        epgList = sorted(epgList)

                if epgList:
                    self.channelsFromEPG(epgList, channels)

        else:
            self.channelsSelect()

    def channelsFromEPG(self, epgList, channels):
        res = xbmcgui.Dialog().select(strings(59991), epgList)

        if res < 0:
            self.letterSort(channels)

        else:
            epgChann = epgList[res]
            self.channelsFromStream(epgChann, epgList, channels)

    def channelsFromStream(self, epgChann="", epgList="", channels=""):
        file = xbmcvfs.File(os.path.join(self.profilePath, 'stream_url.list'), 'r')
        getStreams = file.read().splitlines()
        strmList = getStreams

        strmList = sorted(set(strmList))
        strmList = [x.strip() for x in strmList if x.strip()]
        
        res = xbmcgui.Dialog().select(strings(59992), strmList)

        if res < 0:
            if epgList is not None:
                self.channelsFromEPG(epgList, channels)
            else:
                self.channelsSelect()

        else:
            regChann = strmList[res]
            self.channelRegex(epgChann, regChann)

    def channelRegex(self, epgChann, regChann):
        # regex format
        regChann = re.sub('[ ](?=[ ])|[^-_,A-Za-z0-9 ]+', '', regChann)

        regex = '(?='+regChann.upper()+'$)'.replace(' ', r'\s*')

        regex = re.sub('  ', ' ', str(regex))
        regex = re.sub(' ', '\\ s *', str(regex))
        regex = re.sub('\+', '(\\ +|PLUS)', str(regex))
        regex = re.sub('\-', '(\\ -|\\ s *)', str(regex))
        regex = re.sub('&', '(and|&amp;)', str(regex))
        regex = re.sub(' ', '', str(regex))

        #Add to map
        item = '<channel id="{}"\t\t\t\t\t\t\t\t\ttitle="{}" strm=""/>'.format(epgChann, regex)

        with open(os.path.join(self.profilePath, 'basemap_extra.xml'), 'r+') as f:
            s = f.read()
            new_str = re.sub(r'^(.*{}.*)$'.format(re.escape('strm=""/>')), lambda g: g.group(0) + '\n\t'+item, s, count=1, flags=re.MULTILINE)
            f.seek(0)
            f.write(new_str)
            xbmcgui.Dialog().ok(strings(57051), strings(59993).format(regChann.upper()))
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)


    def _showContextMenu(self, program):
        deb('_showContextMenu')
        self._hideControl(self.C_MAIN_MOUSEPANEL_CONTROLS)
        d = PopupMenu(self.database, program, not program.notificationScheduled)
        d.doModal()
        buttonClicked = d.buttonClicked
        new_category = d.category
        del d

        if buttonClicked == PopupMenu.C_POPUP_REMIND:
            if program.notificationScheduled:
                self.notification.removeNotification(program)
            else:
                self.notification.addNotification(program)

            self.onRedrawEPG(self.channelIdx, self.viewStartDate)

        elif buttonClicked == PopupMenu.C_POPUP_CHOOSE_STREAM:
            d = StreamSetupDialog(self.database, program.channel)
            d.doModal()
            del d

        elif buttonClicked == PopupMenu.C_POPUP_PLAY:
            self.playChannel(program.channel)

        elif buttonClicked == PopupMenu.C_POPUP_CHANNELS:
            d = ChannelsMenu(self.database, program.channel)
            d.doModal()
            del d
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)

        elif buttonClicked == PopupMenu.C_POPUP_QUIT:
            self.close()

        elif buttonClicked == PopupMenu.C_POPUP_ADDON_SETTINGS:
            xbmcaddon.Addon(id=ADDON_ID).openSettings()

        elif buttonClicked == PopupMenu.C_POPUP_RECORD:
            if program.recordingScheduled:
                self.recordProgram(program)

            elif program.endDate <= datetime.datetime.now():
                self.recordProgram(program)

            else:
                res = xbmcgui.Dialog().select(strings(70006) + ' - m-TVGuide [COLOR gold]EPG[/COLOR]', [strings(30622), strings(30623)])
                if res < 0:
                    return

                if res == 0:
                    hours = xbmcgui.Dialog().numeric(0, strings(30624))
                    if hours == '':
                        return
                    else:
                        self.recordProgram(program, watch=True, length=hours)

                if res == 1:
                    self.recordProgram(program)

        elif buttonClicked == PopupMenu.C_POPUP_INFO:
            deb('Info')
            self.infoDialog = InfoDialog(program, self.playChannel2, self.recordProgram, self.notification,
                                         self.ExtendedInfo, self.onRedrawEPG, self.channelIdx, self.viewStartDate)
            self.infoDialog.setChannel(program)
            self.infoDialog.doModal()
            del self.infoDialog
            self.infoDialog = None

        elif buttonClicked == PopupMenu.C_POPUP_RECORDINGS:
            if sys.version_info[0] > 2:
                record_folder = ADDON.getSetting('record_folder')
                xbmc.executebuiltin('ActivateWindow(Videos,{record_folder},return)'.format(record_folder=record_folder))
            else:
                record_folder = native(ADDON.getSetting('record_folder'))
                xbmc.executebuiltin(b'ActivateWindow(Videos,{record_folder},return)'.format(record_folder=record_folder))

        elif buttonClicked == PopupMenu.C_POPUP_LISTS:
            d = xbmcgui.Dialog()
            list = d.select(strings(30309), [strings(30310), strings(30311), strings(30312), strings(30336), strings(30337), strings(30315)])

            if list < 0:
                self.onRedrawEPG(self.channelIdx, self.viewStartDate)
            if list == 0:
                self.showListing(program.channel)
            elif list == 1:
                self.showNow(program.channel)
            elif list == 2:
                self.showNext(program.channel)
            elif list == 3:
                self.showFullReminders(program.channel)
            elif list == 4:
                self.showFullRecordings(program.channel)
            elif list == 5:
                self.programSearchSelect(program.channel)
            return

        elif buttonClicked == PopupMenu.C_POPUP_CATEGORY:
            self.database.setCategory(new_category)
            ADDON.setSetting('category', new_category)
            with self.busyDialog():
                self.onRedrawEPG(self.channelIdx == 1, self.viewStartDate)

        elif buttonClicked == PopupMenu.C_POPUP_NUMBER:
            if ADDON.getSetting('channel_shortcut') == 'false':
                xbmcgui.Dialog().notification(strings(30353), strings(30354))
            else:
                if ADDON.getSetting('channel_shortcut') == 'true':
                    d = xbmcgui.Dialog()
                    number = d.input(strings(30346), type=xbmcgui.INPUT_NUMERIC)
                    if number:
                        self.channel_number = number
                        if self.timer and self.timer.is_alive():
                            self.timer.cancel()
                        self.playShortcut()

        elif buttonClicked == PopupMenu.C_POPUP_EXTENDED:
            deb('ExtendedInfo')
            self.ExtendedInfo(program)

        elif buttonClicked == PopupMenu.C_POPUP_FAQ:
            xbmcgui.Dialog().textviewer(strings(30994), strings(99996))
            return

        elif buttonClicked == PopupMenu.C_POPUP_FAVOURITES:
            xbmc.executebuiltin("ActivateWindow(10134)")

        elif buttonClicked == PopupMenu.C_POPUP_ADD_CHANNEL:
            deb('AddChannel')
            self.channelsSelect()
            return

    def setFocusId(self, controlId):
        debug('setFocusId')
        control = self.getControl(controlId)
        if control:
            self.setFocus(control)

    def setFocus(self, control):
        # debug('setFocus {}'.format(control.getId()))
        if control.getId() in [elem.control.getId() for elem in self.controlAndProgramList]:
            (left, top) = control.getPosition()
            if left > self.focusPoint.x or left + control.getWidth() < self.focusPoint.x:
                self.focusPoint.x = left
            self.focusPoint.y = top + (control.getHeight() // 2)
        super(mTVGuide, self).setFocus(control)

    def onFocus(self, controlId):
        # Call filling all program data was delayed, because of Kodi internal error which may lead to Kodi freeze when scrolling
        try:
            if self.onFocusTimer:
                self.onFocusTimer.cancel()
            self.onFocusTimer = threading.Timer(0.30, self.delayedOnFocus, [controlId])
            self.onFocusTimer.start()
        except:
            pass

    def realtimeDate(self, program):
        #Realtime date & weekday
        startDate = str(program.startDate)
        try:
            now = datetime.proxydt.strptime(startDate, '%Y-%m-%d %H:%M:%S')
        except:
            now = datetime.proxydt.strptime(str(datetime.datetime.now()), '%Y-%m-%d %H:%M:%S.%f')

        try:
            nowDay = now.strftime("%a").replace('Mon', strings(70109)).replace('Tue', strings(70110)).replace('Wed', strings(70111)).replace('Thu', strings(70112)).replace('Fri', strings(70113)).replace('Sat', strings(70114)).replace('Sun', strings(70115))
        except:
            nowDay = now.strftime("%a").replace('Mon', strings(70109).encode('UTF-8')).replace('Tue', strings(70110).encode('UTF-8')).replace('Wed', strings(70111).encode('UTF-8')).replace('Thu', strings(70112).encode('UTF-8')).replace('Fri', strings(70113).encode('UTF-8')).replace('Sat', strings(70114).encode('UTF-8')).replace('Sun', strings(70115).encode('UTF-8'))
        
        nowDate = now.strftime("%d-%m-%Y")

        self.setControlLabel(C_MAIN_DAY, '{}'.format(nowDay))
        self.setControlLabel(C_MAIN_REAL_DATE, '{}'.format(nowDate))

    def calctimeLeft(self, program):
        #Calc time EPG
        startDelta = datetime.datetime.now() - program.startDate
        endDelta = datetime.datetime.now() - program.endDate

        calcTime = startDelta - endDelta

        self.setControlLabel(C_MAIN_CALC_TIME_EPG, '{}'.format(calcTime))

    def getLastPlayingChannel(self):
        file_name = os.path.join(self.profilePath, 'autoplay.list')
        try:    
            with open(file_name, 'r') as f:
                value = f.read()
                idx = int(value.split(',')[0])
                date = value.split(',')[1]
        except:
            idx = int(0)
            controlInFocus = self.getFocus()
            program = self._getProgramFromControl(controlInFocus)
            date = program.startDate

        startDate = proxydt.strptime(str(date), '%Y-%m-%d %H:%M:%S')

        channelList = self.database.getChannelList(onlyVisible=True)
        try:
            chann = channelList[idx]
        except:
            chann = channelList[0]

        prog = self.database.getProgramStartingAt(chann, startDate)

        return chann, prog, idx

    def delayedOnFocus(self, controlId):
        debug('onFocus controlId: {}'.format(controlId))
        try:
            controlInFocus = self.getControl(controlId)
        except Exception as ex:
            deb('onFocus Exception str: {}'.format(getExceptionString()))
            return

        program = self._getProgramFromControl(controlInFocus)
        if program is None:
            return

        self.setControlLabel(C_MAIN_CHAN_NAME, '{}'.format(program.channel.title))
        self.setControlLabel(C_MAIN_TITLE, '{}'.format(program.title))
        self.setControlLabel(C_MAIN_TIME, '{} - {}'.format(self.formatTime(program.startDate), self.formatTime(program.endDate)))

        try:
            if ADDON.getSetting('info_osd') == "false" or self.program is None:
                chann, prog, idx = self.getLastPlayingChannel()

                self.setControlLabel(C_MAIN_CHAN_PLAY, '{}'.format(chann.id))
                self.setControlLabel(C_MAIN_PROG_PLAY, '{}'.format(prog.title))
                self.setControlLabel(C_MAIN_NUMB_PLAY, '{}'.format((str(int(idx) + 1))))
        except:
            pass

        if program.description:
            description = program.description
        elif program.categoryA:
            description = strings(NO_DESCRIPTION)
            category = program.categoryA
        else:
            description = strings(NO_DESCRIPTION)
            category = strings(NO_CATEGORY)

        if skin_separate_category or skin_separate_year_of_production or skin_separate_director or skin_separate_episode or skin_separate_allowed_age_icon or skin_separate_program_progress or skin_separate_program_progress_epg or skin_separate_program_actors:
            # This mean we'll need to parse program description
            descriptionParser = src.ProgramDescriptionParser(description)
            if skin_separate_category:
                category = descriptionParser.extractCategory()
                if category == '':
                    category = program.categoryA
                    if category == '':
                        category = strings(NO_CATEGORY)
                self.setControlText(C_PROGRAM_CATEGORY, category)
            if skin_separate_year_of_production:
                year = descriptionParser.extractProductionDate()
                if year == '':
                    year = program.productionDate
                self.setControlText(C_PROGRAM_PRODUCTION_DATE, year)
            if skin_separate_director:
                director = descriptionParser.extractDirector()
                if director == '':
                    director = program.director
                self.setControlText(C_PROGRAM_DIRECTOR, director)
            if skin_separate_episode:
                episode = descriptionParser.extractEpisode()
                if episode == '':
                    episode = program.episode
                self.setControlText(C_PROGRAM_EPISODE, episode)
            if skin_separate_allowed_age_icon:
                icon = descriptionParser.extractAllowedAge()
                p = re.compile('^http(s)?:\/\/.*')

                if p.match(icon):
                    self.setControlImage(C_PROGRAM_AGE_ICON, icon)
            if skin_separate_program_actors:
                actors = descriptionParser.extractActors()
                if actors == '':
                    actors = program.actor
                self.setControlText(C_PROGRAM_ACTORS, actors)
            if skin_separate_program_progress:
                try:
                    programProgressControl = self.getControl(C_MAIN_PROGRAM_PROGRESS)
                    stdat = time.mktime(self.program.startDate.timetuple())
                    endat = time.mktime(self.program.endDate.timetuple())
                    nodat = time.mktime(datetime.datetime.now().timetuple())
                    percent = 100 - ((endat - nodat) // ((endat - stdat) // 100))
                    if percent > 0 and percent < 100:
                        programProgressControl.setVisible(True)
                        programProgressControl.setPercent(percent)
                    else:
                        programProgressControl.setVisible(False)
                except:
                    pass
            if skin_separate_program_progress_epg:
                try:
                    programProgressControl = self.getControl(C_MAIN_PROGRAM_PROGRESS_EPG)
                    stdat = time.mktime(program.startDate.timetuple())
                    endat = time.mktime(program.endDate.timetuple())
                    nodat = time.mktime(datetime.datetime.now().timetuple())
                    percent = 100 - ((endat - nodat) // ((endat - stdat) // 100))
                    if percent > 0 and percent < 100:
                        programProgressControl.setVisible(True)
                        programProgressControl.setPercent(percent)
                    else:
                        programProgressControl.setVisible(False)
                except:
                    pass

            description = descriptionParser.description

        self.setControlText(C_MAIN_DESCRIPTION, description)
        
        p = re.compile('^http(s)?:\/\/.*')

        if program.channel.logo is not None:
            self.setControlImage(C_MAIN_LOGO, program.channel.logo)
        if program.imageSmall is not None and ADDON.getSetting('show_program_logo') == "true":
            if p.match(program.imageSmall):
                self.setControlImage(C_MAIN_IMAGE, program.imageSmall)
            else: program.imageSmall is None
        if program.imageSmall is None:
            self.setControlImage(C_MAIN_IMAGE, 'tvguide-logo-epg.png')
        if program.imageLarge == 'live':
            self.setControlImage(C_MAIN_LIVE, 'live.png')
        else:
            self.setControlImage(C_MAIN_LIVE, '')

        try:
            self.realtimeDate(program)
            self.calctimeLeft(program)
        except:
            pass

    def _left(self, currentFocus):
        # debug('_left')
        control = self._findControlOnLeft(currentFocus)
        if control is not None:
            self.setFocus(control)

        elif control is None:
            self.viewStartDate -= datetime.timedelta(hours=2)
            self.focusPoint.x = self.epgView.right
            self.onRedrawEPG(self.channelIdx, self.viewStartDate, focusFunction=self._findControlOnLeft)

    def _right(self, currentFocus):
        # debug('_right')
        control = self._findControlOnRight(currentFocus)
        if control is not None:
            self.setFocus(control)
            
        elif control is None:
            self.viewStartDate += datetime.timedelta(hours=2)
            self.focusPoint.x = self.epgView.left
            self.onRedrawEPG(self.channelIdx, self.viewStartDate, focusFunction=self._findControlOnRight)

    def _up(self, currentFocus):
        # debug('_up')
        currentFocus.x = self.focusPoint.x
        control = self._findControlAbove(currentFocus)
        if control is not None:
            self.setFocus(control)
        elif control is None:
            self.focusPoint.y = self.epgView.bottom
            self.onRedrawEPG(self.channelIdx - CHANNELS_PER_PAGE, self.viewStartDate,
                             focusFunction=self._findControlAbove)

    def _down(self, currentFocus):
        # debug('_down')
        currentFocus.x = self.focusPoint.x
        control = self._findControlBelow(currentFocus)
        if control is not None:
            self.setFocus(control)
        elif control is None:
            self.focusPoint.y = self.epgView.top
            self.onRedrawEPG(self.channelIdx + CHANNELS_PER_PAGE, self.viewStartDate,
                             focusFunction=self._findControlBelow)

    def _nextDay(self):
        deb('_nextDay')
        self.viewStartDate += datetime.timedelta(days=1)
        self.onRedrawEPG(self.channelIdx, self.viewStartDate)

    def _previousDay(self):
        deb('_previousDay')
        self.viewStartDate -= datetime.timedelta(days=1)
        self.onRedrawEPG(self.channelIdx, self.viewStartDate)

    def _moveUp(self, count=1, scrollEvent=False):
        debug('_moveUp')
        if scrollEvent:
            self.dontBlockOnAction = True
            self.onRedrawEPG(self.channelIdx - count, self.viewStartDate)
            self.dontBlockOnAction = False
        else:
            self.focusPoint.y = self.epgView.bottom
            self.onRedrawEPG(self.channelIdx - count, self.viewStartDate, focusFunction=self._findControlAbove)

    def _moveDown(self, count=1, scrollEvent=False):
        debug('_moveDown')
        if scrollEvent:
            self.dontBlockOnAction = True
            self.onRedrawEPG(self.channelIdx + count, self.viewStartDate)
            self.dontBlockOnAction = False
        else:
            self.focusPoint.y = self.epgView.top
            self.onRedrawEPG(self.channelIdx + count, self.viewStartDate, focusFunction=self._findControlBelow)

    def _channelUp(self):
        channel = self.database.getNextChannel(self.currentChannel)
        self.playChannel2(self.database.getCurrentProgram(channel))

    def _channelDown(self):
        channel = self.database.getPreviousChannel(self.currentChannel)
        self.playChannel2(self.database.getCurrentProgram(channel))

    def playRecordedProgram(self, program):
        self.playingRecordedProgram = False
        recordedProgram = self.recordService.isProgramRecorded(program)
        if recordedProgram is not None:
            diff = program.endDate - datetime.datetime.now()
            diffSeconds = (diff.days * 86400) + diff.seconds
            if diffSeconds <= 0:
                # start recorded program which already ended
                ret = True
            else:
                ret = xbmcgui.Dialog().yesno(strings(RECORDED_FILE_POPUP), '{} {}?'.format(strings(RECORDED_FILE_QUESTION), program.title))

            if ret == True:
                #if ADDON.getSetting('start_video_minimalized') == 'true':
                    #startWindowed = True
                #else:
                    #startWindowed = False
                try:
                    firstFileInPlaylist = recordedProgram[0].getfilename()
                    playlistIndex = int(self.recordedFilesPlaylistPositions[firstFileInPlaylist])
                except:
                    playlistIndex = -1

                deb('playRecordedProgram starting play of recorded program {} from index {}'.format(program.title, playlistIndex))

                xbmc.Player().play(item=recordedProgram, windowed=False, startpos=playlistIndex)
                self.playingRecordedProgram = True
                return True
        return False

    @contextmanager
    def busyPlayDialog(self):
        time.sleep(1)
        if xbmc.getCondVisibility('!Window.IsVisible(fullscreenvideo)'):
            xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
        try:
            yield
        finally:
            xbmc.executebuiltin('Dialog.Close(busydialognocancel)')

    def playAndWatchRecordedProgram(self, program):
        with self.busyPlayDialog():
            time.sleep(5)
            self.playingRecordedProgram = False
            recordedProgram = self.recordService.isProgramRecorded(program)
            if recordedProgram is not None:
                diff = program.endDate - datetime.datetime.now()
                diffSeconds = (diff.days * 86400) + diff.seconds
                
                #if ADDON.getSetting('start_video_minimalized') == 'true':
                    #startWindowed = True
                #else:
                    #startWindowed = False
                try:
                    firstFileInPlaylist = recordedProgram[0].getfilename()
                    playlistIndex = int(self.recordedFilesPlaylistPositions[firstFileInPlaylist])
                except:
                    playlistIndex = -1

                deb('playRecordedProgram starting play of recorded program {} from index {}'.format(program.title, playlistIndex))

                xbmc.Player().play(item=recordedProgram, windowed=False, startpos=playlistIndex)
                self.playingRecordedProgram = True
                return True

    def updateCurrentChannel(self, channel):
        deb('updateCurrentChannel')
        self.lastChannel = self.currentChannel
        self.currentChannel = channel

        date = datetime.datetime.now()

        file_name = os.path.join(self.profilePath, 'autoplay.list')
        f = xbmcvfs.File(file_name, "wb")
        s = "{}".format(str(self.database.getCurrentChannelIdx(channel)))
        try:
            date = self.program.startDate
        except:
            program = self.database.getCurrentProgram(channel)
            date = program.startDate
        if sys.version_info[0] > 2:
            f.write('{},{}'.format(s, date))
        else:
            f.write(str('{},{}'.format(s, date)))
        f.close()

    def getLastChannel(self):
        return self.lastChannel

    def getCatchupDays(self):
        CatchupList = ''
        try:
            file_name = os.path.join(self.profilePath, 'catchup.list')
            f = xbmcvfs.File(file_name, 'r')
            CatchupList = f.read()
            f.close()
        except:
            CatchupList += ''

        return CatchupList

    def getPlaylist(self):
        ArchivePlaylistList = ''
        try:
            file_name = os.path.join(self.profilePath, 'playlist_ts.list')
            f = xbmcvfs.File(file_name, 'r')
            ArchivePlaylistList = f.read()
            f.close()
        except:
            ArchivePlaylistList += ''

        return ArchivePlaylistList

    def getCmore(self):
        ArchiveCmoreList = ''
        try:
            file_name = os.path.join(self.profilePath, 'cmore_ts.list')
            f = xbmcvfs.File(file_name, 'r')
            ArchiveCmoreList = f.read()
            f.close()
        except:
            ArchiveCmoreList += ''

        return ArchiveCmoreList

    def getPolsatGo(self):
        ArchiveCpGoList = ''
        try:
            file_name = os.path.join(self.profilePath, 'cpgo_ts.list')
            f = xbmcvfs.File(file_name, 'r')
            ArchiveCpGoList = f.read()
            f.close()
        except:
            ArchiveCpGoList += ''

        return ArchiveCpGoList

    def getIpla(self):
        ArchiveIplaList = ''
        try:
            file_name = os.path.join(self.profilePath, 'ipla_ts.list')
            f = xbmcvfs.File(file_name, 'r')
            ArchiveIplaList = f.read()
            f.close()
        except:
            ArchiveIplaList += ''

        return ArchiveIplaList

    #def getPlayerPL(self):
        #ArchivePlayerPLList = ''
        #try:
            #file_name = os.path.join(self.profilePath, 'playerpl_ts.list')
            #f = xbmcvfs.File(file_name, 'r')
            #ArchivePlayerPLList = f.read()
            #f.close()
        #except:
            #ArchivePlayerPLList += ''

        #return ArchivePlayerPLList

    def getTeliaPlay(self):
        ArchiveTeliaPlayList = ''
        try:
            file_name = os.path.join(self.profilePath, 'teliaplay_ts.list')
            f = xbmcvfs.File(file_name, 'r')
            ArchiveTeliaPlayList = f.read()
            f.close()
        except:
            ArchiveTeliaPlayList += ''

        return ArchiveTeliaPlayList

    def elapsed_interval(self, start, end):
        elapsed = end - start
        min, secs = divmod(elapsed.days * 86400 + elapsed.seconds, 60)
        hour, minutes = divmod(min, 60)
        return '%.2d:%.2d:%.2d' % (hour, minutes, secs)

    def playChannel2(self, program):
        deb('playChannel2')
        self.program = program

        # Playback for services
        try:
            ProgramEndDate = datetime.proxydt.strptime(str(self.program.endDate), '%Y-%m-%d %H:%M:%S')
            ProgramStartDate = datetime.proxydt.strptime(str(self.program.startDate), '%Y-%m-%d %H:%M:%S')
        except:
            ProgramEndDate = datetime.proxydt.strptime(str(datetime.datetime.now()), '%Y-%m-%d %H:%M:%S.%f')
            ProgramStartDate = datetime.proxydt.strptime(str(datetime.datetime.now()), '%Y-%m-%d %H:%M:%S.%f')

        try:
            ProgramNowDate = datetime.proxydt.strptime(str(datetime.datetime.now()), '%Y-%m-%d %H:%M:%S.%f')
        except:
            ProgramNowDate = datetime.proxydt.strptime(str(datetime.datetime.now()), '%Y-%m-%d %H:%M:%S')

        if ADDON.getSetting('archive_finished_program') == 'true':
            finishedProgram = ProgramEndDate
        else:
            finishedProgram = ProgramStartDate

        if self.catchupDays is not None:
            self.catchupDays = self.catchupDays
        else:
            self.catchupDays = ADDON.getSetting('archive_reverse_days')

        if ADDON.getSetting('archive_reverse_auto') == '0' and self.catchupDays != '' or self.catchupDays != '0':
            try:
                reverseTime = datetime.datetime.now() - datetime.timedelta(hours = int(self.catchupDays)) * 24 - datetime.timedelta(minutes = 5)
            except:
                reverseTime = datetime.datetime.now() - datetime.timedelta(hours = int(1)) * 24 - datetime.timedelta(minutes = 5)
        else:
            try:
                reverseTime = datetime.datetime.now() - datetime.timedelta(hours = int(ADDON.getSetting('archive_manual_days'))) * 24 - datetime.timedelta(minutes = 5)
            except:
                reverseTime = datetime.datetime.now() - datetime.timedelta(hours = int(1)) * 24 - datetime.timedelta(minutes = 5)
        
        reverseArchiveService = datetime.datetime.now() - datetime.timedelta(hours = int(3)) - datetime.timedelta(minutes = 5)

        try:
            if finishedProgram < datetime.datetime.now() and ADDON.getSetting('archive_support') == 'true':
                archiveList = self.getCmore() + self.getPolsatGo() + self.getIpla()# + self.getPlayerPL()
                archivePlaylist = self.getPlaylist() + self.getTeliaPlay()

                if (program.channel.title.upper() in archiveList and program.startDate > reverseArchiveService) or (program.channel.title.upper() in archivePlaylist and program.startDate > reverseTime):
                    res = xbmcgui.Dialog().yesno(strings(30998), strings(30999).format(program.title))

                    if res:
                        # archiveService
                        if ADDON.getSetting('archive_finished_program') == 'true': 
                            if program.channel.title.upper() in archiveList and program.endDate < datetime.datetime.now():
                                self.archiveService = datetime.datetime.now() - ProgramStartDate
                            else:
                                self.archiveService = ''
                        else:
                            if program.channel.title.upper() in archiveList and program.startDate < datetime.datetime.now():
                                self.archiveService = datetime.datetime.now() - ProgramStartDate
                            else:
                                self.archiveService = ''

                        if ADDON.getSetting('archive_finished_program') == 'true': 
                            if program.channel.title.upper() in archivePlaylist and program.endDate < datetime.datetime.now():
                                from time import mktime

                                n = datetime.datetime.now()
                                t = ProgramStartDate
                                e = ProgramEndDate

                                # Duration
                                durationCalc = int(((ProgramEndDate - ProgramStartDate).total_seconds() / 60.0))
                                duration = str(durationCalc)

                                # Offset
                                offsetCalc = int(((datetime.datetime.now() - ProgramStartDate).total_seconds() / 60.0))
                                offset = str(offsetCalc)

                                # UTC/LUTC
                                if sys.version_info[0] > 2:
                                    utc = str(int(datetime.datetime.timestamp(t)))
                                    lutc = str(int(datetime.datetime.timestamp(e)))
                                else:
                                    utc = str(int(time.mktime(t.timetuple())))
                                    lutc = str(int(time.mktime(e.timetuple())))

                                # Datestring
                                year = t.strftime("%Y")
                                month = t.strftime("%m")
                                day = t.strftime("%d")
                                hour = t.strftime("%H")
                                minute = t.strftime("%M")
                                second = t.strftime("%S")

                                self.archivePlaylist = '{duration}, {offset}, {utc}, {lutc}, {y}, {m}, {d}, {h}, {min}, {s}'.format(
                                    duration=duration, offset=offset, utc=utc, lutc=lutc, y=year, m=month, d=day, h=hour, min=minute, s=second)

                            else:
                                self.archivePlaylist = ''
                        else:
                            if program.channel.title.upper() in archivePlaylist and program.startDate < datetime.datetime.now():
                                from time import mktime

                                n = datetime.datetime.now()
                                t = ProgramStartDate
                                e = ProgramEndDate

                                # Duration
                                durationCalc = int(((ProgramEndDate - ProgramStartDate).total_seconds() / 60.0))
                                duration = str(durationCalc)

                                # Offset
                                offsetCalc = int(((datetime.datetime.now() - ProgramStartDate).total_seconds() / 60.0))
                                offset = str(offsetCalc)

                                # UTC/LUTC
                                if sys.version_info[0] > 2:
                                    utc = str(int(datetime.datetime.timestamp(t)))
                                    lutc = str(int(datetime.datetime.timestamp(e)))
                                else:
                                    utc = str(int(time.mktime(t.timetuple())))
                                    lutc = str(int(time.mktime(e.timetuple())))

                                # Datestring
                                year = t.strftime("%Y")
                                month = t.strftime("%m")
                                day = t.strftime("%d")
                                hour = t.strftime("%H")
                                minute = t.strftime("%M")
                                second = t.strftime("%S")

                                self.archivePlaylist = '{duration}, {offset}, {utc}, {lutc}, {y}, {m}, {d}, {h}, {min}, {s}'.format(
                                    duration=duration, offset=offset, utc=utc, lutc=lutc, y=year, m=month, d=day, h=hour, min=minute, s=second)

                            else:
                                self.archivePlaylist = ''

                    else:
                        if ADDON.getSetting('archive_finished_program') == 'false':
                            if ProgramEndDate > datetime.datetime.now():
                                self.archiveService = ''
                                self.archivePlaylist = ''
                            else:
                                return 'None'
                        else:
                            return 'None'

                else:
                    if self.program.channel.title.upper() in archivePlaylist and program.endDate < datetime.datetime.now():
                        self.recordProgram(self.program)
                        return 'None'
                    elif program.endDate > datetime.datetime.now():
                        self.archiveService = ''
                        self.archivePlaylist = ''
                    else:
                        xbmcgui.Dialog().ok(strings(30998), strings(59980))
                        return 'None'

            else:
                self.archiveService = ''
                self.archivePlaylist = ''

        except:
            self.archiveService = ''
            self.archivePlaylist = ''

        self.updateCurrentChannel(program.channel)
        if self.playRecordedProgram(program):
            return True

        urlList = self.database.getStreamUrlList(program.channel)
        if len(urlList) > 0:
            if ADDON.getSetting('start_video_minimalized') == 'false' and xbmc.Player().isPlaying():
                xbmc.executebuiltin("Action(FullScreen)")
            if ADDON.getSetting('info_osd') == "true":
                self.createOSD(self.program, urlList)
            else:
                self.playService.playUrlList(urlList, self.archiveService, self.archivePlaylist, resetReconnectCounter=True)
        return len(urlList) > 0

    def playChannel(self, channel, program=None):
        deb('playChannel')

        # Playback for services
        try:
            ProgramEndDate = datetime.proxydt.strptime(str(program.endDate), '%Y-%m-%d %H:%M:%S')
            ProgramStartDate = datetime.proxydt.strptime(str(program.startDate), '%Y-%m-%d %H:%M:%S')
        except:
            ProgramEndDate = datetime.proxydt.strptime(str(datetime.datetime.now()), '%Y-%m-%d %H:%M:%S.%f')
            ProgramStartDate = datetime.proxydt.strptime(str(datetime.datetime.now()), '%Y-%m-%d %H:%M:%S.%f')

        try:
            ProgramNowDate = datetime.proxydt.strptime(str(datetime.datetime.now()), '%Y-%m-%d %H:%M:%S.%f')
        except:
            ProgramNowDate = datetime.proxydt.strptime(str(datetime.datetime.now()), '%Y-%m-%d %H:%M:%S')

        if ADDON.getSetting('archive_finished_program') == 'true':
            finishedProgram = ProgramEndDate
        else:
            finishedProgram = ProgramStartDate

        if self.catchupDays is not None:
            self.catchupDays = self.catchupDays
        else:
            self.catchupDays = ADDON.getSetting('archive_reverse_days')

        if ADDON.getSetting('archive_reverse_auto') == '0' and self.catchupDays != '' or self.catchupDays != '0':
            try:
                reverseTime = datetime.datetime.now() - datetime.timedelta(hours = int(self.catchupDays)) * 24 - datetime.timedelta(minutes = 5)
            except:
                reverseTime = datetime.datetime.now() - datetime.timedelta(hours = int(1)) * 24 - datetime.timedelta(minutes = 5)
        else:
            try:
                reverseTime = datetime.datetime.now() - datetime.timedelta(hours = int(ADDON.getSetting('archive_manual_days'))) * 24 - datetime.timedelta(minutes = 5)
            except:
                reverseTime = datetime.datetime.now() - datetime.timedelta(hours = int(1)) * 24 - datetime.timedelta(minutes = 5)
        
        reverseArchiveService = datetime.datetime.now() - datetime.timedelta(hours = int(3)) - datetime.timedelta(minutes = 5)

        try:
            if finishedProgram < datetime.datetime.now() and ADDON.getSetting('archive_support') == 'true':
                archiveList = self.getCmore() + self.getPolsatGo() + self.getIpla()# + self.getPlayerPL()
                archivePlaylist = self.getPlaylist() + self.getTeliaPlay()

                if (program.channel.title.upper() in archiveList and program.startDate > reverseArchiveService) or (program.channel.title.upper() in archivePlaylist and program.startDate > reverseTime):
                    res = xbmcgui.Dialog().yesno(strings(30998), strings(30999).format(program.title))

                    if res:
                        # archiveService
                        if ADDON.getSetting('archive_finished_program') == 'true': 
                            if program.channel.title.upper() in archiveList and program.endDate < datetime.datetime.now():
                                self.archiveService = datetime.datetime.now() - ProgramStartDate
                            else:
                                self.archiveService = ''
                        else:
                            if program.channel.title.upper() in archiveList and program.startDate < datetime.datetime.now():
                                self.archiveService = datetime.datetime.now() - ProgramStartDate
                            else:
                                self.archiveService = ''

                        if ADDON.getSetting('archive_finished_program') == 'true': 
                            if program.channel.title.upper() in archivePlaylist and program.endDate < datetime.datetime.now():
                                from time import mktime

                                n = datetime.datetime.now()
                                t = ProgramStartDate
                                e = ProgramEndDate

                                # Duration
                                durationCalc = int(((ProgramEndDate - ProgramStartDate).total_seconds() / 60.0))
                                duration = str(durationCalc)

                                # Offset
                                offsetCalc = int(((datetime.datetime.now() - ProgramStartDate).total_seconds() / 60.0))
                                offset = str(offsetCalc)

                                # UTC/LUTC
                                if sys.version_info[0] > 2:
                                    utc = str(int(datetime.datetime.timestamp(t)))
                                    lutc = str(int(datetime.datetime.timestamp(e)))
                                else:
                                    utc = str(int(time.mktime(t.timetuple())))
                                    lutc = str(int(time.mktime(e.timetuple())))

                                # Datestring
                                year = t.strftime("%Y")
                                month = t.strftime("%m")
                                day = t.strftime("%d")
                                hour = t.strftime("%H")
                                minute = t.strftime("%M")
                                second = t.strftime("%S")

                                self.archivePlaylist = '{duration}, {offset}, {utc}, {lutc}, {y}, {m}, {d}, {h}, {min}, {s}'.format(
                                    duration=duration, offset=offset, utc=utc, lutc=lutc, y=year, m=month, d=day, h=hour, min=minute, s=second)

                            else:
                                self.archivePlaylist = ''
                        else:
                            if program.channel.title.upper() in archivePlaylist and program.startDate < datetime.datetime.now():
                                from time import mktime

                                n = datetime.datetime.now()
                                t = ProgramStartDate
                                e = ProgramEndDate

                                # Duration
                                durationCalc = int(((ProgramEndDate - ProgramStartDate).total_seconds() / 60.0))
                                duration = str(durationCalc)

                                # Offset
                                offsetCalc = int(((datetime.datetime.now() - ProgramStartDate).total_seconds() / 60.0))
                                offset = str(offsetCalc)

                                # UTC/LUTC
                                if sys.version_info[0] > 2:
                                    utc = str(int(datetime.datetime.timestamp(t)))
                                    lutc = str(int(datetime.datetime.timestamp(e)))
                                else:
                                    utc = str(int(time.mktime(t.timetuple())))
                                    lutc = str(int(time.mktime(e.timetuple())))
                                

                                # Datestring
                                year = t.strftime("%Y")
                                month = t.strftime("%m")
                                day = t.strftime("%d")
                                hour = t.strftime("%H")
                                minute = t.strftime("%M")
                                second = t.strftime("%S")

                                self.archivePlaylist = '{duration}, {offset}, {utc}, {lutc}, {y}, {m}, {d}, {h}, {min}, {s}'.format(
                                    duration=duration, offset=offset, utc=utc, lutc=lutc, y=year, m=month, d=day, h=hour, min=minute, s=second)

                            else:
                                self.archivePlaylist = ''

                    else:
                        if ADDON.getSetting('archive_finished_program') == 'false':
                            if ProgramEndDate > datetime.datetime.now():
                                self.archiveService = ''
                                self.archivePlaylist = ''
                            else:
                                return 'None'
                        else:
                            return 'None'

                else:
                    self.archiveService = ''
                    self.archivePlaylist = ''

        except:
            self.archiveService = ''
            self.archivePlaylist = ''

        self.updateCurrentChannel(channel)
        if program is not None:
            self.program = program
            if self.playRecordedProgram(program):
                return True

        urlList = self.database.getStreamUrlList(channel)
        if len(urlList) > 0:
            if ADDON.getSetting('start_video_minimalized') == 'false' and xbmc.Player().isPlaying():
                xbmc.executebuiltin("Action(FullScreen)")
            if ADDON.getSetting('info_osd') == "true":
                self.createOSD(self.program, urlList)
            else:
                self.playService.playUrlList(urlList, self.archiveService, self.archivePlaylist, resetReconnectCounter=True)
        return len(urlList) > 0

    def recordProgram(self, program, watch='', length=''):
        deb('recordProgram')
        if watch and length != '':
            if self.recordService.recordProgramGui(program, watch, length):
                self.onRedrawEPG(self.channelIdx, self.viewStartDate)
                self.playAndWatchRecordedProgram(program)
                
        else:
            if self.recordService.recordProgramGui(program):
                self.onRedrawEPG(self.channelIdx, self.viewStartDate)

    def waitForPlayBackStopped(self):
        debug('waitForPlayBackStopped')
        while self.epg.playService.isWorking() == True:
            xbmc.sleep(200)
        while (xbmc.Player().isPlaying() or self.epg.playService.isWorking() == True) and not strings2.M_TVGUIDE_CLOSING and not self.isClosing:
            xbmc.sleep(200)
        self.onPlayBackStopped()

    def _hideEpg(self):
        deb('_hideEpg')
        if ADDON.getSetting('touch_panel') == 'true':
            self._hideControl(self.C_MAIN_MOUSEPANEL_CONTROLS)
        self._hideControl(self.C_MAIN_EPG)
        self.mode = MODE_TV
        self._clearEpg()

    def _showEPG(self):
        deb('_showEpg')

        # aktualna godzina!
        try:
            self.viewStartDate = datetime.datetime.today() + datetime.timedelta(minutes=int(ADDON.getSetting('timebar_adjust')))
        except:
            self.viewStartDate = datetime.datetime.today() + datetime.timedelta(minutes=int(0))
        self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)
        if self.currentChannel is not None:
            currentChannelIndex = self.database.getCurrentChannelIdx(self.currentChannel)
            self.channelIdx = (currentChannelIndex // CHANNELS_PER_PAGE) * CHANNELS_PER_PAGE

        # przerysuj tylko wtedy gdy nie bylo epg! jak jest to nie przerysowuj - nie ustawi sie wtedy na aktualnej godzienie!
        if (self.mode == MODE_TV or self.redrawagain):
            self.onRedrawEPG(self.channelIdx, self.viewStartDate, self._getCurrentProgramFocus)  # przerysuj
        if ADDON.getSetting('touch_panel') == 'true':
            self._showControl(self.C_MAIN_MOUSEPANEL_CONTROLS)
                    
    def disableUnusedChannelControls(self, start_index):
        for idx in range(0, CHANNELS_PER_PAGE):
            self.disableControl(start_index + idx)

    def onRedrawEPG(self, channelStart, startTime, focusFunction=None, sourceUpdate=''):
        deb('onRedrawEPG')
        if self.redrawingEPG or (self.database is not None and self.database.updateInProgress) or self.isClosing or strings2.M_TVGUIDE_CLOSING:
            deb('onRedrawEPG - already redrawing')
            return  # ignore redraw request while redrawing
        self.redrawingEPG = True
        self.blockInputDueToRedrawing = True
        self.redrawagain = False
        self.mode = MODE_EPG

        if self.onFocusTimer:
            self.onFocusTimer.cancel()
        if self.infoDialog is not None:
            self.infoDialog.close()

        self._showControl(self.C_MAIN_EPG)
        self.updateTimebar(scheduleTimer=False)

        # remove existing controls
        self._clearEpg()
        try:
            self.channelIdx, channels, programs, cacheExpired = self.database.getEPGView(channelStart, startTime, self.onSourceProgressUpdate, clearExistingProgramList=True)
        except src.SourceException:
            self.blockInputDueToRedrawing = False
            debug('onRedrawEPG onEPGLoadError')
            self.onEPGLoadError()
            return

        if cacheExpired == True and ADDON.getSetting('notifications_enabled') == 'true':
            # make sure notifications are scheduled for newly downloaded programs
            self.notification.scheduleNotifications()

        # date and time row
        self.setControlLabel(self.C_MAIN_DATE, self.formatDate(self.viewStartDate))
        for col in range(1, 5):
            self.setControlLabel(4000 + col, self.formatTime(startTime))
            startTime += HALF_HOUR

        if programs is None:
            debug('onRedrawEPG onEPGLoadError2')
            self.onEPGLoadError()
            return

        categories = self.getCategories()

        if sourceUpdate == True:
            streams = self.getStreamsCid()

        for program in programs:
            idx = channels.index(program.channel)

            startDelta = program.startDate - self.viewStartDate
            stopDelta = program.endDate - self.viewStartDate

            cellStart = self._secondsToXposition(startDelta.seconds)
            if startDelta.days < 0:
                cellStart = self.epgView.left
            cellWidth = self._secondsToXposition(stopDelta.seconds) - cellStart
            if cellStart + cellWidth > self.epgView.right:
                cellWidth = self.epgView.right - cellStart
            if cellWidth > 1:

                if program.categoryA in categories['Movie']:
                    noFocusTexture = self.moviesTexture

                elif program.categoryA in categories['Series']:
                    noFocusTexture = self.seriesTexture

                elif program.categoryA in categories['Information']:
                    noFocusTexture = self.informationTexture

                elif program.categoryA in categories['Entertainment']:
                    noFocusTexture = self.entertainmentTexture

                elif program.categoryA in categories['Document']:
                    noFocusTexture = self.documentsTexture

                elif program.categoryA in categories['Kids']:
                    noFocusTexture = self.kidsTexture

                elif program.categoryA in categories['Sport']:
                    noFocusTexture = self.sportsTexture

                elif program.categoryA in categories['Interactive Entertainment']:
                    noFocusTexture = self.interactiveTexture
                else:
                    noFocusTexture = self.backgroundTexture

                if program.notificationScheduled:
                    if ADDON.getSetting('color_notifications') != '':
                        noFocusTexture = notifications_formatting(ADDON.getSetting('color_notifications'))
                    else:
                        ADDON.setSetting('color_notifications', '0')

                if program.recordingScheduled:
                    if ADDON.getSetting('color_recordings') != '':
                        noFocusTexture = recordings_formatting(ADDON.getSetting('color_recordings'))
                    else:
                        ADDON.setSetting('color_recordings', '0')

                if cellWidth < 35:
                    title = ''  # Text will overflow outside the button if it is too narrow
                else:
                    title = program.title

                archive = self.catchupEPG(program, cellWidth)

                control = xbmcgui.ControlButton(
                    cellStart,
                    self.epgView.top + self.epgView.cellHeight * idx,
                    cellWidth - (int(cell_width)),
                    self.epgView.cellHeight - (int(cell_height)),
                    archive + title,
                    noFocusTexture = noFocusTexture,
                    focusTexture = self.focusTexture,
                    font = skin_font,
                    textColor = skin_font_colour,
                    focusedColor = skin_font_focused_colour)

                self.controlAndProgramList.append(ControlAndProgram(control, program))

        # add program controls
        if focusFunction is None:
            focusFunction = self._findControlAt
        focusControl = focusFunction(self.focusPoint)
        if focusControl is None:
            focusControl = self._findControlAt(self.focusPoint)
        controls = [elem.control for elem in self.controlAndProgramList]
        self.addControls(controls)
        if focusControl is not None:
            self.setFocus(focusControl)
        self.ignoreMissingControlIds.extend([elem.control.getId() for elem in self.controlAndProgramList])
        if focusControl is None and len(self.controlAndProgramList) > 0:
            self.setFocus(self.controlAndProgramList[0].control)

        self._showControl(self.C_MAIN_LOADING_BACKGROUND)
        self._hideControl(self.C_MAIN_LOADING)

        self.blockInputDueToRedrawing = False

        if ADDON.getSetting('channel_shortcut') == 'true':
            channel_index_format = "%%0%sd" % 1
            show_channel_numbers = True
            CHANNEL_LABEL = self.C_CHANNEL_LABEL_START_INDEX_SHORTCUT
            CHANNEL_IMAGE = self.C_CHANNEL_IMAGE_START_INDEX_SHORTCUT
        else:
            show_channel_numbers = False
            CHANNEL_LABEL = self.C_CHANNEL_LABEL_START_INDEX
            CHANNEL_IMAGE = self.C_CHANNEL_IMAGE_START_INDEX

        if ADDON.getSetting('show_logo') == 'true':
            show_channel_logo = True
        else:
            show_channel_logo = False

        # set channel logo or text
        for idx in range(0, CHANNELS_PER_PAGE):
            if idx % 2 == 0 and not self.dontBlockOnAction:
                xbmc.sleep(20)  # Fix for ocasional gui freeze during quick scrolling

            if idx >= len(channels):
                # Clear remaining channels
                self.setControlImage(CHANNEL_IMAGE + idx, ' ')
                self.setControlLabel(CHANNEL_LABEL + idx, ' ')
                if show_channel_numbers:
                    self.setControlLabel(self.C_CHANNEL_NUMBER_START_INDEX_SHORTCUT + idx, ' ')

            else:
                channel = channels[idx]
                self.setControlLabel(CHANNEL_LABEL + idx, channel.title)

                if show_channel_numbers:
                    self.setControlLabel(self.C_CHANNEL_NUMBER_START_INDEX_SHORTCUT + idx, channel_index_format % (self.channelIdx + idx + 1))

                if show_channel_logo:
                    if channel.logo is not None:
                        self.setControlImage(CHANNEL_IMAGE + idx, channel.logo)
                    else:
                        self.setControlImage(CHANNEL_IMAGE + idx, ' ')

                    self.a[idx] = channel

        # Redraw timebar
        addonSkin = ADDON.getSetting('Skin')

         # Addon
        if xbmcvfs.exists(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, 'xml', 'script-tvguide-main.xml')):
            x = 'xml'
        elif xbmcvfs.exists(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, '720p', 'script-tvguide-main.xml')):
            x = '720p'
        elif xbmcvfs.exists(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, '1080i', 'script-tvguide-main.xml')):
            x = '1080i'
        elif xbmcvfs.exists(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, '16x9', 'script-tvguide-main.xml')):
            x = '16x9'
        else:
            x = '16x9'

        # TimebarBack Color
        try:
            f = xbmcvfs.File(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, x, 'script-tvguide-main.xml'), 'r')
            line = f.read()

            matchAddon = re.findall('<texture colordiffuse="(.*?)">osd/back.png</texture>', str(line))
        except:
            None

        try:
            f = xbmcvfs.File(os.path.join(self.kodiSkinPath, 'colors', 'defaults.xml'), 'r')
            line = f.read()

            matchKodi = re.findall('<color name="'+matchAddon[0]+'">(.*?)</color>', str(line))
            resBack = matchKodi[0]

        except:
            try:
                resBack = matchAddon[0]
            except:
                resBack = ''

        try:
            colorTimebarBack = resBack
        except:
            colorTimebarBack = ''

        # Timebar Color
        try:
            f = xbmcvfs.File(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, x, 'script-tvguide-main.xml'), 'r')
            line = f.read()

            matchAddon = re.findall('<texture colordiffuse="(.*?)">tvguide-timebar.png</texture>', str(line))
        except:
            None

        try:
            f = xbmcvfs.File(os.path.join(self.kodiSkinPath, 'colors', 'defaults.xml'), 'r')
            line = f.read()

            matchKodi = re.findall('<color name="'+matchAddon[0]+'">(.*?)</color>', str(line))
            resBar = matchKodi[0]

        except:
            try:
                resBar = matchAddon[0]
            except:
                resBack = ''

        try:
            colorTimebar = resBar
        except:
            colorTimebar = ''

        tmp_background = self.getControl(self.C_MAIN_TIMEBAR_BACK)
        if self.timebarBack:
            self.removeControl(self.timebarBack)

        tmp_control = self.getControl(self.C_MAIN_TIMEBAR)
        if self.timebar:
            self.removeControl(self.timebar)

        if self.getControl(self.C_DYNAMIC_COLORS):
            self.timebarBack = xbmcgui.ControlImage(tmp_background.getX(), tmp_background.getY(), tmp_background.getWidth(), tmp_background.getHeight(), os.path.join(Skin.getSkinPath(), 'media', 'osd', 'back.png'), colorDiffuse=colorTimebarBack)
        else:
            self.timebarBack = xbmcgui.ControlImage(tmp_background.getX(), tmp_background.getY(), tmp_background.getWidth(), tmp_background.getHeight(), os.path.join(Skin.getSkinPath(), 'media', 'osd', 'back.png'), colorDiffuse=skin_timebarback_colour)

        if self.getControl(self.C_DYNAMIC_COLORS):
            self.timebar = xbmcgui.ControlImage(tmp_control.getX(), tmp_control.getY(), tmp_control.getWidth(), tmp_control.getHeight(), os.path.join(Skin.getSkinPath(), 'media', 'tvguide-timebar.png'), colorDiffuse=colorTimebar)
        else:
            self.timebar = xbmcgui.ControlImage(tmp_control.getX(), tmp_control.getY(), tmp_control.getWidth(), tmp_control.getHeight(), os.path.join(Skin.getSkinPath(), 'media', 'tvguide-timebar.png'), colorDiffuse=skin_timebar_colour)
        
        timebars = [self.timebar, self.timebarBack]
        self.addControls(timebars)
        
        self.updateTimebar()

        self.getListLenght = self.getChannelListLenght()

        self.redrawingEPG = False
        if self.redrawagain:
            debug('onRedrawEPG redrawing again')
            self.redrawagain = False
            self.onRedrawEPG(channelStart, self.viewStartDate, focusFunction)
        debug('onRedrawEPG done')

    def _clearEpg(self):
        deb('_clearEpg')  
        try:   
            controls = [elem.control for elem in self.controlAndProgramList]
            try:
                self.removeControls(controls)
            except:
                debug('_clearEpg failed to delete all controls, deleting one by one')
                for elem in self.controlAndProgramList:
                    try:
                        self.removeControl(elem.control)

                    except RuntimeError as ex:
                        debug('_clearEpg RuntimeError: {}'.format(getExceptionString()))
                        pass  # happens if we try to remove a control that doesn't exist

                    except Exception as ex:
                        deb('_clearEpg unhandled exception: {}'.format(getExceptionString()))

            try:
                if self.timebar:
                    self.removeControl(self.timebar)
                    self.timebar = None

                if self.timebarBack:
                    self.removeControl(self.timebarBack)
                    self.timebarBack = None
            except:
                pass

            try:
                self.category = self.database.category
                if sys.version_info[0] < 3:
                    self.category = self.category.decode('utf-8', 'replace')
                self.categories = self.database.getAllCategories()
            except:
                pass

            try:
                listControl = self.getControl(self.C_MAIN_CATEGORY)
                listControl.reset()

                items = list()

                ccList = ['be', 'cz', 'de', 'dk', 'fr', 'hr', 'it', 'no', 'pl', 'se', 'srb', 'uk', 'us', 'radio']
                
                categories = PREDEFINED_CATEGORIES + sorted(list(self.categories), key=lambda x: x.lower())
                for item in ccList:
                    if ADDON.getSetting('country_code_{cc}'.format(cc=item)) == "false":
                        categories.remove('Group: {cc}'.format(cc=item.upper()))

                categories = [label.replace('Group', strings(30995)) for label in categories]

                for label in categories:
                    item = xbmcgui.ListItem(label)
                    items.append(item)

                listControl.addItems(items)
                if self.category and self.category in categories:
                    index = categories.index(self.category)
                    if index >= 0:
                        listControl.selectItem(index)
            except:
                deb('Categories not supported by current skin')
                self.category = None


            del self.controlAndProgramList[:]
            debug('_clearEpg end')

        except:
            debug('_clearEpg can´t clear')
            pass

    def onEPGLoadError(self):
        deb('onEPGLoadError, M_TVGUIDE_CLOSING: {}'.format(strings2.M_TVGUIDE_CLOSING))
        self.redrawingEPG = False
        self._hideControl(self.C_MAIN_LOADING)
        if not strings2.M_TVGUIDE_CLOSING:
            xbmcgui.Dialog().ok(strings(LOAD_ERROR_TITLE), strings(LOAD_ERROR_LINE1) + '\n' + ADDON.getSetting('m-TVGuide').strip() + strings(LOAD_ERROR_LINE2))
        self.close()

    def onSourceNotConfigured(self):
        deb('onSourceNotConfigured')
        self.redrawingEPG = False
        self._hideControl(self.C_MAIN_LOADING)
        xbmcgui.Dialog().ok(strings(LOAD_ERROR_TITLE), strings(LOAD_ERROR_LINE1) + strings(CONFIGURATION_ERROR_LINE2) + '\n' + strings(69036) + ADDON.getSetting('m-TVGuide').strip())
        self.close()

    def isSourceInitializationCancelled(self):
        initialization_cancelled = strings2.M_TVGUIDE_CLOSING or self.isClosing
        deb('isSourceInitializationCancelled: {}'.format(initialization_cancelled))
        return initialization_cancelled

    def onSourceInitialized(self, success):
        deb('onSourceInitialized')

        if success:
            self.notification = Notification(self.database, ADDON.getAddonInfo('path'), self)
            if ADDON.getSetting('notifications_enabled') == 'true':
                self.notification.scheduleNotifications()
            self.recordService.scheduleAllRecordings()
            self.rssFeed = src.RssFeed(url=RSS_FILE, last_message=self.database.getLastRssDate(), update_date_call=self.database.updateRssDate)

            if strings2.M_TVGUIDE_CLOSING == False:

                if ADDON.getSetting('channel_shortcut') == 'true':
                    self.disableUnusedChannelControls(self.C_CHANNEL_LABEL_START_INDEX)
                    self.disableUnusedChannelControls(self.C_CHANNEL_IMAGE_START_INDEX)
                else:
                    self.disableUnusedChannelControls(self.C_CHANNEL_LABEL_START_INDEX_SHORTCUT)
                    self.disableUnusedChannelControls(self.C_CHANNEL_IMAGE_START_INDEX_SHORTCUT)
                    self.disableUnusedChannelControls(self.C_CHANNEL_NUMBER_START_INDEX_SHORTCUT)

                if ADDON.getSetting('categories_remember') == 'true' or ADDON.getSetting('category') != '':
                    self.database.setCategory(ADDON.getSetting('category'))

                self.onRedrawEPG(0, self.viewStartDate, sourceUpdate=True)
                
                if ADDON.getSetting('touch_panel') == 'true':
                    self._showControl(self.C_MAIN_MOUSEPANEL_CONTROLS)

        else:
            self.close()

        if ADDON.getSetting('autostart_channel') == 'true':
            if ADDON.getSetting('autostart_channel_last') == 'true':
                try:
                    self.AutoPlayLastChannel()
                except ValueError:
                    self.AutoPlayByNumber()

            elif ADDON.getSetting('autostart_channel_number') != None:
                self.AutoPlayByNumber()

    def onSourceProgressUpdate(self, percentageComplete, additionalMessage=""):
        if additionalMessage != "":
            self.setControlLabel(self.C_MAIN_LOADING_TIME_LEFT, additionalMessage)
            return not strings2.M_TVGUIDE_CLOSING and not self.isClosing

        deb('onSourceProgressUpdate')
        control = self.getControl(self.C_MAIN_LOADING_PROGRESS)
        if percentageComplete < 1:
            if control:
                control.setPercent(1)
            self.progressStartTime = datetime.datetime.now()
            self.progressPreviousPercentage = percentageComplete

            # show Loading screen
            self.setControlLabel(self.C_MAIN_LOADING_TIME_LEFT, strings(CALCULATING_REMAINING_TIME))
            self._showControl(self.C_MAIN_LOADING)
            self.setFocusId(self.C_MAIN_LOADING_CANCEL)

        elif percentageComplete >= 100:
            if control:
                control.setPercent(100)
            self.progressStartTime = datetime.datetime.now()
            self.progressPreviousPercentage = 100
        elif percentageComplete != self.progressPreviousPercentage:
            if control:
                control.setPercent(percentageComplete)
            self.progressPreviousPercentage = percentageComplete
            delta = datetime.datetime.now() - self.progressStartTime

            if percentageComplete < 20:
                self.setControlLabel(self.C_MAIN_LOADING_TIME_LEFT, strings(CALCULATING_REMAINING_TIME))
            else:
                secondsLeft = int(delta.seconds) / float(percentageComplete) * (100.0 - percentageComplete)
                if secondsLeft > 30:
                    secondsLeft -= secondsLeft % float(10)

                self.setControlLabel(self.C_MAIN_LOADING_TIME_LEFT, strings(TIME_LEFT).format(int(secondsLeft)))

        return not strings2.M_TVGUIDE_CLOSING and not self.isClosing

    def onPlayBackStopped(self):
        deb('onPlayBackStopped')
        if not xbmc.Player().isPlaying() and not self.isClosing:
            self.viewStartDate = datetime.datetime.today() + datetime.timedelta(minutes=int(ADDON.getSetting('timebar_adjust')))
            self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)
            self.onRedrawEPG(self.channelIdx, self.viewStartDate, self._getCurrentProgramFocus)

    def _secondsToXposition(self, seconds):
        # deb('_secondsToXposition')
        return self.epgView.left + (seconds * self.epgView.width // 7200)

    def _findControlOnRight(self, point):
        # debug('_findControlOnRight')
        distanceToNearest = 10000
        nearestControl = None

        for elem in self.controlAndProgramList:
            control = elem.control
            (left, top) = control.getPosition()
            x = left + (control.getWidth() // 2)
            y = top + (control.getHeight() // 2)

            if point.x < x and point.y == y:
                distance = abs(point.x - x)
                if distance < distanceToNearest:
                    distanceToNearest = distance
                    nearestControl = control

        return nearestControl

    def _findControlOnLeft(self, point):
        # debug('_findControlOnLeft')
        distanceToNearest = 10000
        nearestControl = None

        for elem in self.controlAndProgramList:
            control = elem.control
            (left, top) = control.getPosition()
            x = left + (control.getWidth() // 2)
            y = top + (control.getHeight() // 2)

            if point.x > x and point.y == y:
                distance = abs(point.x - x)
                if distance < distanceToNearest:
                    distanceToNearest = distance
                    nearestControl = control

        return nearestControl

    def _findControlBelow(self, point):
        # debug('_findControlBelow')
        if self.getChannelNumber() == self.getListLenght:
            nearestControl = self.getControl(self.C_MAIN_CATEGORY)
        else:
            nearestControl = None

        for elem in self.controlAndProgramList:
            control = elem.control
            (leftEdge, top) = control.getPosition()
            y = top + (control.getHeight() // 2)

            if point.y < y:
                rightEdge = leftEdge + control.getWidth()
                if (leftEdge <= point.x < rightEdge and (nearestControl is None or nearestControl.getPosition()[1] > top)):
                    nearestControl = control

        return nearestControl

    def _findControlAbove(self, point):
        # debug('_findControlAbove')
        if self.getChannelNumber() == 1:
            nearestControl = self.getControl(self.C_MAIN_CATEGORY)
        else:
            nearestControl = None

        for elem in self.controlAndProgramList:
            control = elem.control
            (leftEdge, top) = control.getPosition()
            y = top + (control.getHeight() // 2)

            if point.y > y:
                rightEdge = leftEdge + control.getWidth()
                if (leftEdge <= point.x < rightEdge and (nearestControl is None or nearestControl.getPosition()[1] < top)):
                    nearestControl = control

        return nearestControl

    def _findControlAt(self, point):
        debug('_findControlAt')
        for elem in self.controlAndProgramList:
            control = elem.control
            (left, top) = control.getPosition()
            bottom = top + control.getHeight()
            right = left + control.getWidth()

            if left <= point.x <= right and top <= point.y <= bottom:
                return control

        return None

    def _getProgramFromControl(self, control):
        # deb('_getProgramFromControl')
        try:
            if control is not None:
                for elem in self.controlAndProgramList:
                    if elem.control.getId() == control.getId():
                        return elem.program
        except Exception as ex:
            deb('_getProgramFromControl Error: {}'.format(getExceptionString()))
            raise
        return None

    def _getCurrentProgramFocus(self, point=None):
        try:
            if self.currentChannel:
                program = self.database.getCurrentProgram(self.currentChannel)
                if program is not None:
                    for elem in self.controlAndProgramList:
                        if elem.program.channel.id == program.channel.id and elem.program.startDate == program.startDate:
                            return elem.control
        except:
            pass
        return None

    def _getProgramFocus(self, channel, point=None):
        try:
            program = self.database.getCurrentProgram(channel)
            if program is not None:
                for elem in self.controlAndProgramList:
                    if elem.program.channel.id == program.channel.id and elem.program.startDate == program.startDate:
                        return elem.control
        except:
            pass
        return None

    def _hideControl(self, *controlIds):
        deb('_hideControl')
        """
        Visibility is inverted in skin
        """
        for controlId in controlIds:
            control = self.getControl(controlId)
            if control:
                control.setVisible(True)

    def _showControl(self, *controlIds):
        debug('_showControl')
        """
        Visibility is inverted in skin
        """
        for controlId in controlIds:
            control = self.getControl(controlId)
            if control:
                control.setVisible(False)

    def disableControl(self, controlId):
        # debug('disableControl {}'.format(controlId))
        control = self.getControl(controlId)
        if control:
            control.setVisible(False)
            control.setEnabled(False)

    def convertTimedelta(self, duration):
        days, seconds = duration.days, duration.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = (seconds % 60)
        return minutes

    def formatTime(self, timestamp):
        # debug('formatTime')
        format = xbmc.getRegion('time').replace(':%S', '').replace('%H%H', '%H')
        return timestamp.strftime(format)

    def formatDate(self, timestamp):
        debug('formatDate')
        format = xbmc.getRegion('dateshort')
        return timestamp.strftime(format)

    def setControlImage(self, controlId, image):
        #debug('setControlImage: {}'.format(image))
        control = self.getControl(controlId)
        try:
            control.setImage(image, True)
        except:
            pass

    def setControlLabel(self, controlId, label):
        #debug('setControlLabel: {}'.format(label))
        control = self.getControl(controlId)
        try:
            control.setLabel(label)
        except:
            pass

    def setControlText(self, controlId, text):
        #debug('setControlText: {}'.format(text))
        control = self.getControl(controlId)
        try:
            control.setText(text)
        except:
            pass

    def updateTimebar(self, scheduleTimer=True):
        # debug('updateTimebar')

        if xbmc.Player().isPlaying():
            self.lastKeystroke = datetime.datetime.now()
        try:
            # move timebar to current time
            timeDelta = datetime.datetime.today() - self.viewStartDate + datetime.timedelta(minutes=int(ADDON.getSetting('timebar_adjust')))
            control = self.getControl(self.C_MAIN_TIMEBAR)

            timeDeltaBg = datetime.datetime.today() - self.viewStartDate + datetime.timedelta(minutes=int(ADDON.getSetting('timebar_adjust')))
            background = self.getControl(self.C_MAIN_TIMEBAR_BACK)

            if control and background:
                (x, y) = control.getPosition()
                w = background.getWidth()
                (x, y) = background.getPosition()
                try:
                    # Sometimes raises:
                    # exceptions.RuntimeError: Unknown exception thrown from the call "setVisible"
                    control.setVisible(timeDelta.days == 0)
                    background.setVisible(timeDelta.days == 0)
                except:
                    pass

                xPositionBar = self._secondsToXposition(timeDelta.seconds)
                control.setPosition(xPositionBar, y)
                if self.timebar:
                    self.timebar.setPosition(xPositionBar, y)

                if self.viewStartDate.date() == self.lastKeystroke.date():
                    xPositionBar = self._secondsToXposition(timeDelta.seconds)
                    
                    marker = self.getControl(self.C_MAIN_EPG_VIEW_MARKER)
                    p = marker.getWidth()
                    
                    if self.timebarBack:
                        background.setWidth(xPositionBar - x + 13)
                        self.timebarBack.setWidth(xPositionBar - x + 13)

                    if xPositionBar > (self.epgView.left + ((self.epgView.right - self.epgView.left) * 0.8)):
                        # Time bar exceeded EPG
                        # Check how long was since EPG was used
                        background.setWidth(p - int(cell_width))
                        self.timebarBack.setWidth(p - int(cell_width))

                        diff = datetime.datetime.now() - self.lastKeystroke
                        diffSeconds = (diff.days * 86400) + diff.seconds
                        debug('updateTimebar seconds since last user action {}'.format(diffSeconds))
                        if diffSeconds > 300:
                            deb('updateTimebar redrawing EPG start')
                            self.lastKeystroke = datetime.datetime.now()
                            self.viewStartDate = datetime.datetime.today()
                            self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)
                            self.onRedrawEPG(self.channelIdx, self.viewStartDate, self._getCurrentProgramFocus)
                            debug('updateTimebar redrawing EPG end')

                else:
                    marker = self.getControl(self.C_MAIN_EPG_VIEW_MARKER)
                    p = marker.getWidth()
                    self.timebarBack.setWidth(p - int(cell_width))
                    diff = datetime.datetime.now() - self.lastKeystroke
                    diffSeconds = (diff.days * 86400) + diff.seconds
                    debug('updateTimebar seconds since last user action {}'.format(diffSeconds))
                    if diffSeconds > 300:
                        deb('updateTimebar redrawing EPG start')
                        self.lastKeystroke = datetime.datetime.now()
                        self.viewStartDate = datetime.datetime.today()
                        self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)
                        self.onRedrawEPG(self.channelIdx, self.viewStartDate, self._getCurrentProgramFocus)
                        debug('updateTimebar redrawing EPG end')

                try:
                    # Sometimes raises:
                    # exceptions.RuntimeError: Unknown exception thrown from the call "setVisible"
                    if self.lastKeystroke < self.viewStartDate:
                        self.timebarBack.setVisible(True)
                        
                    if self.viewStartDate > self.lastKeystroke:
                        self.timebarBack.setVisible(False)

                    if self.viewStartDate.date() == self.lastKeystroke.date():
                        self.timebar.setVisible(True)
                    else:
                        self.timebar.setVisible(False)

                    if not xbmc.getCondVisibility('!Control.IsVisible(5000)'):
                        self.timebarBack.setVisible(False)
                        self.timebar.setVisible(False)
                except:
                    pass

            if scheduleTimer and not strings2.M_TVGUIDE_CLOSING and not self.isClosing:
                if self.updateTimebarTimer is not None:
                    self.updateTimebarTimer.cancel()
                self.updateTimebarTimer = threading.Timer(20, self.updateTimebar)
                self.updateTimebarTimer.start()
        except Exception:
            pass

    def refreshStreamsLoop(self):
        if self.autoUpdateCid == 'true':
            refreshTime = REFRESH_STREAMS_TIME
            if not strings2.M_TVGUIDE_CLOSING and not self.isClosing and self.database and self.recordService and self.playService and not self.recordService.isRecordOngoing() and not xbmc.Player().isPlaying() and not self.playService.isWorking() and self.checkUrl():
                if datetime.datetime.now().hour < 8:
                    refreshTime = 3600
                else:
                    diff = datetime.datetime.now() - self.lastKeystroke
                    diffSeconds = (diff.days * 86400) + diff.seconds
                    if diffSeconds > 60:
                        deb('refreshStreamsLoop refreshing all services')
                        self.database.reloadServices()
                        self.onRedrawEPG(self.channelIdx, self.viewStartDate, self._getCurrentProgramFocus)
                    else:
                        deb(
                            'refreshStreamsLoop services will be refreshed if no activity for 60s, currently no activity for {} seconds'.format(
                                diffSeconds))
                        refreshTime = 60
            else:
                refreshTime = 600
                deb('refreshStreamsLoop delaying service refresh for {} seconds due to playback or record'.format(
                    refreshTime))

            if not strings2.M_TVGUIDE_CLOSING and not self.isClosing:
                self.refreshStreamsTimer = threading.Timer(refreshTime, self.refreshStreamsLoop)
                self.refreshStreamsTimer.start()
        else:
            self.refreshStreamsTimer = None

    def checkUrl(slef, url='http://www.google.com'):
        if sys.version_info[0] > 2:
            try:
                import urllib.request, urllib.error, urllib.parse
                open = urllib.request.urlopen(url, timeout=3)
                if (open):
                    open.read()
                    return True
            except:
                pass
            return False
        else:
            try:
                import urllib2
                open = urllib2.urlopen(url, timeout = 3)
                if(open):
                    open.read()
                    return True
            except:
                pass
            return False


class PopupMenu(xbmcgui.WindowXMLDialog):
    C_POPUP_PLAY = 4000
    C_POPUP_CHOOSE_STREAM = 4001
    C_POPUP_REMIND = 4002
    C_POPUP_CHANNELS = 4003
    C_POPUP_QUIT = 4004
    C_POPUP_RECORDINGS = 4006
    C_POPUP_RECORD = 4007
    C_POPUP_INFO = 4008
    C_POPUP_LISTS = 4009
    C_POPUP_NUMBER = 4010
    C_POPUP_EXTENDED = 4011
    C_POPUP_CHANNEL_LOGO = 4100
    C_POPUP_CHANNEL_TITLE = 4101
    C_POPUP_PROGRAM_TITLE = 4102
    C_POPUP_PROGRAM_TIME_RANGE = 4103
    C_POPUP_ADDON_SETTINGS = 4110
    C_POPUP_CATEGORY = 7004
    C_POPUP_FAQ = 4013
    C_POPUP_FAVOURITES = 4014
    C_POPUP_ADD_CHANNEL = 4015

    LABEL_CHOOSE_STRM = CHOOSE_STRM_FILE

    def __new__(cls, database, program, showRemind):
        return super(PopupMenu, cls).__new__(cls, 'script-tvguide-menu.xml', Skin.getSkinBasePath(), Skin.getSkinName(), skin_resolution)

    def __init__(self, database, program, showRemind):
        """

        @type database: source.Database
        @param program:
        @type program: source.Program
        @param showRemind:
        """
        super(PopupMenu, self).__init__()
        self.database = database
        self.program = program
        self.showRemind = showRemind
        self.buttonClicked = None
        self.category = self.database.category
        self.categories = self.database.getAllCategories()

    def onInit(self):
        playControl = self.getControl(self.C_POPUP_PLAY)
        remindControl = self.getControl(self.C_POPUP_REMIND)
        channelLogoControl = self.getControl(self.C_POPUP_CHANNEL_LOGO)
        channelTitleControl = self.getControl(self.C_POPUP_CHANNEL_TITLE)
        programTitleControl = self.getControl(self.C_POPUP_PROGRAM_TITLE)
        chooseStrmControl = self.getControl(self.C_POPUP_CHOOSE_STREAM)
        programTimeRangeControl = self.getControl(self.C_POPUP_PROGRAM_TIME_RANGE)
        programRecordControl = self.getControl(self.C_POPUP_RECORD)

        try:
            listControl = self.getControl(self.C_POPUP_CATEGORY)

            items = list()

            ccList = ['be', 'cz', 'de', 'dk', 'fr', 'hr', 'it', 'no', 'pl', 'se', 'srb', 'uk', 'us', 'radio']

            categories = PREDEFINED_CATEGORIES + sorted(list(self.categories), key=lambda x: x.lower())
            for item in ccList:
                if ADDON.getSetting('country_code_{cc}'.format(cc=item)) == "false":
                    categories.remove('Group: {cc}'.format(cc=item.upper()))

            categories = [label.replace('Group', strings(30995)) for label in categories]

            for label in categories:
                item = xbmcgui.ListItem(label)
                items.append(item)

            listControl.addItems(items)
            if self.category and self.category in categories:
                index = categories.index(self.category)
                if index >= 0:
                    listControl.selectItem(index)
        except:
            deb('Categories not supported by current skin')
            self.category = None

        playControl.setLabel(strings(WATCH_CHANNEL, self.program.channel.title))
        if not self.program.channel.isPlayable():
            playControl.setEnabled(False)
            self.setFocusId(self.C_POPUP_NUMBER)

        self.LABEL_CHOOSE_STRM = getStateLabel(chooseStrmControl, 0, CHOOSE_STRM_FILE)
        LABEL_REMOVE_STRM = getStateLabel(chooseStrmControl, 1, REMOVE_STRM_FILE)
        LABEL_REMIND = getStateLabel(remindControl, 0, REMIND_PROGRAM)
        LABEL_DONT_REMIND = getStateLabel(remindControl, 1, DONT_REMIND_PROGRAM)

        if self.database.getCustomStreamUrl(self.program.channel):
            chooseStrmControl.setLabel(strings(LABEL_REMOVE_STRM))
        else:
            chooseStrmControl.setLabel(strings(self.LABEL_CHOOSE_STRM))

        if self.program.channel.logo is not None:
            channelLogoControl.setImage(self.program.channel.logo)
            channelTitleControl.setVisible(False)
        else:
            channelTitleControl.setLabel(self.program.channel.title)
            channelLogoControl.setVisible(False)

        programTitleControl.setLabel(self.program.title)

        if self.showRemind:
            remindControl.setLabel(strings(LABEL_REMIND))
        else:
            remindControl.setLabel(strings(LABEL_DONT_REMIND))

        if self.program.endDate < datetime.datetime.now():
            if self.program.recordingScheduled:
                programRecordControl.setLabel(strings(DOWNLOAD_PROGRAM_CANCEL_STRING))
            else:
                programRecordControl.setLabel(strings(DOWNLOAD_PROGRAM_STRING))
        else:
            if self.program.recordingScheduled:
                programRecordControl.setLabel(strings(RECORD_PROGRAM_CANCEL_STRING))
            else:
                programRecordControl.setLabel(strings(RECORD_PROGRAM_STRING))

        if programTimeRangeControl is not None:
            programTimeRangeControl.setLabel('{} - {}'.format(self.formatTime(self.program.startDate), self.formatTime(self.program.endDate)))

    def onAction(self, action):
        if action.getId() in [ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, KEY_NAV_BACK]:
            self.close()
            return

        elif action.getId() in [KEY_CONTEXT_MENU] and xbmc.getCondVisibility('!Control.HasFocus(7004)'):
            self.close()
            return

        elif action.getId() in [KEY_CONTEXT_MENU] and xbmc.getCondVisibility('Control.HasFocus(7004)'):
            cList = self.getControl(self.C_POPUP_CATEGORY)
            label = cList.getSelectedItem().getLabel()
            match = re.search(r'\w+: ([^\s]*)', label)

            if match or cList.getSelectedPosition() == 0:
                return

            item = cList.getSelectedItem()
            if item:
                self.category = item.getLabel()
                if sys.version_info[0] < 3:
                    self.category = self.category.decode('utf-8')

            dialog = xbmcgui.Dialog()
            ret = dialog.select(self.category, (strings(30985), strings(30986), strings(30987)))

            if ret < 0:
                return

            categories = {}
            categories[self.category] = []
            for name, cat in self.database.getCategoryMap():
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(name)

            if ret == 0:
                channelList = sorted([channel.title for channel in self.database.getChannelList(onlyVisible=True, customCategory=self.category, excludeCurrentCategory=True)])
                string = strings(30989).format(self.category)
                ret = dialog.multiselect(string, channelList)
                if ret is None:
                    return
                if not ret:
                    ret = []
                channels = []
                for i in ret:
                    channels.append(channelList[i])

                for channel in channels:
                    if channel not in categories[self.category]:
                        categories[self.category].append(channel)

            elif ret == 1:
                channelList = sorted([channel.title for channel in self.database.getChannelList(onlyVisible=True, customCategory=self.category)])
                string = strings(30990).format(self.category)
                ret = dialog.multiselect(string, channelList)
                if ret is None:
                    return
                if not ret:
                    ret = []
                channels = []
                for i in ret:
                    channelList[i] = ""
                categories[self.category] = []
                for name in channelList:
                    if name:
                        categories[self.category].append(name)

            elif ret == 2:
                categories[self.category] = []

            self.database.saveCategoryMap(categories)
            self.categories = [category for category in categories if category]
            self.buttonClicked = self.C_POPUP_CATEGORY

    def onClick(self, controlId):
        if controlId == self.C_POPUP_CHOOSE_STREAM and self.database.getCustomStreamUrl(self.program.channel):
            self.database.deleteCustomStreamUrl(self.program.channel)
            chooseStrmControl = self.getControl(self.C_POPUP_CHOOSE_STREAM)
            chooseStrmControl.setLabel(strings(self.LABEL_CHOOSE_STRM))

            if not self.program.channel.isPlayable():
                playControl = self.getControl(self.C_POPUP_PLAY)
                playControl.setEnabled(False)

        elif controlId == self.C_POPUP_CATEGORY:
            cList = self.getControl(self.C_POPUP_CATEGORY)
            if cList.getSelectedPosition() == 0:
                self.category = None
            else:
                item = cList.getSelectedItem()
                if item:
                    self.category = item.getLabel()
                    if sys.version_info[0] < 3:
                        self.category = self.category.decode('utf-8')
            self.buttonClicked = controlId
            self.close()
        elif controlId == 4012:
            dialog = xbmcgui.Dialog()
            cat = dialog.input(strings(30984), type=xbmcgui.INPUT_ALPHANUM)
            if cat:
                categories = set(self.categories)
                if sys.version_info[0] > 2:
                    categories.add(cat)
                else:
                    categories.add(cat.decode('utf-8'))
                self.categories = list(set(categories))
                items = list()
                categories = PREDEFINED_CATEGORIES + sorted(list(self.categories), key=lambda x: x.lower())
                for label in categories:
                    item = xbmcgui.ListItem(label)
                    items.append(item)
                listControl = self.getControl(self.C_POPUP_CATEGORY)
                listControl.reset()
                listControl.addItems(items)
                if sys.version_info[0] > 2:
                    listControl.selectItem(categories.index(cat))
                else:
                    listControl.selectItem(categories.index(cat.decode('utf-8')))

                self.setFocusId(self.C_POPUP_CATEGORY)
                xbmc.sleep(300)
                xbmc.executebuiltin('Action(ContextMenu)')

        else:
            self.buttonClicked = controlId
            self.close()

    def onFocus(self, controlId):
        pass

    def formatTime(self, timestamp):
        deb('formatTime')
        format = xbmc.getRegion('time').replace(':%S', '').replace('%H%H', '%H')
        return timestamp.strftime(format)

    def getControl(self, controlId):
        try:
            return super(PopupMenu, self).getControl(controlId)
        except:
            pass
        return None


class ChannelsMenu(xbmcgui.WindowXMLDialog):
    C_CHANNELS_LIST = 6000
    C_CHANNELS_SELECTION_VISIBLE = 6001
    C_CHANNELS_SELECTION = 6002
    C_CHANNELS_SAVE = 6003
    C_CHANNELS_CANCEL = 6004

    def __new__(cls, database, channel=None):
        return super(ChannelsMenu, cls).__new__(cls, 'script-tvguide-channels.xml', Skin.getSkinBasePath(), Skin.getSkinName(), skin_resolution)

    def __init__(self, database, channel=None):
        """

        @type database: source.Database
        """
        super(ChannelsMenu, self).__init__()
        self.database = database
        self.channelList = database.getChannelList(onlyVisible=False)
        self.swapInProgress = False
        try:
            self.startChannelIndex = self.channelList.index(channel)
        except:
            self.startChannelIndex = -1

    def onInit(self):
        self.updateChannelList()
        self.setFocusId(self.C_CHANNELS_LIST)

        if self.startChannelIndex > -1:
            try:
                listControl = self.getControl(self.C_CHANNELS_LIST)
                listControl.selectItem(self.startChannelIndex)
            except:
                pass
            self.startChannelIndex = -1

    def onAction(self, action):
        if action.getId() in [ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, KEY_NAV_BACK]:
            self.close()
            return

        if self.getFocusId() == self.C_CHANNELS_LIST and action.getId() == KEY_CONTEXT_MENU:
            listControl = self.getControl(self.C_CHANNELS_LIST)
            idx = listControl.getSelectedPosition()
            buttonControl = self.getControl(self.C_CHANNELS_SELECTION)
            buttonControl.setLabel('[UPPERCASE]{}[/UPPERCASE]'.format(self.channelList[idx].title))

            self.getControl(self.C_CHANNELS_SELECTION_VISIBLE).setVisible(False)
            self.setFocusId(self.C_CHANNELS_SELECTION)

        elif self.getFocusId() == self.C_CHANNELS_SELECTION and action.getId() in [ACTION_SELECT_ITEM, KEY_CONTEXT_MENU]:
            self.getControl(self.C_CHANNELS_SELECTION_VISIBLE).setVisible(True)
            xbmc.sleep(350)
            self.setFocusId(self.C_CHANNELS_LIST)

        elif self.getFocusId() == self.C_CHANNELS_SELECTION and action.getId() == ACTION_UP:
            listControl = self.getControl(self.C_CHANNELS_LIST)
            idx = listControl.getSelectedPosition()
            if idx > 0:
                self.swapChannels(idx, idx - 1)

        elif self.getFocusId() == self.C_CHANNELS_SELECTION and action.getId() == ACTION_DOWN:
            listControl = self.getControl(self.C_CHANNELS_LIST)
            idx = listControl.getSelectedPosition()
            if idx < listControl.size() - 1:
                self.swapChannels(idx, idx + 1)

    def onClick(self, controlId):
        if controlId == self.C_CHANNELS_LIST:
            listControl = self.getControl(self.C_CHANNELS_LIST)
            item = listControl.getSelectedItem()
            channel = self.channelList[int(item.getProperty('idx'))]
            channel.visible = not channel.visible

            if channel.visible:
                iconImage = 'tvguide-channel-visible.png'
            else:
                iconImage = 'tvguide-channel-hidden.png'
            item.setArt({'icon':iconImage})

        elif controlId == self.C_CHANNELS_SAVE:
            self.database.saveChannelList(self.close, self.channelList)

        elif controlId == self.C_CHANNELS_CANCEL:
            self.close()

    def onFocus(self, controlId):
        pass

    def updateChannelList(self):
        listControl = self.getControl(self.C_CHANNELS_LIST)
        listControl.reset()
        for idx, channel in enumerate(self.channelList):
            if channel.visible:
                iconImage = 'tvguide-channel-visible.png'
            else:
                iconImage = 'tvguide-channel-hidden.png'

            items = xbmcgui.ListItem('{}. {}'.format(idx + 1, channel.title))
            items.setArt({'icon':iconImage})
            items.setProperty('idx', str(idx))
            listControl.addItem(items)

    def updateListItem(self, idx, item):
        channel = self.channelList[idx]
        item.setLabel('{}. {}'.format(idx + 1, channel.title))

        if channel.visible:
            iconImage = 'tvguide-channel-visible.png'
        else:
            iconImage = 'tvguide-channel-hidden.png'
        item.setArt({'icon':iconImage})
        item.setProperty('idx', str(idx))

    def swapChannels(self, fromIdx, toIdx):
        if self.swapInProgress:
            return
        self.swapInProgress = True

        c = self.channelList[fromIdx]
        self.channelList[fromIdx] = self.channelList[toIdx]
        self.channelList[toIdx] = c

        # recalculate weight
        for idx, channel in enumerate(self.channelList):
            channel.weight = idx

        listControl = self.getControl(self.C_CHANNELS_LIST)
        self.updateListItem(fromIdx, listControl.getListItem(fromIdx))
        self.updateListItem(toIdx, listControl.getListItem(toIdx))

        listControl.selectItem(toIdx)
        xbmc.sleep(50)
        self.swapInProgress = False


class StreamSetupDialog(xbmcgui.WindowXMLDialog):
    C_STREAM_STRM_TAB = 101
    C_STREAM_FAVOURITES_TAB = 102
    C_STREAM_ADDONS_TAB = 103
    C_STREAM_STRM_BROWSE = 1001
    C_STREAM_STRM_FILE_LABEL = 1005
    C_STREAM_STRM_PREVIEW = 1002
    C_STREAM_STRM_OK = 1003
    C_STREAM_STRM_CANCEL = 1004
    C_STREAM_FAVOURITES = 2001
    C_STREAM_FAVOURITES_PREVIEW = 2002
    C_STREAM_FAVOURITES_OK = 2003
    C_STREAM_FAVOURITES_CANCEL = 2004
    C_STREAM_ADDONS = 3001
    C_STREAM_ADDONS_STREAMS = 3002
    C_STREAM_ADDONS_NAME = 3003
    C_STREAM_ADDONS_DESCRIPTION = 3004
    C_STREAM_ADDONS_PREVIEW = 3005
    C_STREAM_ADDONS_OK = 3006
    C_STREAM_ADDONS_CANCEL = 3007

    C_STREAM_VISIBILITY_MARKER = 100

    VISIBLE_STRM = 'strm'
    VISIBLE_FAVOURITES = 'favourites'
    VISIBLE_ADDONS = 'addons'

    def __new__(cls, database, channel):
        return super(StreamSetupDialog, cls).__new__(cls, 'script-tvguide-streamsetup.xml', Skin.getSkinBasePath(), Skin.getSkinName(), skin_resolution)

    def __init__(self, database, channel):
        """
        @type database: source.Database
        @type channel:source.Channel
        """
        super(StreamSetupDialog, self).__init__()
        self.database = database
        self.channel = channel
        self.previousAddonId = None
        self.strmFile = None
        self.streamingService = streaming.StreamsService()

    def close(self):
        if xbmc.Player().isPlaying():
            xbmc.Player().stop()
        super(StreamSetupDialog, self).close()

    def onInit(self):
        self.getControl(self.C_STREAM_VISIBILITY_MARKER).setLabel(self.VISIBLE_STRM)

        favourites = self.streamingService.loadFavourites()
        items = list()
        for label, value in favourites:
            item = xbmcgui.ListItem(label)
            item.setProperty('stream', value)
            items.append(item)

        listControl = self.getControl(StreamSetupDialog.C_STREAM_FAVOURITES)
        listControl.addItems(items)

        items = list()
        for id in self.streamingService.getAddons():
            try:
                addon = xbmcaddon.Addon(id)  # raises Exception if addon is not installed
                item = xbmcgui.ListItem(addon.getAddonInfo('name'), iconImage=addon.getAddonInfo('icon'))
                item.setProperty('addon_id', id)
                items.append(item)
            except Exception:
                pass
        listControl = self.getControl(StreamSetupDialog.C_STREAM_ADDONS)
        listControl.addItems(items)
        self.updateAddonInfo()

    def onAction(self, action):
        if action.getId() in [ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, KEY_NAV_BACK, KEY_CONTEXT_MENU] or action.getButtonCode() in [KEY_CONTEXT]:
            self.close()
            return

        elif self.getFocusId() == self.C_STREAM_ADDONS:
            self.updateAddonInfo()

    def onClick(self, controlId):
        if controlId == self.C_STREAM_STRM_BROWSE:
            stream = xbmcgui.Dialog().browse(1, ADDON.getLocalizedString(30304), 'video', '.strm')
            if stream:
                self.database.setCustomStreamUrl(self.channel, stream)
                self.getControl(self.C_STREAM_STRM_FILE_LABEL).setText(stream)
                self.strmFile = stream

        elif controlId == self.C_STREAM_ADDONS_OK:
            listControl = self.getControl(self.C_STREAM_ADDONS_STREAMS)
            item = listControl.getSelectedItem()
            if item:
                stream = item.getProperty('stream')
                self.database.setCustomStreamUrl(self.channel, stream)
            self.close()

        elif controlId == self.C_STREAM_FAVOURITES_OK:
            listControl = self.getControl(self.C_STREAM_FAVOURITES)
            item = listControl.getSelectedItem()
            if item:
                stream = item.getProperty('stream')
                self.database.setCustomStreamUrl(self.channel, stream)
            self.close()

        elif controlId == self.C_STREAM_STRM_OK:
            self.database.setCustomStreamUrl(self.channel, self.strmFile)
            self.close()

        elif controlId in [self.C_STREAM_ADDONS_CANCEL, self.C_STREAM_FAVOURITES_CANCEL, self.C_STREAM_STRM_CANCEL]:
            self.close()

        elif controlId in [self.C_STREAM_ADDONS_PREVIEW, self.C_STREAM_FAVOURITES_PREVIEW, self.C_STREAM_STRM_PREVIEW]:
            if xbmc.Player().isPlaying():
                xbmc.Player().stop()
                self.getControl(self.C_STREAM_ADDONS_PREVIEW).setLabel(strings(PREVIEW_STREAM))
                self.getControl(self.C_STREAM_FAVOURITES_PREVIEW).setLabel(strings(PREVIEW_STREAM))
                self.getControl(self.C_STREAM_STRM_PREVIEW).setLabel(strings(PREVIEW_STREAM))
                return

            stream = None
            visible = self.getControl(self.C_STREAM_VISIBILITY_MARKER).getLabel()
            if visible == self.VISIBLE_ADDONS:
                listControl = self.getControl(self.C_STREAM_ADDONS_STREAMS)
                item = listControl.getSelectedItem()
                if item:
                    stream = item.getProperty('stream')
            elif visible == self.VISIBLE_FAVOURITES:
                listControl = self.getControl(self.C_STREAM_FAVOURITES)
                item = listControl.getSelectedItem()
                if item:
                    stream = item.getProperty('stream')
            elif visible == self.VISIBLE_STRM:
                stream = self.strmFile

            if stream is not None:
                xbmc.Player().play(item=stream, windowed=True)
                if xbmc.Player().isPlaying():
                    self.getControl(self.C_STREAM_ADDONS_PREVIEW).setLabel(strings(STOP_PREVIEW))
                    self.getControl(self.C_STREAM_FAVOURITES_PREVIEW).setLabel(strings(STOP_PREVIEW))
                    self.getControl(self.C_STREAM_STRM_PREVIEW).setLabel(strings(STOP_PREVIEW))

    def onFocus(self, controlId):
        if controlId == self.C_STREAM_STRM_TAB:
            self.getControl(self.C_STREAM_VISIBILITY_MARKER).setLabel(self.VISIBLE_STRM)
        elif controlId == self.C_STREAM_FAVOURITES_TAB:
            self.getControl(self.C_STREAM_VISIBILITY_MARKER).setLabel(self.VISIBLE_FAVOURITES)
        elif controlId == self.C_STREAM_ADDONS_TAB:
            self.getControl(self.C_STREAM_VISIBILITY_MARKER).setLabel(self.VISIBLE_ADDONS)

    def updateAddonInfo(self):
        listControl = self.getControl(self.C_STREAM_ADDONS)
        item = listControl.getSelectedItem()
        if item is None:
            return

        if item.getProperty('addon_id') == self.previousAddonId:
            return

        self.previousAddonId = item.getProperty('addon_id')
        addon = xbmcaddon.Addon(id=item.getProperty('addon_id'))
        self.getControl(self.C_STREAM_ADDONS_NAME).setLabel('{}'.format(addon.getAddonInfo('name')))
        self.getControl(self.C_STREAM_ADDONS_DESCRIPTION).setText(addon.getAddonInfo('description'))

        streams = self.streamingService.getAddonStreams(item.getProperty('addon_id'))
        items = list()
        for (label, stream) in streams:
            item = xbmcgui.ListItem(label)
            item.setProperty('stream', stream)
            items.append(item)
        listControl = self.getControl(StreamSetupDialog.C_STREAM_ADDONS_STREAMS)
        listControl.reset()
        listControl.addItems(items)


class ChooseStreamAddonDialog(xbmcgui.WindowXMLDialog):
    C_SELECTION_LIST = 1000

    def __new__(cls, addons):
        return super(ChooseStreamAddonDialog, cls).__new__(cls, 'script-tvguide-streamaddon.xml', Skin.getSkinBasePath(), Skin.getSkinName(), skin_resolution)

    def __init__(self, addons):
        super(ChooseStreamAddonDialog, self).__init__()
        self.addons = addons
        self.stream = None

    def onInit(self):
        items = list()
        for id, label, url in self.addons:
            addon = xbmcaddon.Addon(id)

            item = xbmcgui.ListItem(label, addon.getAddonInfo('name'), addon.getAddonInfo('icon'))
            item.setProperty('stream', url)
            items.append(item)

        listControl = self.getControl(ChooseStreamAddonDialog.C_SELECTION_LIST)
        listControl.addItems(items)

        self.setFocus(listControl)

    def onAction(self, action):
        if action.getId() in [ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, KEY_NAV_BACK]:
            self.close()

    def onClick(self, controlId):
        if controlId == ChooseStreamAddonDialog.C_SELECTION_LIST:
            listControl = self.getControl(ChooseStreamAddonDialog.C_SELECTION_LIST)
            self.stream = listControl.getSelectedItem().getProperty('stream')
            self.close()

    def onFocus(self, controlId):
        pass


class InfoDialog(xbmcgui.WindowXMLDialog):
    C_INFO_PLAY = 7201
    C_INFO_RECORD = 7202
    C_INFO_REMIND = 7203
    C_INFO_EXTENDED = 7204

    def __new__(cls, program, playChannel2, recordProgram, notification, ExtendedInfo, onRedrawEPG, channelIdx, viewStartDate):
        return super(InfoDialog, cls).__new__(cls, 'DialogInfo.xml', Skin.getSkinBasePath(), Skin.getSkinName(), skin_resolution)

    def __init__(self, program, playChannel2, recordProgram, notification, ExtendedInfo, onRedrawEPG, channelIdx, viewStartDate):
        super(InfoDialog, self).__init__()
        self.program = program
        self.playChannel2 = playChannel2
        self.recordProgram = recordProgram
        self.notification = notification
        self.ExtendedInfo = ExtendedInfo
        self.onRedrawEPG = onRedrawEPG
        self.channelIdx = channelIdx
        self.viewStartDate = viewStartDate
        self.ignoreMissingControlIds = list()

        self.ignoreMissingControlIds.append(self.C_INFO_PLAY)
        self.ignoreMissingControlIds.append(self.C_INFO_RECORD)
        self.ignoreMissingControlIds.append(self.C_INFO_REMIND)
        self.ignoreMissingControlIds.append(self.C_INFO_EXTENDED)

    def setControlLabel(self, controlId, label):
        control = self.getControl(controlId)
        if control:
            control.setLabel(label)

    def formatTime(self, timestamp):
        format = xbmc.getRegion('time').replace(':%S', '').replace('%H%H', '%H')
        return timestamp.strftime(format)

    def setControlText(self, controlId, text):
        control = self.getControl(controlId)
        if control:
            control.setText(text)

    def setControlImage(self, controlId, image):
        control = self.getControl(controlId)
        if control:
            control.setImage(image)

    def realtimeDate(self, program):
        #Realtime date & weekday
        startDate = str(program.startDate)
        try:
            now = datetime.proxydt.strptime(startDate, '%Y-%m-%d %H:%M:%S')
        except:
            now = datetime.proxydt.strptime(str(datetime.datetime.now()), '%Y-%m-%d %H:%M:%S.%f')

        nowDay = now.strftime("%a").replace('Mon', strings(70109)).replace('Tue', strings(70110)).replace('Wed', strings(70111)).replace('Thu', strings(70112)).replace('Fri', strings(70113)).replace('Sat', strings(70114)).replace('Sun', strings(70115))
        nowDate = now.strftime("%d-%m-%Y")

        self.setControlLabel(C_MAIN_DAY, '{}'.format(nowDay))
        self.setControlLabel(C_MAIN_REAL_DATE, '{}'.format(nowDate))

    def calctimeLeft(self, program):
        startDelta = program.startDate
        endDelta = program.endDate

        calcTime = (endDelta - startDelta)

        calcTime = re.sub(r'^0:', '', str(calcTime))
        calcTime = re.sub(r':00$', 'min', str(calcTime))
        calcTime = re.sub(':', 'h', str(calcTime))

        matchHour = re.search(r'h\d+min$', calcTime)
        matchMin = re.search(r'^0\dmin', calcTime)

        if matchHour:
            calcTime = re.sub(r'min$', '', str(calcTime))

        elif matchMin:
            calcTime = re.sub(r'^0', '', str(calcTime))

        return calcTime

    def onInit(self):
        if self.program is None:
            return

        self.setControlLabel(C_MAIN_TITLE, '{}'.format(self.program.title))
        self.setControlLabel(C_MAIN_TIME, '{} - {}'.format(self.formatTime(self.program.startDate), self.formatTime(self.program.endDate)))
        self.setControlLabel(C_MAIN_CHAN_NAME, '{}'.format(self.program.channel.title))
        self.setControlLabel(C_MAIN_CALC_TIME_EPG, '{}'.format(self.calctimeLeft(self.program)))

        self.realtimeDate(self.program)

        if self.program.description:
            description = self.program.description
        else:
            description = strings(NO_DESCRIPTION)

        if skin_separate_category or skin_separate_year_of_production or skin_separate_director or skin_separate_episode or skin_separate_allowed_age_icon or skin_separate_program_progress or skin_separate_program_actors:
            # This mean we'll need to parse program description
            descriptionParser = src.ProgramDescriptionParser(description)
            if skin_separate_category:
                try:
                    categoryControl = self.getControl(C_PROGRAM_CATEGORY)
                    category = descriptionParser.extractCategory()
                    if category == strings(NO_CATEGORY):
                        category = self.program.categoryA
                    categoryControl.setText(category)
                except:
                    pass
            if skin_separate_year_of_production:
                try:
                    productionDateControl = self.getControl(C_PROGRAM_PRODUCTION_DATE)
                    year = descriptionParser.extractProductionDate()
                    if year == '':
                        year = self.program.productionDate
                    productionDateControl.setText(year)
                except:
                    pass
            if skin_separate_director:
                try:
                    directorControl = self.getControl(C_PROGRAM_DIRECTOR)
                    director = descriptionParser.extractDirector()
                    if director == '':
                        director = self.program.director
                    directorControl.setText(director)
                except:
                    pass
            if skin_separate_episode:
                try:
                    episodeControl = self.getControl(C_PROGRAM_EPISODE)
                    episode = descriptionParser.extractEpisode()
                    if episode == '':
                        episode = self.program.episode
                    episodeControl.setText(episode)
                except:
                    pass
            if skin_separate_allowed_age_icon:
                try:
                    ageImageControl = self.getControl(C_PROGRAM_AGE_ICON)
                    icon = descriptionParser.extractAllowedAge()
                    ageImageControl.setImage(icon)
                except:
                    pass
            if skin_separate_program_actors:
                try:
                    actorsControl = self.getControl(C_PROGRAM_ACTORS)
                    actors = descriptionParser.extractActors()
                    if actors == '':
                        actors = self.program.actor
                    actorsControl.setText(actors)
                except:
                    pass

            description = descriptionParser.description

        self.setControlText(C_MAIN_DESCRIPTION, description)
        
        p = re.compile('^http(s)?:\/\/.*')

        if self.program.channel.logo is not None:
            self.setControlImage(C_MAIN_LOGO, self.program.channel.logo)
        if self.program.imageSmall is not None and ADDON.getSetting('show_program_logo') == "true":
            if p.match(self.program.imageSmall):
                self.setControlImage(C_MAIN_IMAGE, self.program.imageSmall)
            else: self.program.imageSmall is None 
        if self.program.imageSmall is None:
            self.setControlImage(C_MAIN_IMAGE, 'tvguide-logo-epg.png')
        if self.program.imageLarge == 'live':
            self.setControlImage(C_MAIN_LIVE, 'live.png')
        else:
            self.setControlImage(C_MAIN_LIVE, '')

        self.stdat = time.mktime(self.program.startDate.timetuple())
        self.endat = time.mktime(self.program.endDate.timetuple())
        self.nodat = time.mktime(datetime.datetime.now().timetuple()) + 60 * float(ADDON.getSetting('timebar_adjust'))
        self.per = 100 - ((self.endat - self.nodat) // ((self.endat - self.stdat) // 100))
        if self.per > 0 and self.per < 100:
            self.getControl(C_PROGRAM_PROGRESS).setVisible(True)
            self.getControl(C_PROGRAM_PROGRESS).setPercent(self.per)
        else:
            self.getControl(C_PROGRAM_PROGRESS).setVisible(False)

        if self.per > 0 and self.per < 100:
            self.getControl(C_PROGRAM_SLIDER).setVisible(True)
            self.getControl(C_PROGRAM_SLIDER).setPercent(self.per)
        else:
            self.getControl(C_PROGRAM_SLIDER).setVisible(False)

    def setChannel(self, channel):
        self.channel = channel

    def getChannel(self):
        return self.channel

    def onAction(self, action):
        if action.getId() in [ACTION_SHOW_INFO, ACTION_PREVIOUS_MENU, KEY_NAV_BACK, ACTION_PARENT_DIR] or (action.getButtonCode() == KEY_INFO and KEY_INFO != 0) or (action.getButtonCode() == KEY_STOP and KEY_STOP != 0):
            self.close()

    def onClick(self, controlId):
        if controlId == 1000:
            self.close()

        elif controlId == self.C_INFO_PLAY:
            self.playChannel2(self.program)
            return

        elif controlId == self.C_INFO_RECORD:
            if xbmc.Player().isPlaying():
                xbmc.Player().stop()
                xbmc.sleep(1000)
                self.recordProgram(self.program)
            else:
                self.recordProgram(self.program)
                self.onRedrawEPG(self.channelIdx, self.viewStartDate)
                return

        elif controlId == self.C_INFO_REMIND:
            if self.program.notificationScheduled:
                if xbmc.Player().isPlaying():
                    self.notification.removeNotification(self.program)
                else:
                    self.notification.removeNotification(self.program)
                    self.onRedrawEPG(self.channelIdx, self.viewStartDate)
                    return
            else:
                if xbmc.Player().isPlaying():
                    self.notification.addNotification(self.program)
                else:
                    self.notification.addNotification(self.program)
                    self.onRedrawEPG(self.channelIdx, self.viewStartDate)
                    return

        elif controlId == self.C_INFO_EXTENDED:
            self.ExtendedInfo(self.program)
            return


class Pla(xbmcgui.WindowXMLDialog):
    def __new__(cls, program, database, urlList, archiveService, archivePlaylist, epg):
        return super(Pla, cls).__new__(cls, 'Vid.xml', Skin.getSkinBasePath(), Skin.getSkinName(), skin_resolution)

    def __init__(self, program, database, urlList, archiveService, archivePlaylist, epg):
        # debug('Pla __init__')
        super(Pla, self).__init__()
        self.epg = epg
        self.database = database
        self.controlAndProgramList = list()
        self.ChannelChanged = 0
        self.mouseCount = 0
        self.isClosing = False
        self.playbackStarted = False
        self.key_right_left_show_next = ADDON.getSetting('key_right_left_show_next')
        self.playButtonAsSchedule = False
        self.videoOSD = None
        self.displayService = True
        self.displayServiceTimer = None
        self.showOsdOnPlay = False
        self.displayAutoOsd = False
        self.ignoreInput = False
        self.ctrlService = None
        self.timer = None
        self.channel_number_input = False
        self.archiveService = archiveService
        self.archivePlaylist = archivePlaylist

        if sys.version_info[0] > 2:
            self.kodiPath = xbmcvfs.translatePath("special://home/")
            self.kodiPathMain = xbmcvfs.translatePath("special://xbmc/")
            self.kodiSkinPath = xbmcvfs.translatePath("special://skin/")
        else:
            self.kodiPath = xbmc.translatePath("special://home/")
            self.kodiPathMain = xbmc.translatePath("special://xbmc/")
            self.kodiSkinPath = xbmc.translatePath("special://skin/")

        if ADDON.getSetting('show_osd_on_play') == 'true':
            self.showOsdOnPlay = True
            self.displayAutoOsd = True
        if program is not None:
            if urlList is None:
                urlList = database.getStreamUrlList(program.channel)
            self.program = program
        elif self.epg.currentChannel:
            self.program = self.getCurrentProgram()
        else:
            deb('Pla currentChannel is none! Closing Pla!')
            self.isClosing = True
            return

        if urlList is not None:
            self.play(urlList)

        threading.Timer(0, self.waitForPlayBackStopped).start()

    def onInit(self):
        if self.isClosing:
            self.closeOSD()
            return
        if not self.ctrlService:
            self.ctrlService = self.getControl(C_VOSD_SERVICE)

        if ADDON.getSetting('info_osd') == "true":
            self.epg.setControlLabel(C_MAIN_CHAN_PLAY, '{}'.format(self.program.channel.title))
            self.epg.setControlLabel(C_MAIN_PROG_PLAY, '{}'.format(self.program.title))
            self.epg.setControlLabel(C_MAIN_TIME_PLAY, '{} - {}'.format(self.epg.formatTime(self.program.startDate), self.epg.formatTime(self.program.endDate)))
            self.epg.setControlLabel(C_MAIN_NUMB_PLAY, '{}'.format(self.database.getCurrentChannelIdx(self.program.channel) + 1))


        if ADDON.getSetting('show_time') == "true":
            nowtime = '$INFO[System.Time]'

            alignLeft = 0
            alignRight = 1

            skin_resolution = config.get("Skin", "resolution")
            currentSkin = xbmc.getSkinDir()
            chkSkinKodi = currentSkin

            smallList = list()
            mediumList = list()
            largeList = list()

            try:
                # Check path
                if xbmcvfs.exists(os.path.join(self.kodiPath, 'addons', chkSkinKodi, 'xml/')):
                    path0 = 'xml'
                elif xbmcvfs.exists(os.path.join(self.kodiPath, 'addons', chkSkinKodi, '720p/')):
                    path0 = '720p'
                elif xbmcvfs.exists(os.path.join(self.kodiPath, 'addons', chkSkinKodi, '1080i/')):
                    path0 = '1080i'
                elif xbmcvfs.exists(os.path.join(self.kodiPath, 'addons', chkSkinKodi, '16x9/')):
                    path0 = '16x9'

                if xbmcvfs.exists(os.path.join(self.kodiSkinPath, 'xml/')):
                    path1 = 'xml'
                elif xbmcvfs.exists(os.path.join(self.kodiSkinPath, '720p/')):
                    path1 = '720p'
                elif xbmcvfs.exists(os.path.join(self.kodiSkinPath, '1080i/')):
                    path1 = '1080i'
                elif xbmcvfs.exists(os.path.join(self.kodiSkinPath, '16x9/')):
                    path1 = '16x9'

                try:
                    file_check = xbmcvfs.File(os.path.join(self.kodiPath, 'addons', chkSkinKodi, path0, 'Font.xml'), 'r')
                except:
                    file_check = xbmcvfs.File(os.path.join(self.kodiSkinPath, path1, 'Font.xml'), 'r')
                f = file_check.read()
                
                sizeList = re.findall('<size>(.*?)</size>', f)
                nameList = re.findall('<name>(.*?)</name>', f)

                for idx in range(len(nameList)):
                    name = nameList[idx]
                    size = sizeList[idx]
                    size = re.sub('\.\d+$', '', size)
                    if int(size) > 25 and int(size) <= 35:
                        smallList.append(name)
                    if int(size) > 35 and int(size) <= 45:
                        mediumList.append(name)
                    if int(size) > 45:
                        largeList.append(name)

                if ADDON.getSetting('show_time_size') == "1":
                    size = smallList[0]
                elif ADDON.getSetting('show_time_size') == "2":
                    size = mediumList[0]
                elif ADDON.getSetting('show_time_size') == "3":
                    size = largeList[0]
                else:
                    size = 'font13'
                    
            except:
                size = 'font13'

            if ADDON.getSetting('show_time_pos') == "0":
                if skin_resolution == '720p':
                    showTime = xbmcgui.ControlLabel(20, 6, 200, 50, nowtime, textColor='0xFFFFFFFF',
                                                         alignment=alignLeft, font=size)
                elif skin_resolution == '1080i':
                    showTime = xbmcgui.ControlLabel(30, 10, 300, 75, nowtime, textColor='0xFFFFFFFF',
                                                         alignment=alignLeft, font=size)
                else:
                    showTime = xbmcgui.ControlLabel(30, 10, 300, 75, nowtime, textColor='0xFFFFFFFF',
                                                         alignment=alignLeft, font=size)

            if ADDON.getSetting('show_time_pos') == "1":
                if skin_resolution == '720p':
                    showTime = xbmcgui.ControlLabel(1060, 6, 200, 50, nowtime, textColor='0xFFFFFFFF',
                                                         alignment=alignRight, font=size)
                elif skin_resolution == '1080i':
                    showTime = xbmcgui.ControlLabel(1590, 10, 300, 75, nowtime,
                                                         textColor='0xFFFFFFFF', alignment=alignRight, font=size)
                else:
                    showTime = xbmcgui.ControlLabel(1590, 10, 300, 75, nowtime,
                                                         textColor='0xFFFFFFFF', alignment=alignRight, font=size)

            if ADDON.getSetting('show_time_pos') == "2":
                if skin_resolution == '720p':
                    showTime = xbmcgui.ControlLabel(20, 663, 200, 50, nowtime, textColor='0xFFFFFFFF',
                                                         alignment=alignLeft, font=size)
                elif skin_resolution == '1080i':
                    showTime = xbmcgui.ControlLabel(30, 995, 300, 75, nowtime, textColor='0xFFFFFFFF',
                                                         alignment=alignLeft, font=size)
                else:
                    showTime = xbmcgui.ControlLabel(30, 995, 300, 75, nowtime, textColor='0xFFFFFFFF',
                                                         alignment=alignLeft, font=size)

            if ADDON.getSetting('show_time_pos') == "3":
                if skin_resolution == '720p':
                    showTime = xbmcgui.ControlLabel(1060, 663, 200, 50, nowtime,
                                                         textColor='0xFFFFFFFF', alignment=alignRight, font=size)
                elif skin_resolution == '1080i':
                    showTime = xbmcgui.ControlLabel(1590, 995, 300, 75, nowtime,
                                                         textColor='0xFFFFFFFF', alignment=alignRight, font=size)
                else:
                    showTime = xbmcgui.ControlLabel(1590, 995, 300, 75, nowtime,
                                                         textColor='0xFFFFFFFF', alignment=alignRight, font=size)

            time.sleep(1)
            self.addControl(showTime)

            showTime.setAnimations([('visible', 'effect=fade end=100 time=300 delay=300',)])
            showTime.setVisibleCondition('Player.Playing + !Window.IsVisible(VidOSD.xml)')

    def play(self, urlList):
        self.epg.playService.playUrlList(urlList, self.archiveService, self.archivePlaylist, resetReconnectCounter=True)

    def playShortcut(self):
        self.channel_number_input = False
        self.viewStartDate = datetime.datetime.today() + datetime.timedelta(minutes=int(ADDON.getSetting('timebar_adjust')))
        self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)
        channelList = self.database.getChannelList(onlyVisible=True)
        if ADDON.getSetting('channel_shortcut') == 'false':
            for i in range(len(channelList)):
                if self.channel_number == channelList[i].id:
                    self.channelIdx = i
                    break
        else:
            self.channelIdx = (int(self.channel_number) - 1)
            self.channel_number = ""
            self.getControl(9999).setLabel(self.channel_number)

        channel = Channel(id='', title='', logo='', streamUrl='', visible='', weight='')
        program = Program(channel=channelList[self.channelIdx], title='', startDate='', endDate='', description='', productionDate='', director='', actor='', episode='', imageLarge='', imageSmall='', categoryA='', categoryB='')
        self.playChannel(program.channel)

    def onAction(self, action):
        debug('Pla onAction keyId {}, buttonCode {}'.format(action.getId(), action.getButtonCode()))

        if action.getId() == ACTION_PREVIOUS_MENU or action.getId() == ACTION_STOP or (action.getButtonCode() == KEY_STOP and KEY_STOP != 0) or (action.getId() == KEY_STOP and KEY_STOP != 0):
            self.epg.playService.stopPlayback()
            self.closeOSD()

        elif action.getId() == KEY_NAV_BACK:
            self.closeOSD()
            if ADDON.getSetting('navi_back_stop_play') == 'true':
                self.epg.playService.stopPlayback()
            else:
                # xbmc.executebuiltin("Action(FullScreen)")
                # if ADDON.getSetting('start_video_minimalized') == 'false':
                # xbmc.executebuiltin("Action(FullScreen)")
                # xbmc.executebuiltin("Action(Back)")
                # xbmc.sleep(300)
                if ADDON.getSetting('start_video_minimalized') == 'false':
                    xbmc.executebuiltin("Action(Back)")
                else:
                    self.epg._showEPG()

                # if ADDON.getSetting('start_video_minimalized') == 'false':
                # xbmc.executebuiltin("Action(FullScreen)")
                # xbmc.executebuiltin("Action(Back)")
                # self.epg.redrawagain = True
                # self.epg._showEPG()
                # pass
            return

        elif self.ignoreInput:
            debug('Pla ignoring key')
            return

        if action.getId() == KEY_CODEC_INFO:  # przysik O
            xbmc.executebuiltin("Action(CodecInfo)")

        elif action.getId() == ACTION_PAGE_UP or (action.getButtonCode() == KEY_PP and KEY_PP != 0) or (action.getId() == KEY_PP and KEY_PP != 0):
            self.ignoreInput = True
            self.ChannelChanged = 1
            self._channelUp()
            self.ignoreInput = False
            return

        elif action.getId() == ACTION_PAGE_DOWN or (action.getButtonCode() == KEY_PM and KEY_PM != 0) or (action.getId() == KEY_PM and KEY_PM != 0):
            self.ignoreInput = True
            self.ChannelChanged = 1
            self._channelDown()
            self.ignoreInput = False
            return

        elif action.getId() == KEY_CONTEXT_MENU or action.getButtonCode() == KEY_CONTEXT:
            self.ignoreInput = True
            self.changeStream()
            self.ignoreInput = False
            return

        elif self.playbackStarted == False:
            debug('Playback has not started yet, canceling all key requests')
            return

        elif action.getId() == ACTION_SHOW_INFO or (action.getButtonCode() == KEY_INFO and KEY_INFO != 0) or (action.getId() == KEY_INFO and KEY_INFO != 0):
            try:
                d = xbmcgui.Dialog()
                list = d.select(strings(31009), [strings(58000), strings(30356)])
                if list == 0:
                    self.program = self.getCurrentProgram()
                    self.epg.Info(self.program, self.epg.playChannel2, self.epg.recordProgram, self.epg.notification, self.epg.ExtendedInfo, self.epg.onRedrawEPG, self.epg.channelIdx, self.epg.viewStartDate)
                elif list == 1:
                    self.program = self.getCurrentProgram()
                    self.epg.ExtendedInfo(self.program)
            except:
                pass
            return

        elif action.getButtonCode() == KEY_VOL_DOWN or (action.getId() == ACTION_LEFT and self.key_right_left_show_next == 'false'):
            xbmc.executebuiltin("Action(VolumeDown)")

        elif action.getButtonCode() == KEY_VOL_UP or (action.getId() == ACTION_RIGHT and self.key_right_left_show_next == 'false'):
            xbmc.executebuiltin("Action(VolumeUp)")

        elif (action.getId() == ACTION_LEFT and self.key_right_left_show_next == 'true'):
            self.showVidOsd(ACTION_LEFT)

        elif (action.getId() == ACTION_RIGHT and self.key_right_left_show_next == 'true'):
            self.showVidOsd(ACTION_RIGHT)

        elif (action.getId() == ACTION_UP):
            self.showVidOsd(ACTION_UP)

        elif (action.getId() == ACTION_DOWN):
            self.showVidOsd(ACTION_DOWN)

        elif (action.getId() == ACTION_SELECT_ITEM):
            try:
                if ADDON.getSetting('VidOSD_on_select') == 'true':
                    self.showVidOsd()
                else:
                    self.program = self.getCurrentProgram()
                    self.epg.Info(self.program)
            except:
                pass
            return

        elif (action.getButtonCode() == KEY_HOME2 and KEY_HOME2 != 0) or (action.getId() == KEY_HOME2 and KEY_HOME2 != 0):
            xbmc.executebuiltin("SendClick(VideoLibrary)")

        elif action.getId() == ACTION_MOUSE_MOVE and xbmc.Player().isPlaying():
            self.mouseCount = self.mouseCount + 1
            if self.mouseCount > 15:
                self.mouseCount = 0
                osd = VideoOSD(self)
                osd.doModal()
                del osd

        elif action.getButtonCode() == KEY_SWITCH_TO_LAST:
            deb('Pla play last channel')
            channel = self.epg.getLastChannel()
            if channel:
                self.playChannel(channel)

        if (ADDON.getSetting('channel_shortcut') != 'false'):
            digit = None
            if not self.channel_number_input:
                code = action.getButtonCode() - 61488
                action_code = action.getId() - 58
                action_code_2 = action.getId() - 140
                if (code >= 0 and code <= 9) or (action_code >= 0 and action_code <= 9) or (action_code_2 >= 0 and action_code_2 <= 9):
                    digit = None
                    if (code >= 0 and code <= 9):
                        digit = code
                    elif (action_code_2 >= 0 and action_code_2 <= 9):
                        digit = action_code_2
                    else:
                        digit = action_code
                    self.channel_number_input = True
                    self.channel_number = str(digit)
                    self.getControl(9999).setLabel(self.channel_number)
                    if self.timer and self.timer.is_alive():
                        self.timer.cancel()
                    self.timer = threading.Timer(2, self.playShortcut)
                    self.timer.start()

            if self.channel_number_input:
                if digit == None:
                    code = action.getButtonCode() - 61488
                    action_code = action.getId() - 58
                    action_code_2 = action.getId() - 140
                    if (code >= 0 and code <= 9) or (action_code >= 0 and action_code <= 9) or (action_code_2 >= 0 and action_code_2 <= 9):
                        digit = None
                        if (code >= 0 and code <= 9):
                            digit = code
                        elif (action_code_2 >= 0 and action_code_2 <= 9):
                            digit = action_code_2
                        else:
                            digit = action_code
                    if digit != None:
                        self.channel_number = "{}{}".format(self.channel_number.strip('_'), digit)
                        self.getControl(9999).setLabel(self.channel_number)
                        if self.timer and self.timer.is_alive():
                            self.timer.cancel()
                        self.timer = threading.Timer(2, self.playShortcut)
                        self.timer.start()

        if (ADDON.getSetting('channel_shortcut') == 'false'):
            digit = None
            if not self.channel_number_input:
                code = action.getButtonCode() - 61488
                action_code = action.getId() - 58
                action_code_2 = action.getId() - 140
                if (code >= 0 and code <= 9) or (action_code >= 0 and action_code <= 9) or (action_code_2 >= 0 and action_code_2 <= 9):
                    digit = None
                    if (code >= 0 and code <= 9):
                        digit = code
                    elif (action_code_2 >= 0 and action_code_2 <= 9):
                        digit = action_code_2
                    else:
                        digit = action_code
                    xbmcgui.Dialog().notification(strings(30353), strings(30354))
                    return

            if self.channel_number_input:
                if digit == None:
                    code = action.getButtonCode() - 61488
                    action_code = action.getId() - 58
                    action_code_2 = action.getId() - 140
                    if (code >= 0 and code <= 9) or (action_code >= 0 and action_code <= 9) or (action_code_2 >= 0 and action_code_2 <= 9):
                        digit = None
                        if (code >= 0 and code <= 9):
                            digit = code
                        elif (action_code_2 >= 0 and action_code_2 <= 9):
                            digit = action_code_2
                        else:
                            digit = action_code
                    if digit != None:
                        xbmcgui.Dialog().notification(strings(30353), strings(30354))
                        return

    def onAction2(self, action, program=None):
        debug('Pla onAction2')
        if action in [ACTION_STOP, KEY_NAV_BACK]:
            self.epg.playService.stopPlayback()
            self.closeOSD()

        elif action == ACTION_SHOW_INFO:
            try:
                if program is None:
                    program = self.getCurrentProgram()
                d = xbmcgui.Dialog()
                list = d.select(strings(31009), [strings(58000), strings(30356)])
                if list == 0:
                    self.epg.Info(program, self.epg.playChannel2, self.epg.recordProgram, self.epg.notification, self.epg.ExtendedInfo, self.epg.onRedrawEPG, self.epg.channelIdx, self.epg.viewStartDate)
                elif list == 1:
                    self.epg.ExtendedInfo(program)
            except:
                pass
            return

        elif action == ACTION_PAGE_UP:
            self.ChannelChanged = 1
            self._channelUp()

        elif action == ACTION_PAGE_DOWN:
            self.ChannelChanged = 1
            self._channelDown()

    def onPlayBackStopped(self):
        debug('Pla onPlayBackStopped')
        self.closeOSD()

    def waitForPlayBackStopped(self):
        self.wait = True

        xbmc.sleep(50)
        while self.epg.playService.isWorking() == True and not self.isClosing:
            xbmc.sleep(100)

        while self.wait == True and not self.isClosing:
            if xbmc.Player().isPlaying() and not strings2.M_TVGUIDE_CLOSING and not self.isClosing and not self.epg.playService.isWorking():
                self.playbackStarted = True
                if self.displayService:
                    self.displayServiceOnOSD()
                if self.displayAutoOsd and self.showOsdOnPlay:
                    self.displayAutoOsd = False
                    self.showVidOsd(AUTO_OSD)
                else:
                    xbmc.sleep(200)
            else:
                xbmc.sleep(100)
                self.playbackStarted = False
                if not self.isClosing and (self.ChannelChanged == 1 or self.epg.playService.isWorking() == True):
                    while self.epg.playService.isWorking() == True and not self.isClosing:
                        xbmc.sleep(100)
                    self.ChannelChanged = 0
                    self.show()
                    self.displayService = True
                else:
                    if ADDON.getSetting('vosd.arg'):
                        self.epg.playService.stopPlayback()
                        self.closeOSD()
                    else:
                        debug('Pla waitForPlayBackStopped not waiting anymore')
                        self.wait = False
                        break

        self.onPlayBackStopped()

    def _channelUp(self):
        # debug('Pla _channelUp')
        channel = self.database.getNextChannel(self.epg.currentChannel)
        self.playChannel(channel)

    def _channelDown(self):
        # debug('Pla _channelDown')
        channel = self.database.getPreviousChannel(self.epg.currentChannel)
        self.playChannel(channel)

    def playChannel(self, channel):
        debug('Pla playChannel')
        if channel.id != self.epg.currentChannel.id:
            self.ChannelChanged = 1
            self.epg.updateCurrentChannel(channel)
            self.program = self.getCurrentProgram()
            self.epg.program = self.program
            urlList = self.database.getStreamUrlList(channel)
            if len(urlList) > 0:
                self.epg.playService.playUrlList(urlList, self.archiveService, self.archivePlaylist, resetReconnectCounter=True)
                if self.showOsdOnPlay:
                    self.displayAutoOsd = True

    def changeStream(self):
        deb('Changing stream for channel {}'.format(self.epg.currentChannel.id))
        self.epg.playService.playNextStream()
        self.displayService = True
        if ADDON.getSetting('osd_on_stream_change') == 'true':
            self.displayAutoOsd = True

    def getProgramUp(self, program):
        channel = self.database.getPreviousChannel(program.channel)
        return self.database.getCurrentProgram(channel)

    def getProgramDown(self, program):
        channel = self.database.getNextChannel(program.channel)
        return self.database.getCurrentProgram(channel)

    def getProgramLeft(self, program):
        return self.database.getPreviousProgram(program)

    def getProgramRight(self, program):
        return self.database.getNextProgram(program)

    def getCurrentProgram(self):
        return self.database.getCurrentProgram(self.epg.currentChannel)

    def showVidOsd(self, action=None):
        if ADDON.getSetting('archive_support') == 'true' and (self.archiveService != '' or self.archivePlaylist != ''):
            self.program = self.program
        else:
            self.program = self.getCurrentProgram()
        self.displayServiceOnOSD()
        self.videoOSD = VideoOSD(self, False, action)
        self.videoOSD.doModal()
        del self.videoOSD
        self.videoOSD = None

    def closeOSD(self):
        # debug('Pla closeOSD')
        self.isClosing = True
        if self.videoOSD:
            self.videoOSD.isClosing = True
            self.videoOSD.close()
        if self.displayServiceTimer:
            self.displayServiceTimer.cancel()
        self.close()

    def displayServiceOnOSD(self):
        # debug('displayServiceOnOSD')
        self.displayService = False
        if self.ctrlService and ADDON.getSetting('show_service_name') == 'true':
            displayedService = self.epg.playService.getCurrentServiceString()
            self.ctrlService.setLabel(displayedService)
            if self.displayServiceTimer:
                self.displayServiceTimer.cancel()
            self.displayServiceTimer = threading.Timer(3, self.hideServiceOnOSD)
            self.displayServiceTimer.start()

    def hideServiceOnOSD(self):
        self.displayServiceTimer = None
        self.ctrlService.setLabel('')

    def getControl(self, controlId):
        try:
            return super(Pla, self).getControl(controlId)
        except:
            pass
        return None

class ProgramListDialog(xbmcgui.WindowXMLDialog):
    C_PROGRAM_LIST = 1000
    C_PROGRAM_LIST_TITLE = 1001

    def __new__(cls, title, programs, currentChannel, sort_time=False):
        return super(ProgramListDialog, cls).__new__(cls, 'script-tvguide-programlist.xml', Skin.getSkinBasePath(), Skin.getSkinName(), skin_resolution)

    def __init__(self, title, programs, currentChannel, sort_time=False):
        super(ProgramListDialog, self).__init__()
        self.title = title
        self.programs = programs
        self.index = -1
        self.action = None
        self.sort_time = sort_time
        self.startChannelIndex = currentChannel

    def onInit(self):
        xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
        control = self.getControl(ProgramListDialog.C_PROGRAM_LIST_TITLE)
        control.setLabel(self.title)

        items = list()
        index = 0

        for program in self.programs:  # type: object
            label = program.title
            description = program.description
            descriptionParser = src.ProgramDescriptionParser(description)
            episode = descriptionParser.extractEpisode()
            if episode != '':
                se_label = ' - {}'.format(episode)
            else:
                se_label = ''
            try:
                episode = program.episode
                if episode:
                    se_label = ' - {}'.format(episode)
            except:
                pass
            label = label + se_label
            name = ''
            icon = program.channel.logo  # type: object
            item = xbmcgui.ListItem(label, name)

            item.setArt({'icon':icon})

            item.setProperty('index', str(index))
            index = index + 1

            item.setProperty('ChannelName', replace_formatting(program.channel.title))
            item.setProperty('Plot', replace_formatting(program.description))
            item.setProperty('startDate', str(time.mktime(program.startDate.timetuple())))

            start = program.startDate
            end = program.endDate
            duration = end - start
            now = datetime.datetime.now() + datetime.timedelta(minutes=int(ADDON.getSetting('timebar_adjust')))

            if now > start:
                when = datetime.timedelta(-1)
                elapsed = now - start
            else:
                when = start - now
                elapsed = datetime.timedelta(0)

            day = self.formatDateTodayTomorrow(start)
            start_str = start.strftime("%H:%M")
            start_str = "{} {} - {}".format(start_str, start.strftime("%d-%m").replace('-', '/').replace('0', ''), day)
            
            if len(start_str) > 18 and xbmcgui.getScreenWidth() < 2560:
                start_str = start_str[0:18] + '.'
            
            item.setProperty('StartTime', start_str)

            duration_str = "{} min".format(duration.seconds // 60)
            item.setProperty('Duration', duration_str)

            days = when.days
            hours, remainder = divmod(when.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if days > 1:
                when_str = strings(30332).format(days)
                item.setProperty('When', when_str)
            elif days > 0:
                when_str = strings(30333).format(days)
                item.setProperty('When', when_str)
            elif hours > 1:
                when_str = strings(30334).format(hours)
                item.setProperty('When', when_str)
            elif seconds > 0:
                when_str = strings(30335).format(when.seconds // 60)
                item.setProperty('When', when_str)

            if elapsed.seconds > 0:
                progress = 100.0 * float(timedelta_total_seconds(elapsed)) // float(duration.seconds + 0.001)
                progress = str(int(progress))
            else:
                # TODO hack for progress bar with 0 time
                progress = "0"

            if progress and (int(progress) < 100):
                item.setProperty('Completed', progress)

            program_image = program.imageSmall if program.imageSmall else 'tvguide-logo-epg.png'
            item.setProperty('ProgramImage', program_image)
            items.append(item)

        if self.sort_time == True:
            items = sorted(items, key=lambda x: x.getProperty('startDate'))

        listControl = self.getControl(ProgramListDialog.C_PROGRAM_LIST)
        listControl.addItems(items)
        if self.startChannelIndex is not None:
            try:
                listControl.selectItem(int(self.startChannelIndex))
            except:
                listControl.selectItem(int(0))

        if items != '':
            xbmc.executebuiltin('Dialog.Close(busydialognocancel)')

    def onAction(self, action):
        listControl = self.getControl(self.C_PROGRAM_LIST)
        self.id = self.getFocusId(self.C_PROGRAM_LIST)
        item = listControl.getSelectedItem()
        if item:
            self.index = int(item.getProperty('index'))
        else:
            self.index = -1
        if action.getId() in [ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, KEY_NAV_BACK]:
            self.action = KEY_NAV_BACK
            self.close()
        elif action.getId() == KEY_CONTEXT_MENU:
            self.action = KEY_CONTEXT_MENU
            self.close()
        elif action.getId() == ACTION_LEFT:
            self.action = ACTION_LEFT
            self.close()
        elif action.getId() == ACTION_RIGHT:
            self.action = ACTION_RIGHT
            self.close()
        elif action.getId() == ACTION_SHOW_INFO:
            self.action = ACTION_SHOW_INFO
            self.close()

    def onClick(self, controlId):
        if controlId == self.C_PROGRAM_LIST:
            listControl = self.getControl(self.C_PROGRAM_LIST)
            self.id = self.getFocusId(self.C_PROGRAM_LIST)
            item = listControl.getSelectedItem()
            if item:
                self.index = int(item.getProperty('index'))
            else:
                self.index = -1
            self.close()

    def onFocus(self, controlId):
        pass

    # TODO make global function
    def formatDateTodayTomorrow(self, timestamp):
        if timestamp:
            today = datetime.datetime.today() + datetime.timedelta(minutes=int(ADDON.getSetting('timebar_adjust')))
            tomorrow = today + datetime.timedelta(days=1)
            yesterday = today - datetime.timedelta(days=1)
            if today.date() == timestamp.date():
                return strings(30329)
            elif tomorrow.date() == timestamp.date():
                return strings(30330)
            elif yesterday.date() == timestamp.date():
                return strings(30331)
            else:
                return timestamp.strftime("%a").replace('Mon', strings(70109)).replace('Tue', strings(70110)).replace('Wed', strings(70111)).replace('Thu', strings(70112)).replace('Fri', strings(70113)).replace('Sat', strings(70114)).replace('Sun', strings(70115))

    def close(self):
        super(ProgramListDialog, self).close()