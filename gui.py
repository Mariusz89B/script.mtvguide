#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2020 Mariusz89B
#   Copyright (C) 2018 primaeval
#   Copyright (C) 2016 Andrzej Mleczko
#   Copyright (C) 2014 Krzysztof Cebulski
#   Copyright (C) 2013 Szakalit
#   Copyright (C) 2013 Tommy Winther

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

if sys.version_info[0] > 2:
    PY3 = True
else:
    PY3 = False

if sys.version_info[0] < 3:
    from future.utils import bytes_to_native_str as native

if PY3:
    import configparser
else:
    import ConfigParser

import re, os, datetime, time, platform, threading, shutil
import xbmc, xbmcgui, xbmcvfs, xbmcaddon
import source as src
from unidecode import unidecode
from notification import Notification
from groups import *
from strings import *
import strings as strings2
import streaming
import playService
import requests
import json
from vosd import VideoOSD
from recordService import RecordService
from settingsImportExport import SettingsImp
from skins import Skin
from source import Program, Channel

import collections

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

ACTION_GESTURE_SWIPE_LEFT = 511
ACTION_GESTURE_SWIPE_RIGHT = 521
ACTION_GESTURE_SWIPE_UP = 531
ACTION_GESTURE_SWIPE_DOWN = 541
ACTION_TOUCH_TAP = 401

ACTION_MOUSE_RIGHT_CLICK = 101
ACTION_MOUSE_MIDDLE_CLICK = 102
ACTION_MOUSE_WHEEL_UP = 104
ACTION_MOUSE_WHEEL_DOWN = 105
ACTION_MOUSE_MOVE = 107

KEY_NAV_BACK = 92
KEY_CONTEXT_MENU = 117
KEY_HOME = 159
KEY_END = 160

ACTION_GUIDE = 777

KEY_CODEC_INFO = 0

if PY3:
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
    skin_separate_rating = config.getboolean("Skin", "program_show_rating")
except:
    skin_separate_rating = False
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
    return (timedelta.microseconds + 0.0 + (timedelta.seconds + timedelta.days * 24 * 3600) * 10 ** 6) // 10 ** 6


def timebarAdjust():
    timebar_adjust = ADDON.getSetting('timebar_adjust')
    if timebar_adjust == '' or timebar_adjust is None:
        timebar_adjust = 0
    return timebar_adjust

def getDistro():
    if xbmc.getCondVisibility('System.HasAddon(service.coreelec.settings)'):
        return "CoreElec"
    elif xbmc.getCondVisibility('System.HasAddon(service.libreelec.settings)'):
        return "LibreElec"
    elif xbmc.getCondVisibility('System.HasAddon(service.osmc.settings)'):
        return "OSMC"
    else:
        return "Kodi"

def formatFileSize(size):
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return "%3.1f %s" % (size, x)
        size /= 1024.0

    return size

class proxydt(datetime.datetime):
    @staticmethod
    def strptime(date_string, format):
        import time
        try:
            res = datetime.datetime.strptime(date_string, format)
        except:
            res = datetime.datetime(*(time.strptime(date_string, format)[0:6]))
        return res

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
        deb("################ Starting control VideoPlayer events ################")
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
        deb("################ PlayBackError ################")
        self.updatePositionTimerData['stop'] = True
        self.onStateChange("PlayBackError")
        ADDON.setSetting('vosd.arg', 'false')

    def onPlayBackPaused(self):
        deb("################ Im paused ################")
        # self.playerStateChanged("Paused")
        # threading.Timer(0.3, self.stopplaying).start()

    def onPlayBackResumed(self):
        deb("################ Im Resumed ################")
        # self.onStateChange("Resumed")

    def onPlayBackStarted(self):
        deb("################ Playback Started ################")
        self.updatePositionTimerData['stop'] = True
        self.onStateChange("Started")
        try:
            playedFile = xbmc.Player().getPlayingFile()
            if os.path.isfile(playedFile):
                try:
                    playlistFileName = re.sub('_part_\d*.mpeg', '.mpeg', playedFile)
                    currentPositionInPlaylist = int(xbmc.PlayList(xbmc.PLAYLIST_VIDEO).getposition())
                    self.recordedFilesPlaylistPositions[playlistFileName] = currentPositionInPlaylist
                    deb('onPlayBackStarted updating playlist position to: {} file: {}'.format(currentPositionInPlaylist, playlistFileName))
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
        deb("################# Playback Ended #################")
        self.updatePositionTimerData['stop'] = True
        self.onStateChange("Ended")
        ADDON.setSetting('vosd.arg', 'false')

    def onPlayBackStopped(self):
        xbmc.sleep(100)
        deb("################# Playback Stopped #################")
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

    C_MAIN_SLIDE = 4975
    C_MAIN_SLIDE_CLICK = 4976

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
        self.controlAndProgramList = []
        self.ignoreMissingControlIds = []
        self.recordedFilesPlaylistPositions = {}
        self.streamingService = streaming.StreamsService()
        self.playService = playService.PlayService()
        self.recordService = RecordService(self)
        self.predefinedCategories = []
        self.getListLenght = []
        self.catchupChannels = None
        self.context = False

        # find nearest half hour
        self.viewStartDate = datetime.datetime.today() + datetime.timedelta(minutes=int(timebarAdjust()))
        self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)

        self.start = 0
        self.end = 0
        self.played = 0

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

        if PY3:
            try:
                self.profilePath  = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
            except:
                self.profilePath  = xbmcvfs.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')
        else:
            try:
                self.profilePath  = xbmc.translatePath(ADDON.getAddonInfo('profile'))
            except:
                self.profilePath  = xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')

        if PY3:
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

    def restartKodi(self):
        androidOS = xbmc.getCondVisibility('system.platform.android') 
        iOS = xbmc.getCondVisibility('system.platform.ios')
        macOS = xbmc.getCondVisibility('system.platform.osx')
        atvOS = xbmc.getCondVisibility('system.platform.atv2')

        if androidOS:
            xbmc.executebuiltin("Quit")

        else:
            if getDistro() == 'Kodi':
                xbmc.executebuiltin("RestartApp")
            else:
                xbmc.executebuiltin("Reboot")

    def exitAddon(self):
        exit()

    def tutorialGetEPG(self):
        res = xbmcgui.Dialog().select(strings(59940), [strings(59906), strings(59908)])

        if res < 0:
            res = xbmcgui.Dialog().yesno(strings(59924), strings(59938))
            if res:
                ADDON.setSetting('m-TVGuide', 'https://')
                ADDON.setSetting('xmltv_file', '')
                ADDON.setSetting('tutorial', 'true')
                self.exitAddon()
            else:
                self.tutorialGetEPG()

        if res == 0:
            ADDON.setSetting('source', '1')

            txt = ADDON.getSetting('m-TVGuide')
            if txt == '' or txt == 'http://' or txt == 'https://':
                txt = 'https://'

            kb = xbmc.Keyboard(txt,'')
            kb.setHeading(strings(59941))
            kb.setHiddenInput(False)
            kb.doModal()
            c = kb.getText() if kb.isConfirmed() else None
            if c == '': c = None

            ADDON.setSetting('m-TVGuide', c)

            if c is not None:
                ans = xbmcgui.Dialog().yesno(strings(60011), strings(60012))
                if ans:
                    ADDON.setSetting('epg_display_name', 'true')
                else:
                    ADDON.setSetting('epg_display_name', 'false')
                self.tutorialGetCountry()
            else:
                self.tutorialGetEPG()


        elif res == 1:
            ADDON.setSetting('source', '0')
            fn = xbmcgui.Dialog().browse(1, strings(59942), '')
            ADDON.setSetting('xmltv_file', fn)
            if fn != '':
                ans = xbmcgui.Dialog().yesno(strings(60011), strings(60012))
                if ans:
                    ADDON.setSetting('epg_display_name', 'true')
                else:
                    ADDON.setSetting('epg_display_name', 'false')
                self.tutorialGetCountry()
            else:
                self.tutorialGetEPG()


    def tutorialGetCountry(self):
        CC_DICT = ccDict()

        progExec = False
        resExtra = False

        langList = []
        ccList = []

        continent = xbmcgui.Dialog().select(strings(30725), [xbmc.getLocalizedString(593), strings(30727), strings(30728), strings(30729), strings(30730), strings(30731), strings(30732), '[COLOR red]' + strings(30726) + '[/COLOR]'])

        if continent < 0:
            resBack = xbmcgui.Dialog().yesno(strings(59924), strings(59938), yeslabel=strings(59939), nolabel=strings(30308))

            if resBack:
                self.tutorialGetEPG()

            else:
                ADDON.setSetting('tutorial', 'true')
                self.exitAddon()

        elif continent == 0:
            filtered_dict = dict((k, v) for k, v in CC_DICT.items() if int(v['continent']) != 7)
            ADDON.setSetting(id='show_group_channels', value='true')

        elif continent == 7:
            filtered_dict = dict((k, v) for k, v in CC_DICT.items() if int(v['continent']) == 7)
            ADDON.setSetting(id='show_group_channels', value='false')

        else:
            filtered_dict = dict((k, v) for k, v in CC_DICT.items() if int(v['continent']) == continent or (int(v['continent']) == -1 and continent != 6))
            ADDON.setSetting(id='show_group_channels', value='true')

        if sys.version_info[0] < 3:
            filtered_dict = collections.OrderedDict(sorted(filtered_dict.items()))

        for cc, value in filtered_dict.items():
            lang = value.get('translated', '')
            if lang == '':
                lang = value['language']

            if lang.isdigit():
                country = strings(int(lang))
            else:
                country = lang

            if cc == 'all':
                langList.append(country)
            else:
                langList.append('[B]' + cc.upper() + '[/B] - ' + country)
            ccList.append(cc)

        res = xbmcgui.Dialog().multiselect(strings(59943), langList)

        if not res:
            self.tutorialGetCountry()

        if res == 0:
            for i in range(len(langList)):
                if ccList[i] != 'all':
                    ADDON.setSetting('country_code_{cc}'.format(cc=ccList[i]), 'false')
                ADDON.setSetting('show_group_channels', 'false')
            progExec = True

        else:
            ADDON.setSetting('show_group_channels', 'true')

            if len(res) > 1:
                resExtra = xbmcgui.Dialog().yesno(strings(59924), strings(59962))

            for i in range(len(langList)):
                ADDON.setSetting('country_code_{cc}'.format(cc=ccList[i]), 'false')
                if i in res:
                    label = langList[i].lower()
                    if ccList[i] != 'all':
                        ADDON.setSetting('country_code_{cc}'.format(cc=ccList[i]), 'true')
                    if resExtra:
                        response = xbmcgui.Dialog().yesno(strings(59924), strings(59944).format(ccList[i].upper()))
                        if response:
                            ADDON.setSetting('source', 'm-TVGuide')
                            if ccList[i] != 'all':
                                txt = ADDON.getSetting('epg_{cc}'.format(cc=ccList[i]))
                            else:
                                txt = ADDON.getSetting('m-TVGuide')
                            if txt == '':
                                txt = 'https://'

                            kb = xbmc.Keyboard(txt,'')
                            kb.setHeading(strings(59945).format(label))
                            kb.setHiddenInput(False)
                            kb.doModal()
                            c = kb.getText() if kb.isConfirmed() else None
                            if c == '': c = None

                            ADDON.setSetting('epg_{cc}'.format(cc=ccList[i]), c)
                            if c is not None:
                                progExec = True

                            else:
                                ADDON.setSetting('country_code_{cc}'.format(cc=ccList[i]), 'false')
                                self.tutorialGetCountry()

                        else:
                            progExec = True

                    else:
                        progExec = True

        if progExec is True:
            try:
                ADDON.setSetting(id="countryUrlChannels", value=str(strings(30721) + ' (' + strings(59919)+')'))
            except:
                ADDON.setSetting(id="countryUrlChannels", value=str((strings(30721) + ' (' + strings(59919)+')').encode('utf-8', 'replace'))) 
            self.tutorialGetService()

    def tutorialGetService(self):
        progExec = False

        res = xbmcgui.Dialog().multiselect(strings(59946), [strings(59947), strings(59948)])

        if not res:
            resBack = xbmcgui.Dialog().yesno(strings(59924), strings(59938), yeslabel=strings(59939), nolabel=strings(30308))
            if resBack:
                self.tutorialGetCountry()

            else:
                ADDON.setSetting('tutorial', 'true')
                self.exitAddon()

        for p in res:
            if p == 0:
                res = xbmcgui.Dialog().multiselect(strings(59949), ['C More', 'Ipla', 'nc+ GO', 'PlayerPL', 'Polsat GO', 'Polsat GO Box', 'TVP GO', 'Telia Play', 'WP Pilot'])

                if not res:
                    resBack = xbmcgui.Dialog().yesno(strings(59924), strings(59938), yeslabel=strings(59939), nolabel=strings(30308))
                    if resBack:
                        self.tutorialGetService()

                    else:
                        ADDON.setSetting('tutorial', 'true')
                        self.exitAddon()
                for s in res:
                    if s == 0:
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

                    if s == 1:
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

                                res = xbmcgui.Dialog().select(strings(95014), ['Ipla', 'Cyfrowy Polsat'])

                                if res < 0:
                                    ADDON.setSetting('ipla_enabled', 'false')
                                    self.tutorialGetService()

                                if res == 0:
                                    ADDON.setSetting('ipla_client', 'Ipla')

                                elif res == 1:
                                    ADDON.setSetting('ipla_client', 'Cyfrowy Polsat')

                            else:
                                ADDON.setSetting('ipla_enabled', 'false')
                                self.tutorialGetService()

                        else:
                            ADDON.setSetting('ipla_enabled', 'false')
                            self.tutorialGetService()

                    if s == 2:
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

                    if s == 3:
                        label = 'PlayerPL'
                        xbmcgui.Dialog().ok(label, label + ' ' + strings(30733).lower())
                        ADDON.setSetting('playerpl_enabled', 'true')
                        progExec = True

                    if s == 4:
                        label = 'Polsat GO'
                        xbmcgui.Dialog().ok(label, strings(59950).format(label))
                        ADDON.setSetting('polsatgo_enabled', 'true')
                        kb = xbmc.Keyboard('','')
                        kb.setHeading(strings(59952) + ' ({})'.format(label))
                        kb.setHiddenInput(False)
                        kb.doModal()
                        login = kb.getText() if kb.isConfirmed() else self.tutorialGetService()
                        if login == '': login = self.tutorialGetService()

                        if login != '':
                            ADDON.setSetting('polsatgo_username', login)
                            kb = xbmc.Keyboard('','')
                            kb.setHeading(strings(59953) + ' ({})'.format(label))
                            kb.setHiddenInput(True)
                            kb.doModal()
                            pswd = kb.getText() if kb.isConfirmed() else self.tutorialGetService()
                            if pswd == '': pswd = self.tutorialGetService()

                            ADDON.setSetting('polsatgo_password', pswd)
                            if pswd != '':
                                progExec = True

                                res = xbmcgui.Dialog().select(strings(95014), ['Ipla', 'Polsat Box'])

                                if res < 0:
                                    ADDON.setSetting('polsatgo_enabled', 'false')
                                    self.tutorialGetService()

                                elif res == 0:
                                    ADDON.setSetting('polsatgo_client', 'Ipla')

                                elif res == 1:
                                    ADDON.setSetting('polsatgo_client', 'Polsat Box')

                            else:
                                ADDON.setSetting('polsatgo_enabled', 'false')
                                self.tutorialGetService()

                        else:
                            ADDON.setSetting('polsatgo_enabled', 'false')
                            self.tutorialGetService()

                    if s == 5:
                        label = 'Polsat GO Box'
                        xbmcgui.Dialog().ok(label, strings(59950).format(label))
                        ADDON.setSetting('pgobox_enabled', 'true')
                        kb = xbmc.Keyboard('','')
                        kb.setHeading(strings(59952) + ' ({})'.format(label))
                        kb.setHiddenInput(False)
                        kb.doModal()
                        login = kb.getText() if kb.isConfirmed() else self.tutorialGetService()
                        if login == '': login = self.tutorialGetService()

                        if login != '':
                            ADDON.setSetting('pgobox_username', login)
                            kb = xbmc.Keyboard('','')
                            kb.setHeading(strings(59953) + ' ({})'.format(label))
                            kb.setHiddenInput(True)
                            kb.doModal()
                            pswd = kb.getText() if kb.isConfirmed() else self.tutorialGetService()
                            if pswd == '': pswd = self.tutorialGetService()

                            ADDON.setSetting('pgobox_password', pswd)
                            if pswd != '':
                                progExec = True

                                res = xbmcgui.Dialog().select(strings(95014), ['Cyfrowy Polsat', 'Ipla', 'Polsat Box'])

                                if res < 0:
                                    ADDON.setSetting('pgobox_enabled', 'false')
                                    self.tutorialGetService()

                                if res == 0:
                                    ADDON.setSetting('pgobox_client', 'Cyfrowy Polsat')

                                elif res == 1:
                                    ADDON.setSetting('pgobox_client', 'Ipla')

                                elif res == 2:
                                    ADDON.setSetting('pgobox_client', 'Polsat Box')

                            else:
                                ADDON.setSetting('pgobox_enabled', 'false')
                                self.tutorialGetService()

                        else:
                            ADDON.setSetting('pgobox_enabled', 'false')
                            self.tutorialGetService()

                    if s == 6:
                        label = 'TVP GO'
                        xbmcgui.Dialog().ok(label, label + ' ' + strings(30733).lower())
                        ADDON.setSetting('tvpgo_enabled', 'true')
                        progExec = True

                    if s == 7:
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

                                res = xbmcgui.Dialog().select(strings(95014), ['teliatv.dk', 'teliaplay.se'])

                                if res < 0:
                                    ADDON.setSetting('teliaplay_enabled', 'false')
                                    self.tutorialGetService()

                                if res == 0:
                                    ADDON.setSetting('teliaplay_locale', 'teliatv.dk')

                                elif res == 1:
                                    ADDON.setSetting('teliaplay_locale', 'teliaplay.se')

                            else:
                                ADDON.setSetting('teliaplay_enabled', 'false')
                                self.tutorialGetService()

                        else:
                            ADDON.setSetting('teliaplay_enabled', 'false')
                            self.tutorialGetService()

                    if s == 8:
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

            if p == 1:
                ADDON.setSetting('nr_of_playlists', '1')
                ADDON.setSetting('playlist_1_enabled', 'true')
                res = xbmcgui.Dialog().select(strings(59954), [strings(59906), strings(59908)])

                if res < 0:
                    res = xbmcgui.Dialog().yesno(strings(59924), strings(59938), yeslabel=strings(59939), nolabel=strings(30308))
                    if res: 
                        self.tutorialGetService()
                    else:
                        ADDON.setSetting('nr_of_playlists', '0')
                        ADDON.setSetting('playlist_1_enabled', 'false')
                        ADDON.setSetting('playlist_1_file', '')
                        ADDON.setSetting('tutorial', 'true')
                        self.exitAddon()

                elif res == 0:
                    ADDON.setSetting('playlist_1_source', '0')
                    txt = ADDON.getSetting('playlist_1_url')
                    if txt == 'http://' or txt == 'https://' or txt == '':
                        txt = 'https://'
                    kb = xbmc.Keyboard(txt,'')
                    kb.setHeading(strings(59955))
                    kb.setHiddenInput(False)
                    kb.doModal()
                    c = kb.getText() if kb.isConfirmed() else None
                    if c == '': c = None

                    ADDON.setSetting('playlist_1_url', c)
                    if c is not None:
                        progExec = True

                    else:
                        self.tutorialGetService()

                elif res == 1:
                    ADDON.setSetting('playlist_1_source', '1')
                    fn = xbmcgui.Dialog().browse(1, strings(59956), '')
                    ADDON.setSetting('playlist_1_file', fn)
                    if fn != '':
                        progExec = True
                    else:
                        self.tutorialGetService()

        if progExec:
            self.tutorialCatchup(False)

    def tutorialCatchup(self, playlist):
        res = xbmcgui.Dialog().yesno(strings(59924), strings(60013))
        if res:
            ADDON.setSetting('archive_support', 'true')
            if playlist:
                ret = xbmcgui.Dialog().select(strings(59989), [strings(70007), strings(59990), strings(59996), strings(59999)])
                if ret < 0:
                    self.tutorialCatchup(playlist)

                if ret == 0:
                    ADDON.setSetting('archive_type', '0')
                    self.tutorialGetRecording()

                elif ret == 1:
                    ADDON.setSetting('archive_type', '1')
                    kb = xbmc.Keyboard('?utc={utc}&lutc={lutc}','')
                    kb.setHeading(strings(59977))
                    kb.setHiddenInput(False)
                    kb.doModal()
                    c = kb.getText() if kb.isConfirmed() else None
                    if c == '': c = None

                    if c is not None:
                        self.tutorialGetRecording()
                    else:
                        self.tutorialCatchup(playlist)

                elif ret == 2:
                    ADDON.setSetting('archive_type', '2')
                    self.tutorialGetRecording()

                elif ret == 3:
                    ADDON.setSetting('archive_type', '3')
                    self.tutorialGetRecording()

            else:
                ADDON.setSetting('archive_type', '0')
                self.tutorialGetRecording()
        else:
            ADDON.setSetting('archive_support', 'false')
            self.tutorialGetRecording()

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
                    self.restartKodi()
                    time.sleep(5)

            else:
                run = SettingsImp().downloadRecordApp()
                ADDON.setSetting('tutorial', 'false')
                xbmcgui.Dialog().ok(strings(70100), strings(70102))
                self.restartKodi()
                time.sleep(5)

        else:
            ADDON.setSetting('tutorial', 'false')
            xbmcgui.Dialog().ok(strings(70100), strings(70102))
            self.restartKodi()
            time.sleep(5)

    def tutorialExec(self):
        if ADDON.getSetting('tutorial') == 'false':
            if ADDON.getSetting('source') == '0':
                if ADDON.getSetting('xmltv_file') == '':
                    ADDON.setSetting('tutorial', 'true')
                else:
                    ADDON.setSetting('tutorial', 'false')

            if ADDON.getSetting('source') == '1':
                if ADDON.getSetting('m-TVGuide') == 'http://' or ADDON.getSetting('m-TVGuide') == 'https://' or ADDON.getSetting('m-TVGuide') == '':
                    ADDON.setSetting('tutorial', 'true')
                else:
                    ADDON.setSetting('tutorial', 'false')

        if ADDON.getSetting('tutorial') == 'true':
            res = xbmcgui.Dialog().yesno(strings(59924), strings(59959))
            if res == False:
                ADDON.setSetting('tutorial', 'false')
                self.exitAddon()

            elif res == True:
                res = xbmcgui.Dialog().ok(strings(59924), strings(59960))
                if res == False:
                    xbmcgui.Dialog().ok(strings(59924), strings(59938))
                    ADDON.setSetting('tutorial', 'true')
                    self.exitAddon()
                else:
                    self.tutorialGetEPG()

            else:
                ADDON.setSetting('tutorial', 'true')
                self.exitAddon()

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
            if PY3:
                checkProfileFonts = list(filter(r.match, item))
            else:
                checkProfileFonts = filter(r.match, item)

        checkDirKodi = xbmcvfs.listdir(os.path.join(self.kodiSkinPath, 'fonts', addonSkin))
        for item in checkDirKodi:
            r = re.compile('(.*?).ttf')
            if PY3:
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
            if PY3:
                import functools 
                check = functools.reduce(lambda i, j : i and j, map(lambda m, k: m == k, checkProfileFonts, checkKodiFonts), True)
            else:
                check = set(checkProfileFonts) == set(checkKodiFonts)

            deb('Skin check: {}'.format(check))
            deb('Skin fonts: {}'.format(font))
            deb('Skin match: {}'.format(match))

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
                    self.exitAddon()

                if res == 0:
                    # Check non-writeable skins
                    if chkSkinKodi == 'skin.estuary':
                        if xbmc.getSkinDir() == "skin.estuary":
                            sk = xbmcaddon.Addon(id="skin.estuary")
                            skinpath = sk.getAddonInfo("path")

                            if xbmcgui.Dialog().yesno(strings(70105), strings(70118).format(chkSkinKodi)):
                                if PY3:
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
                                self.exitAddon()

                    if chkSkinKodi == 'skin.estouchy':
                        if xbmc.getSkinDir() == "skin.estouchy":
                            sk = xbmcaddon.Addon(id="skin.estouchy")
                            skinpath = sk.getAddonInfo("path")

                            if xbmcvfs.listdir(os.path.join(self.kodiPath, 'addons', 'skin.estouchy')) == False:
                                if xbmcgui.Dialog().yesno(strings(70105), strings(70118).format(chkSkinKodi)):
                                    if PY3:
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
                                    self.exitAddon()

                    path2 = 'xml'
                    path3 = 'xml'
                    path4 = 'xml'

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
                                   lambda m: str(int(m.group(0)) // 1.5), fileContent)
                        file_font_size = xbmcvfs.File(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, path2, 'Font.temp'), 'w+')
                        file_font_size.write(newSize)
                        file_font_size.close()

                    elif profile_xml == 1 and kodi_720p == 1:
                        newSize = re.sub(r"(?s)(?<=<size>)\d+(?=</size>)",
                                   lambda m: str(int(m.group(0)) // 1.5), fileContent)
                        file_font_size = xbmcvfs.File(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, path2, 'Font.temp'), 'w+')
                        file_font_size.write(newSize)
                        file_font_size.close()

                    elif profile_16x9 == 1 and kodi_720p == 1:
                        newSize = re.sub(r"(?s)(?<=<size>)\d+(?=</size>)",
                                   lambda m: str(int(m.group(0)) // 1.5), fileContent)
                        file_font_size = xbmcvfs.File(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, path2, 'Font.temp'), 'w+')
                        file_font_size.write(newSize)
                        file_font_size.close()

                    elif profile_720p == 1 and kodi_1080i == 1:
                        newSize = re.sub(r"(?s)(?<=<size>)\d+(?=</size>)", 
                                    lambda m: str(int(m.group(0)) * 1.5), fileContent)
                        file_font_size = xbmcvfs.File(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, path2, 'Font.temp'), 'w+')
                        file_font_size.write(newSize)
                        file_font_size.close()

                    elif profile_720p == 1 and kodi_xml == 1:
                        newSize = re.sub(r"(?s)(?<=<size>)\d+(?=</size>)",
                                    lambda m: str(int(m.group(0)) * 1.5), fileContent)
                        file_font_size = xbmcvfs.File(os.path.join(self.profilePath, 'resources', 'skins', addonSkin, path2, 'Font.temp'), 'w+')
                        file_font_size.write(newSize)
                        file_font_size.close()

                    elif profile_720p == 1 and kodi_16x9 == 1:
                        newSize = re.sub(r"(?s)(?<=<size>)\d+(?=</size>)",
                                    lambda m: str(int(m.group(0)) * 1.5), fileContent)
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
                        removeContent = re.sub(r'\t</fontset>\s<fontset', '\t</fontset>\n\t<fontset', str(removeContent))
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
                        self.restartKodi()
                    else:
                        xbmcgui.Dialog().ok(strings(70105), strings(70103))
                        self.exitAddon()

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
                        self.exitAddon()


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
        deb("########### onPlayerStateChanged {}, pstate: {} ###########".format(pstate, ADDON.getSetting('info_osd')))
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

    def reloadSkin(self):
        try:
            if ADDON.getSetting('skin_fontpack') == 'true':
                xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Settings.SetSettingValue","id":1,"params":{"setting":"lookandfeel.font","value":"Default"}}')
        except:
            None

    def close(self, background=False):
        deb('close')
        xbmc.executebuiltin('Dialog.Close(busydialog)')

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
                    if xbmc.Monitor().waitForAbort(1):
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
                self.reloadSkin()
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

        ADDON.setSetting('epg_size', '0')

        self.interval = 900
        self.updateEpgTimer = epgTimer(self.interval, self.updateEpg)

        self.getListLenght = self.getChannelListLenght()

    def updateEpg(self):
        if ADDON.getSetting('epg_interval') == '0':
            epgSize = ADDON.getSetting('epg_size')
            epgDbSize = self.database.source.getEpgSize()
            if epgDbSize == '' or epgDbSize is None:
                epgDbSize = 0

            #deb('getEpgSize: {}'.format(epgSize))
            #deb('getEpgDbSize: {}'.format(epgDbSize))

            if ADDON.getSetting('epg_size') == '0':
                ADDON.setSetting('epg_size', str(epgDbSize))

            if int(epgSize) != int(epgDbSize):
                if xbmc.Player().isPlaying() and self.mode == MODE_TV:
                    self.onRedrawEPGPlaying(self.channelIdx, self.viewStartDate)
                else:
                    self.onRedrawEPG(self.channelIdx, self.viewStartDate, self._getCurrentProgramFocus)
                ADDON.setSetting('epg_size', str(epgDbSize))

    def getStreamsCid(self, channels):
        streams = self.database.getAllCatchupUrlList(channels)
        #deb('getAllCatchupUrlList: {}'.format(streams))

        if PY3:
            streams = streams.items()
        else:
            streams = streams.iteritems()

        catchupList = {}

        p = re.compile('service=.*_(TS|AR)_(.*?)(_.*)?$')

        for k,v in streams:
            v = list(v)
            dayList = []

            channel = k
            days = v

            for day in days:
                if p.match(day):
                    day = p.search(day).group(2)
                    dayList.append(day)

                    if dayList:
                        d = max(dayList)
                    else:
                        d = ''

                    catchupList.update({channel.upper():d})

        return catchupList

    def catchupEPG(self, program, cellWidth, catchupList):
        addonSkin = ADDON.getSetting('Skin')

        archive = ''
        day = ''

        catchupList = catchupList.items()

        if catchupList:
            if program.channel.title.upper() in [k for k,v in catchupList]:
                day = [v for k,v in catchupList if k == program.channel.title.upper()][0]

        if day == '':
            day = ADDON.getSetting('archive_reverse_days')

        if day == '3H':
            reverseTime = datetime.datetime.now() - datetime.timedelta(hours = int(3)) - datetime.timedelta(minutes = 5)

        elif ADDON.getSetting('archive_reverse_auto') == '0' and day != '':
            try:
                reverseTime = datetime.datetime.now() - datetime.timedelta(hours = int(day)) * 24 - datetime.timedelta(minutes = 5)
            except:
                reverseTime = datetime.datetime.now() - datetime.timedelta(hours = int(1)) * 24 - datetime.timedelta(minutes = 5)
        else:
            try:
                reverseTime = datetime.datetime.now() - datetime.timedelta(hours = int(ADDON.getSetting('archive_manual_days'))) * 24 - datetime.timedelta(minutes = 5)
            except:
                reverseTime = datetime.datetime.now() - datetime.timedelta(hours = int(1)) * 24 - datetime.timedelta(minutes = 5)

        if ADDON.getSetting('archive_support') == 'true': 
            if program.channel.title.upper() in [k for k,v in catchupList] and program.title != program.channel.title:
                if ADDON.getSetting('archive_finished_program') == 'true':
                    #Catchup
                    if program.endDate < datetime.datetime.now():
                        if program.startDate > reverseTime:
                            if cellWidth < 35:
                                archive  = ''
                            else:
                                if skin_catchup_size == '1' or addonSkin == 'skin.confluence':
                                    archive = '[UPPERCASE][COLOR FF0cbe24][B]• [/B][/COLOR][/UPPERCASE]'
                                else:
                                    archive = '[UPPERCASE][COLOR FF0cbe24][B]● [/B][/COLOR][/UPPERCASE]'

                else:
                    #Catchup
                    if program.startDate < datetime.datetime.now():
                        if program.startDate > reverseTime:
                            if cellWidth < 35:
                                archive  = ''
                            else:
                                if skin_catchup_size == '1' or addonSkin == 'skin.confluence':
                                    archive = '[UPPERCASE][COLOR FF0cbe24][B]• [/B][/COLOR][/UPPERCASE]'
                                else:
                                    archive = '[UPPERCASE][COLOR FF0cbe24][B]● [/B][/COLOR][/UPPERCASE]'

        return archive

    def getChannelListLenght(self):
        try:
            channelList = self.database.getChannelList(onlyVisible=True)
            indexList = len(channelList)
        except:
            indexList = 0
        return indexList

    def getChannelNumber(self):
        try:
            controlInFocus = self.getFocus()
            program = self._getProgramFromControl(controlInFocus)
            index = self.database.getCurrentChannelIdx(program.channel) + 1
            return index
        except:
            pass

    def AutoPlayByNumber(self):
        deb('AutoPlayByNumber')
        self.viewStartDate = datetime.datetime.today() + datetime.timedelta(minutes=int(timebarAdjust()))
        self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)
        channelList = self.database.getChannelList(onlyVisible=True)
        self.channelIdx = int(ADDON.getSetting('autostart_channel_number')) - 1

        try:
            index = channelList[self.channelIdx]
        except:
            if channelList:
                index = channelList[0]
            else:
                return

        now = datetime.datetime.now()

        if PY3:
            start = str(datetime.datetime.timestamp(now))
        else:
            start = str(int(time.mktime(now.timetuple())))

        program = self.database.getProgramStartingAt(index, start, None)
        if not program:
            program = Program(channel=index, title='', startDate='', endDate='', description='', productionDate='', director='', actor='', episode='', 
                imageLarge='', imageSmall='', categoryA='', categoryB='')

        xbmc.sleep(350)
        if not xbmc.Player().isPlaying():
            self.playChannel(program.channel)

    def AutoPlayLastChannel(self):
        deb('AutoPlayLastChannel')
        self.viewStartDate = datetime.datetime.today() + datetime.timedelta(minutes=int(timebarAdjust()))
        self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)
        channelList = self.database.getChannelList(onlyVisible=True)
        idx, start, end, played = self.database.getLastChannel()
        self.channelIdx = int(idx)

        try:
            index = channelList[self.channelIdx]
        except:
            if channelList:
                index = channelList[0]
            else:
                return

        now = datetime.datetime.now()

        if PY3:
            start = str(datetime.datetime.timestamp(now))
        else:
            start = str(int(time.mktime(now.timetuple())))

        program = self.database.getProgramStartingAt(index, start, None)
        if not program:
            program = Program(channel=index, title='', startDate='', endDate='', description='', productionDate='', director='', actor='', episode='', 
                imageLarge='', imageSmall='', categoryA='', categoryB='')

        xbmc.sleep(350)
        if not xbmc.Player().isPlaying():
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
        if PY3:
            return xbmc.getCondVisibility('System.AddonIsEnabled({id})'.format(id='script.extendedinfo'))
        else:
            return xbmc.getCondVisibility('System.HasAddon({id})'.format(id='script.extendedinfo'))

    def scriptChkMovieDBHelper(self):
        if PY3:
            return xbmc.getCondVisibility('System.AddonIsEnabled({id})'.format(id='plugin.video.themoviedb.helper'))
        else:
            return xbmc.getCondVisibility('System.HasAddon({id})'.format(id='plugin.video.themoviedb.helper'))

    @contextmanager
    def busyDialog(self):
        xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
        try:
            yield
        finally:
            xbmc.executebuiltin('Dialog.Close(busydialognocancel)')

    def ExtendedInfo(self, program):
        extInfo = self.scriptChkExtendedInfo()
        mvDbHelper = self.scriptChkMovieDBHelper()

        check = True

        if not extInfo and not mvDbHelper:
            check = False

        if check:
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

            if PY3:
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
                                if not PY3:
                                    title = title.encode('unicode_escape')

                                if extInfo:
                                    xbmc.executebuiltin('RunScript(script.extendedinfo,info=extendedinfo,name={title},id={id})'.format(title=title, id=id))
                                elif mvDbHelper:
                                    xbmc.executebuiltin('Dialog.Close(all,true)')
                                    xbmc.executebuiltin('ActivateWindow(Videos,"plugin://plugin.video.themoviedb.helper/?info=search&type=movie&query={title}&tmdb_id={id}",return)'.format(title=title, id=id))
                            elif ttype == 'tv':
                                if not PY3:
                                    title = program.title.encode('unicode_escape')

                                if extInfo:
                                    xbmc.executebuiltin('RunScript(script.extendedinfo,info=extendedtvinfo,name={title},id={id})'.format(title=title, id=id))
                                elif mvDbHelper:
                                    xbmc.executebuiltin('Dialog.Close(all,true)')
                                    xbmc.executebuiltin('ActivateWindow(Videos,"plugin://plugin.video.themoviedb.helper/?info=search&type=tv&query={title}&tmdb_id={id}",return)'.format(title=title, id=id))
                            else:
                                xbmcgui.Dialog().notification(strings(30353), strings(30361).format(title))

                    else:
                        if selection == 0:
                            xbmcgui.Dialog().notification(strings(30353), strings(30362).format(title))
                            search = xbmcgui.Dialog().input(strings(30322), program.title)
                            if search:
                                if not PY3:
                                    search = search.encode('unicode_escape')

                                if extInfo:
                                    xbmc.executebuiltin('RunScript(script.extendedinfo,info=extendedinfo,name={title})'.format(title=search))
                                elif mvDbHelper:
                                    xbmc.executebuiltin('Dialog.Close(all,true)')
                                    xbmc.executebuiltin('ActivateWindow(Videos,"plugin://plugin.video.themoviedb.helper/?info=search&type=movies&query={title}",return)'.format(title=title))
                            else:
                                return
                        elif selection == 1:
                            xbmcgui.Dialog().notification(strings(30353), strings(30363).format(title))
                            search = xbmcgui.Dialog().input(strings(30322), title)
                            if search:
                                if not PY3:
                                    search = search.encode('unicode_escape')

                                if extInfo:
                                    xbmc.executebuiltin('RunScript(script.extendedinfo,info=extendedtvinfo,name={title})'.format(title=search))
                                elif mvDbHelper:
                                    xbmc.executebuiltin('Dialog.Close(all,true)')
                                    xbmc.executebuiltin('ActivateWindow(Videos,"plugin://plugin.video.themoviedb.helper/?info=search&type=tv&query={title}",return)'.format(title=title))
                            else:
                                return
                        else:
                            xbmcgui.Dialog().notification(strings(30353), strings(30361).format(title))
                else:
                    if selection == 0:
                        xbmcgui.Dialog().notification(strings(30353), strings(30362).format(title))
                        search = xbmcgui.Dialog().input(strings(30322), program.title)
                        if search:
                            if not PY3:
                                search = search.encode('unicode_escape')

                            if extInfo:
                                xbmc.executebuiltin('RunScript(script.extendedinfo,info=extendedinfo,name={title})'.format(title=search))
                            elif mvDbHelper:
                                xbmc.executebuiltin('Dialog.Close(all,true)')
                                xbmc.executebuiltin('ActivateWindow(Videos,"plugin://plugin.video.themoviedb.helper/?info=search&type=movies&query={title}",return)'.format(title=search))
                        else:
                            return
                    elif selection == 1:
                        xbmcgui.Dialog().notification(strings(30353), strings(30363).format(title))
                        search = xbmcgui.Dialog().input(strings(30322), title)
                        if search:
                            if not PY3:
                                search = search.encode('unicode_escape')

                            if extInfo:
                                xbmc.executebuiltin('RunScript(script.extendedinfo,info=extendedtvinfo,name={title})'.format(title=search))
                            elif mvDbHelper:
                                xbmc.executebuiltin('Dialog.Close(all,true)')
                                xbmc.executebuiltin('ActivateWindow(Videos,"plugin://plugin.video.themoviedb.helper/?info=search&type=tv&query={title}",return)'.format(title=search))
                        else:
                            return
                    else:
                        xbmcgui.Dialog().notification(strings(30353), strings(30361).format(title))

        else:
            sel = xbmcgui.Dialog().select(strings(70100), ['script.extendedinfo', 'plugin.video.themoviedb.helper'])
            restart = True

            if sel < 0:
                return
            if sel == 0:
                selected = 'script.extendedinfo'
            elif sel == 1: 
                selected = 'plugin.video.themoviedb.helper'
                restart = False

            try:
                res = xbmc.executebuiltin('InstallAddon({0})'.format(selected))
                if not res:
                    installed = xbmc.getCondVisibility('System.HasAddon({id})'.format(id=selected))
                    if installed:
                        xbmc.executebuiltin('EnableAddon({0})'.format(selected))

            except:
                res = None

            if restart:
                if res:
                    xbmcgui.Dialog().ok(strings(57051), strings(30979))
                    self.exitAddon()
                else:
                    xbmcgui.Dialog().ok(strings(69062), strings(31021).format('{0}'.format(selected)))
                    return

    def playShortcut(self):
        self.channel_number_input = False
        self.viewStartDate = datetime.datetime.today() + datetime.timedelta(minutes=int(timebarAdjust()))
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
            try:
                index = channelList[self.channelIdx]
            except:
                if channelList:
                    index = channelList[0]
                else:
                    return

            now = datetime.datetime.now()

            if PY3:
                start = str(datetime.datetime.timestamp(now))
            else:
                start = str(int(time.mktime(now.timetuple())))

            program = self.database.getProgramStartingAt(index, start, None)
            if not program:
                program = Program(channel=index, title='', startDate='', endDate='', description='', productionDate='', director='', actor='', episode='', 
                    imageLarge='', imageSmall='', categoryA='', categoryB='')

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

        if action.getId() in [KEY_CONTEXT_MENU] and self.getFocusId() == 7900:
            self.sortCategory()

    def sortCategory(self):
        categories = []

        values = dict(self.database.getCategoryMap())

        current_categories = list(self.database.getAllCategories())

        if current_categories:
            for category in range(len(current_categories)):
                res = xbmcgui.Dialog().select(strings(30375).format(category+1), current_categories)
                if res == -1:
                    return
                elif res > -1:
                    cat = current_categories[res]
                    categories.append(cat)

                current_categories.pop(res)

            sortedvalues = sorted(values.items(), key=lambda x: categories.index(x[1]))

            self.database.saveCategoryMap(sortedvalues, True)
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)

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
            C_MAIN_RETURN_STR = strings(30912)
        else:
            background = False
            C_MAIN_EXIT_STR = strings(30981)
            C_MAIN_RETURN_STR = strings(30964)

        if action.getId() in [ACTION_PARENT_DIR, KEY_NAV_BACK, ACTION_PREVIOUS_MENU]:
            if xbmc.Player().isPlaying() or self.playService.isWorking():
                if not background:
                    self.playService.stopPlayback()
                else:
                    # Close by two returns
                    if (datetime.datetime.now() - self.lastCloseKeystroke).seconds < 3:
                        self.close(background=background)
                    else:
                        self.lastCloseKeystroke = datetime.datetime.now()
                        xbmcgui.Dialog().notification(strings(30963), C_MAIN_RETURN_STR, time=3000, sound=False)

            elif action.getButtonCode() != 0 or action.getId() == ACTION_SELECT_ITEM:
                if ADDON.getSetting('exit') == '0' and not background:
                    # Ask to close
                    if xbmc.getCondVisibility('!Window.IsVisible(10100)'): 
                        ret = xbmcgui.Dialog().yesno(strings(30963), '{}?'.format(C_MAIN_EXIT_STR))
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
                        xbmcgui.Dialog().notification(strings(30963), C_MAIN_RETURN_STR, time=3000, sound=False)

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
                prog, idx = self.getLastPlayingChannel()
                try:
                    self.currentChannel = prog.channel
                except:
                    self.currentChannel = None

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
                elif action.getId() == ACTION_GESTURE_SWIPE_UP:
                    pass
                elif action.getId() == ACTION_GESTURE_SWIPE_DOWN:
                    pass
                elif action.getId() == ACTION_GESTURE_SWIPE_LEFT:
                    pass
                elif action.getId() == ACTION_GESTURE_SWIPE_RIGHT:
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
                self.onRedrawEPG(0 - CHANNELS_PER_PAGE, self.viewStartDate, focusFunction=self._findControlAbove)
            else:
                self._up(currentFocus)
        elif action.getId() == ACTION_DOWN:
            if self.getFocusId() == 7900:
                self.focusPoint.y = self.epgView.top
                self.onRedrawEPG(0, self.viewStartDate, focusFunction=self._findControlAbove)
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
        elif action.getId() == ACTION_GESTURE_SWIPE_UP and self.getFocusId() != 7900:
            self._moveDown(scrollEvent=True)
        elif action.getId() == ACTION_GESTURE_SWIPE_DOWN and self.getFocusId() != 7900:
            self._moveUp(scrollEvent=True)
        elif action.getId() == ACTION_GESTURE_SWIPE_RIGHT and self.getFocusId() != 7900:
            self.viewStartDate -= datetime.timedelta(hours=2)
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)
        elif action.getId() == ACTION_GESTURE_SWIPE_LEFT and self.getFocusId() != 7900:
            self.viewStartDate += datetime.timedelta(hours=2)
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)
        elif action.getId() == KEY_HOME or (action.getButtonCode() == KEY_HOME2 and KEY_HOME2 != 0) or (action.getId() == KEY_HOME2 and KEY_HOME2 != 0):
            self.viewStartDate = datetime.datetime.today() + datetime.timedelta(minutes=int(timebarAdjust()))
            self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)
            self.onRedrawEPG(0, self.viewStartDate)
        elif action.getId() == KEY_END:
            self.viewStartDate = datetime.datetime.today() + datetime.timedelta(minutes=int(timebarAdjust()))
            self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)
            self.onRedrawEPG(-1, self.viewStartDate)
        elif (action.getId() in [KEY_CONTEXT_MENU, ACTION_MOUSE_RIGHT_CLICK] or action.getButtonCode() in [KEY_CONTEXT]) and controlInFocus is not None:
            program = self._getProgramFromControl(controlInFocus)
            if program is not None:
                self._showContextMenu(program)
                return

            if program is None and not self.database.getAllStreamUrlList():
                if self.getFocusId() != 7900:
                    ret = xbmcgui.Dialog().contextmenu([strings(68005), strings(30308)])

                    if ret == 0:
                        #xbmcaddon.Addon(id=ADDON_ID).openSettings()
                        self.popupMenu(program)

                    elif ret == 1:
                        self.close()

        elif action.getButtonCode() == KEY_RECORD:
            program = self._getProgramFromControl(controlInFocus)
            self.recordProgram(program)
            return

        elif action.getButtonCode() == KEY_LIST:
            program = self._getProgramFromControl(controlInFocus)
            d = xbmcgui.Dialog()
            list = d.select(strings(30309), [strings(30315), strings(30310), strings(30311), strings(30312), strings(30336), strings(30337)])

            if list < 0:
                self.onRedrawEPG(self.channelIdx, self.viewStartDate)
            if list == 0:
                self.programSearchSelect(program.channel)
            elif list == 1:
                index = self.database.getCurrentChannelIdx(program.channel)
                programList = self.database.getChannelListing(program.channel)
                self.showListing(program.channel)
            elif list == 2:
                index = self.database.getCurrentChannelIdx(program.channel)
                programList = self.database.getChannelListing(program.channel)
                self.showNow(program.channel)
            elif list == 3:
                index = self.database.getCurrentChannelIdx(program.channel)
                programList = self.database.getChannelListing(program.channel)
                self.showNext(program.channel)
            elif list == 4:
                self.showFullReminders(program.channel)
            elif list == 5:
                self.showFullRecordings(program.channel)
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
            channel = self.getLastPreviousChannel()
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

        if controlId == self.C_MAIN_SLIDE_CLICK:
            self.popupMenu(self.program)

        if controlId == self.C_MAIN_CATEGORY:
            cList = self.getControl(self.C_MAIN_CATEGORY)
            item = cList.getSelectedItem()
            if item:
                self.category = item.getLabel()

            self.database.setCategory(self.category)
            ADDON.setSetting('category', self.category)
            with self.busyDialog():
                self.onRedrawEPG(self.channelIdx == 1, self.viewStartDate)

        if controlId in [self.C_MAIN_LOADING_CANCEL, self.C_MAIN_MOUSEPANEL_EXIT]:
            if ADDON.getSetting('background_services') == 'true':
                background = True
                C_MAIN_RETURN_STR = strings(30912)
            else:
                background = False
                C_MAIN_EXIT_STR = strings(30981)
                C_MAIN_RETURN_STR = strings(30964)

            if ADDON.getSetting('exit') == '0' and not background:
                # Ask to close
                if xbmc.getCondVisibility('!Window.IsVisible(10100)'): 
                    ret = xbmcgui.Dialog().yesno(strings(30963), '{}?'.format(C_MAIN_EXIT_STR))
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
                    xbmcgui.Dialog().notification(strings(30963), C_MAIN_RETURN_STR, time=3000, sound=False)

        if self.isClosing:
            return

        if controlId == self.C_MAIN_MOUSEPANEL_HOME:
            self.viewStartDate = datetime.datetime.today() + datetime.timedelta(minutes=int(timebarAdjust()))
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
            #xbmcaddon.Addon(id=ADDON_ID).openSettings()
            self.viewStartDate = datetime.datetime.today() + datetime.timedelta(minutes=int(timebarAdjust()))
            self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)

            controlInFocus = self.getFocus()
            program = self._getProgramFromControl(controlInFocus)
            if program is not None:
                self._showContextMenu(program)
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
        d = ProgramListDialog(title, programList, channel)
        d.doModal()
        index = d.index
        action = d.action
        self.context = False
        if action == ACTION_RIGHT:
            self.showNow(programList[index].channel)
        elif action == ACTION_LEFT:
            self.showNext(programList[index].channel)
        elif action == KEY_NAV_BACK:
            self.index = -1
            d = xbmcgui.Dialog()
            list = d.select(strings(30309), [strings(30315), strings(30310), strings(30311), strings(30312), strings(30336), strings(30337)])

            if list < 0:
                if xbmc.getCondVisibility('Control.IsVisible(5001)'): 
                    self.onRedrawEPG(self.channelIdx, self.viewStartDate)
                else:
                    return
            if list == 0:
                self.programSearchSelect(channel)
            elif list == 1:
                self.showListing(programList[index].channel)
            elif list == 2:
                self.showNow(programList[index].channel)
            elif list == 3:
                self.showNext(programList[index].channel)
            elif list == 4:
                self.showFullReminders(channel)
            elif list == 5:
                self.showFullRecordings(channel)

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
        elif action == KEY_CONTEXT_MENU:
            if index > -1:
                if xbmc.getCondVisibility('!Control.IsVisible(5001)'):
                    try:
                        self.osd.closeOSD()
                    except:
                        pass
                self.context = True
                channelIdx = int(self.database.getCurrentChannelIdx(programList[index].channel))

                self.viewStartDate = programList[index].startDate + datetime.timedelta(minutes=int(timebarAdjust()))
                self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)

                self.onRedrawEPG(channelIdx, self.viewStartDate, self._getCurrentProgramFocus)

        elif action == KEY_RECORD:
            if index > -1:
                xbmc.Player().stop()
                self.recordProgram(programList[index])
                if xbmc.getCondVisibility('!Window.IsVisible(okdialog)'):
                    with self.busyDialog():
                        time.sleep(1)
                        self.showListing(programList[index].channel)
                else:
                    if xbmc.getCondVisibility('!Control.IsVisible(5001)'):
                        try:
                            self.osd.closeOSD()
                        except:
                            pass


        elif action == ACTION_STOP:
            return

        else:
            if index > -1:
                program = programList[index]
                now = datetime.datetime.now()
                start = program.startDate
                end = program.endDate
                self.playChannel2(program)
                with self.busyDialog():
                    time.sleep(1)
                    self.showListing(programList[index].channel)

    def showNow(self, channel):
        programList = self.database.getNowList(channel)
        title = strings(30311)

        d = ProgramListDialog(title, programList, channel)
        d.doModal()
        index = d.index
        action = d.action
        self.context = False
        if action == ACTION_RIGHT:
            self.showNext(programList[index].channel)
        elif action == ACTION_LEFT:
            self.showListing(programList[index].channel)
        elif action == KEY_NAV_BACK:
            self.index = -1
            d = xbmcgui.Dialog()
            list = d.select(strings(30309), [strings(30315), strings(30310), strings(30311), strings(30312), strings(30336), strings(30337)])

            if list < 0:
                if xbmc.getCondVisibility('Control.IsVisible(5001)'): 
                    self.onRedrawEPG(self.channelIdx, self.viewStartDate)
                else:
                    return
            if list == 0:
                self.programSearchSelect(channel)
            elif list == 1:
                self.showListing(programList[index].channel)
            elif list == 2:
                self.showNow(programList[index].channel)
            elif list == 3:
                self.showNext(programList[index].channel)
            elif list == 4:
                self.showFullReminders(channel)
            elif list == 5:
                self.showFullRecordings(channel)

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

        elif action == KEY_CONTEXT_MENU:
            if index > -1:
                if xbmc.getCondVisibility('!Control.IsVisible(5001)'):
                    try:
                        self.osd.closeOSD()
                    except:
                        pass
                self.context = True
                channelIdx = int(self.database.getCurrentChannelIdx(programList[index].channel))

                self.viewStartDate = programList[index].startDate + datetime.timedelta(minutes=int(timebarAdjust()))
                self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)

                self.onRedrawEPG(channelIdx, self.viewStartDate, self._getCurrentProgramFocus)

        elif action == KEY_RECORD:
            if index > -1:
                self.recordProgram(programList[index])
                if xbmc.getCondVisibility('!Window.IsVisible(okdialog)'):
                    with self.busyDialog():
                        time.sleep(1)
                        self.showNow(programList[index].channel)
                else:
                    if xbmc.getCondVisibility('!Control.IsVisible(5001)'):
                        try:
                            self.osd.closeOSD()
                        except:
                            pass

        elif action == ACTION_STOP:
            return

        else:
            if index > -1:
                program = programList[index]
                now = datetime.datetime.now()
                start = program.startDate
                end = program.endDate
                self.playChannel2(program)
                with self.busyDialog():
                    time.sleep(1)
                    self.showNow(programList[index].channel)

    def showNext(self, channel):
        programList = self.database.getNextList(channel)
        title = strings(30312)

        d = ProgramListDialog(title, programList, channel)
        d.doModal()
        index = d.index
        action = d.action
        self.context = False
        if action == ACTION_LEFT:
            self.showNow(programList[index].channel)
        elif action == ACTION_RIGHT:
            self.showListing(programList[index].channel)
        elif action == KEY_NAV_BACK:
            self.index = -1
            d = xbmcgui.Dialog()
            list = d.select(strings(30309), [strings(30315), strings(30310), strings(30311), strings(30312), strings(30336), strings(30337)])

            if list < 0:
                if xbmc.getCondVisibility('Control.IsVisible(5001)'): 
                    self.onRedrawEPG(self.channelIdx, self.viewStartDate)
                else:
                    return
            if list == 0:
                self.programSearchSelect(channel)
            elif list == 1:
                self.showListing(programList[index].channel)
            elif list == 2:
                self.showNow(programList[index].channel)
            elif list == 3:
                self.showNext(programList[index].channel)
            elif list == 4:
                self.showFullReminders(channel)
            elif list == 5:
                self.showFullRecordings(channel)

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

        elif action == KEY_CONTEXT_MENU:
            if index > -1:
                if xbmc.getCondVisibility('!Control.IsVisible(5001)'):
                    try:
                        self.osd.closeOSD()
                    except:
                        pass
                self.context = True
                channelIdx = int(self.database.getCurrentChannelIdx(programList[index].channel))

                self.viewStartDate = programList[index].startDate + datetime.timedelta(minutes=int(timebarAdjust()))
                self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)

                self.onRedrawEPG(channelIdx, self.viewStartDate, self._getCurrentProgramFocus)

        elif action == KEY_RECORD:
            if index > -1:
                self.recordProgram(programList[index])
                if xbmc.getCondVisibility('!Window.IsVisible(okdialog)'):
                    with self.busyDialog():
                        time.sleep(1)
                        self.showNext(programList[index].channel)
                else:
                    if xbmc.getCondVisibility('!Control.IsVisible(5001)'):
                        try:
                            self.osd.closeOSD()
                        except:
                            pass

        elif action == ACTION_STOP:
            return

        else:
            if index > -1:
                program = programList[index]
                now = datetime.datetime.now()
                start = program.startDate
                end = program.endDate
                self.playChannel2(program)
                with self.busyDialog():
                    time.sleep(1)
                    self.showNext(programList[index].channel)

    def programSearchSelect(self, channel):
        d = xbmcgui.Dialog()
        what = d.select(strings(30315), [strings(30316), strings(30317), strings(30318), strings(30343), strings(30319)])

        if what == -1:
            d = xbmcgui.Dialog()
            list = d.select(strings(30309), [strings(30315), strings(30310), strings(30311), strings(30312), strings(30336), strings(30337)])

            if list < 0:
                if xbmc.getCondVisibility('Control.IsVisible(5001)'): 
                    self.onRedrawEPG(self.channelIdx, self.viewStartDate)
                else:
                    return
            if list == 0:
                self.programSearchSelect(channel)
            elif list == 1:
                index = self.database.getCurrentChannelIdx(channel)
                programList = self.database.getChannelListing(channel)
                self.showListing(programList[index].channel)
            elif list == 2:
                index = self.database.getCurrentChannelIdx(channel)
                programList = self.database.getChannelListing(channel)
                self.showNow(programList[index].channel)
            elif list == 3:
                index = self.database.getCurrentChannelIdx(channel)
                programList = self.database.getChannelListing(channel)
                self.showNext(programList[index].channel)
            elif list == 4:
                self.showFullReminders(channel)
            elif list == 5:
                self.showFullRecordings(channel)

        if what == 0:
            self.programSearch()
            self.index = -1
            if not self.context:
                self.programSearchSelect(channel)

        elif what == 1:
            self.descriptionSearch()
            self.index = -1
            if not self.context:
                self.programSearchSelect(channel)
        elif what == 2:
            self.categorySearchInput()
            self.index = -1
            if not self.context:
                self.programSearchSelect(channel)
        elif what == 3:
            self.categorySearch()
            self.index = -1
            if not self.context:
                self.programSearchSelect(channel)
        elif what == 4:
            self.channelSearch(channel)
            self.index = -1
            if not self.context:
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
        self.context = False
        actions = [strings(30320), strings(30321)] + searches
        action = d.select(strings(30327).format(title), actions)
        if action == -1:
            return
        elif action == 0:
            pass
        elif action == 1:
            which = d.multiselect(strings(30321), searches)
            if which is None:
                return
            else:
                for item in reversed(which):
                    del searches[item]

                f = xbmcvfs.File(file_name, "wb")
                if sys.version_info[0] < 3:
                    searches = [x.decode('utf-8') for x in searches]
                f.write(bytearray('\n'.join(searches), 'utf-8'))
                f.close()
                return
        else:
            title = searches[action - 2]

        if action == 0:
            search = d.input(strings(30322), title)
        else:
            if PY3:
                search = title
            else:
                search = title.encode('utf-8')

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
        d = ProgramListDialog(title=title, programs=programList, sort_time=ADDON.getSetting('listing_sort_time') == 'true')
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

        elif action == KEY_CONTEXT_MENU:
            if index > -1:
                if xbmc.getCondVisibility('!Control.IsVisible(5001)'):
                    try:
                        self.osd.closeOSD()
                    except:
                        pass
                self.context = True
                channelIdx = int(self.database.getCurrentChannelIdx(programList[index].channel))

                self.viewStartDate = programList[index].startDate + datetime.timedelta(seconds=5, microseconds=000) + datetime.timedelta(minutes=int(timebarAdjust()))
                self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)

                self.onRedrawEPG(channelIdx, self.viewStartDate, self._getCurrentProgramFocus)

        elif action == KEY_RECORD:
            if index > -1:
                self.recordProgram(programList[index])
                if xbmc.getCondVisibility('!Window.IsVisible(okdialog)'):
                    with self.busyDialog():
                        time.sleep(1)
                        self.programSearch(programList[index].channel)
                else:
                    if xbmc.getCondVisibility('!Control.IsVisible(5001)'):
                        try:
                            self.osd.closeOSD()
                        except:
                            pass

        elif action == ACTION_STOP:
            return

        else:
            if index > -1:
                program = programList[index]
                now = datetime.datetime.now()
                start = program.startDate
                end = program.endDate
                self.playChannel2(program)
                with self.busyDialog():
                    time.sleep(1)
                    self.programSearch(programList[index].channel)

    def descriptionSearch(self):
        d = xbmcgui.Dialog()
        title = ''
        file_name = os.path.join(self.profilePath, 'synopsis_search.list')
        f = xbmcvfs.File(file_name, "rb")
        searches = sorted(f.read().splitlines())
        f.close()
        self.context = False
        actions = [strings(30320), strings(30321)] + searches
        action = d.select(strings(30328), actions)
        if action == -1:
            return
        elif action == 0:
            pass
        elif action == 1:
            which = d.multiselect(strings(30321), searches)
            if which is None:
                return
            else:
                for item in reversed(which):
                    del searches[item]

                f = xbmcvfs.File(file_name, "wb")
                if sys.version_info[0] < 3:
                    searches = [x.decode('utf-8') for x in searches]
                f.write(bytearray('\n'.join(searches), 'utf-8'))
                f.close()
                return
        else:
            title = searches[action - 2]

        if action == 0:
            search = d.input(strings(30323), title)
        else:
            if PY3:
                search = title
            else:
                search = title.encode('utf-8')

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
        d = ProgramListDialog(title=title, programs=programList, sort_time=ADDON.getSetting('listing_sort_time') == 'true')
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

        elif action == KEY_CONTEXT_MENU:
            if index > -1:
                if xbmc.getCondVisibility('!Control.IsVisible(5001)'):
                    try:
                        self.osd.closeOSD()
                    except:
                        pass
                self.context = True
                channelIdx = int(self.database.getCurrentChannelIdx(programList[index].channel))

                self.viewStartDate = programList[index].startDate + datetime.timedelta(seconds=5, microseconds=000) + datetime.timedelta(minutes=int(timebarAdjust()))
                self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)

                self.onRedrawEPG(channelIdx, self.viewStartDate, self._getCurrentProgramFocus)

        elif action == KEY_RECORD:
            if index > -1:
                self.recordProgram(programList[index])
                if xbmc.getCondVisibility('!Window.IsVisible(okdialog)'):
                    with self.busyDialog():
                        time.sleep(1)
                        self.descriptionSearch(programList[index].channel)
                else:
                    if xbmc.getCondVisibility('!Control.IsVisible(5001)'):
                        try:
                            self.osd.closeOSD()
                        except:
                            pass

        elif action == ACTION_STOP:
            return

        else:
            if index > -1:
                program = programList[index]
                now = datetime.datetime.now()
                start = program.startDate
                end = program.endDate
                self.playChannel2(program)
                with self.busyDialog():
                    time.sleep(1)
                    self.descriptionSearch(programList[index].channel)

    def categorySearchInput(self):
        d = xbmcgui.Dialog()
        title = ''
        file_name = os.path.join(self.profilePath, 'category_search.list')
        f = xbmcvfs.File(file_name, "rb")
        searches = sorted(f.read().splitlines())
        f.close()
        self.context = False
        actions = [strings(30320), strings(30321)] + searches
        action = d.select(strings(30345), actions)
        if action == -1:
            return
        elif action == 0:
            pass
        elif action == 1:
            which = d.multiselect(strings(30321), searches)
            if which is None:
                return
            else:
                for item in reversed(which):
                    del searches[item]

                f = xbmcvfs.File(file_name, "wb")
                if sys.version_info[0] < 3:
                    searches = [x.decode('utf-8') for x in searches]
                f.write(bytearray('\n'.join(searches), 'utf-8'))
                f.close()
                return
        else:
            title = searches[action - 2]

        if action == 0:
            search = d.input(strings(30344), title)
        else:
            if PY3:
                search = title
            else:
                search = title.encode('utf-8')

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
        d = ProgramListDialog(title=title, programs=programList, sort_time=ADDON.getSetting('listing_sort_time') == 'true')
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

        elif action == KEY_CONTEXT_MENU:
            if index > -1:
                if xbmc.getCondVisibility('!Control.IsVisible(5001)'):
                    try:
                        self.osd.closeOSD()
                    except:
                        pass
                self.context = True
                channelIdx = int(self.database.getCurrentChannelIdx(programList[index].channel))

                self.viewStartDate = programList[index].startDate + datetime.timedelta(minutes=int(timebarAdjust()))
                self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)

                self.onRedrawEPG(channelIdx, self.viewStartDate, self._getCurrentProgramFocus)

        elif action == KEY_RECORD:
            if index > -1:
                self.recordProgram(programList[index])
                if xbmc.getCondVisibility('!Window.IsVisible(okdialog)'):
                    with self.busyDialog():
                        time.sleep(1)
                        self.categorySearchInput(programList[index].channel)
                else:
                    if xbmc.getCondVisibility('!Control.IsVisible(5001)'):
                        try:
                            self.osd.closeOSD()
                        except:
                            pass

        elif action == ACTION_STOP:
            return

        else:
            if index > -1:
                program = programList[index]
                now = datetime.datetime.now()
                start = program.startDate
                end = program.endDate
                self.playChannel2(program)
                with self.busyDialog():
                    time.sleep(1)
                    self.categorySearchInput(programList[index].channel)

    def categorySearch(self):
        d = xbmcgui.Dialog()
        f = xbmcvfs.File(os.path.join(self.profilePath, 'category_count.list'))

        category_count = [x.split("=", 1) for x in f.read().splitlines()]
        f.close()

        self.context = False
        categories = []
        for x in category_count:
            if not self.database.category or self.database.category == strings(30325):
                s = "{} ({})".format(x[0], x[1])
            else:
                s = x[0]

            if PY3:
                categories.append(s)
            else:
                categories.append(s.decode("utf-8"))

        which = d.select(strings(30324), categories)
        if which == -1:
            return
        category = category_count[which][0]
        programList = self.database.programCategorySearch(category)
        title = "{}".format(category)
        d = ProgramListDialog(title=title, programs=programList, sort_time=ADDON.getSetting('listing_sort_time') == 'true')
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

        elif action == KEY_CONTEXT_MENU:
            if index > -1:
                if xbmc.getCondVisibility('!Control.IsVisible(5001)'):
                    try:
                        self.osd.closeOSD()
                    except:
                        pass
                self.context = True
                channelIdx = int(self.database.getCurrentChannelIdx(programList[index].channel))

                self.viewStartDate = programList[index].startDate + datetime.timedelta(minutes=int(timebarAdjust()))
                self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)

                self.onRedrawEPG(channelIdx, self.viewStartDate, self._getCurrentProgramFocus)

        elif action == KEY_RECORD:
            if index > -1:
                self.recordProgram(programList[index])
                if xbmc.getCondVisibility('!Window.IsVisible(okdialog)'):
                    with self.busyDialog():
                        time.sleep(1)
                        self.categorySearch(programList[index].channel)
                else:
                    if xbmc.getCondVisibility('!Control.IsVisible(5001)'):
                        try:
                            self.osd.closeOSD()
                        except:
                            pass 

        elif action == ACTION_STOP:
            return

        else:
            if index > -1:
                program = programList[index]
                now = datetime.datetime.now()
                start = program.startDate
                end = program.endDate
                self.playChannel2(program)
                with self.busyDialog():
                    time.sleep(1)
                    self.categorySearch(programList[index].channel)

    def channelSearch(self, channel):
        d = xbmcgui.Dialog()
        search = d.input(strings(30326), str(channel.title))
        if not search:
            return
        programList = self.database.channelSearch(search)
        title = strings(30326)
        d = ProgramListDialog(title=title, programs=programList, sort_time=ADDON.getSetting('listing_sort_time') == 'true')
        d.doModal()
        index = d.index
        action = d.action
        self.context = False
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

        elif action == KEY_CONTEXT_MENU:
            if index > -1:
                if xbmc.getCondVisibility('!Control.IsVisible(5001)'):
                    try:
                        self.osd.closeOSD()
                    except:
                        pass
                self.context = True
                channelIdx = int(self.database.getCurrentChannelIdx(programList[index].channel))

                self.viewStartDate = programList[index].startDate + datetime.timedelta(minutes=int(timebarAdjust()))
                self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)

                self.onRedrawEPG(channelIdx, self.viewStartDate, self._getCurrentProgramFocus)

        elif action == KEY_RECORD:
            if index > -1:
                self.recordProgram(programList[index])
                if xbmc.getCondVisibility('!Window.IsVisible(okdialog)'):
                    with self.busyDialog():
                        time.sleep(1)
                        self.channelSearch(programList[index].channel)
                else:
                    if xbmc.getCondVisibility('!Control.IsVisible(5001)'):
                        try:
                            self.osd.closeOSD()
                        except:
                            pass

        elif action == ACTION_STOP:
            return

        else:
            if index > -1:
                program = programList[index]
                now = datetime.datetime.now()
                start = program.startDate
                end = program.endDate
                self.playChannel2(program)
                with self.busyDialog():
                    time.sleep(1)
                    self.channelSearch(programList[index].channel)

    def showReminders(self, channel):
        programList = self.database.getNotifications()
        title = (strings(30336))
        d = ProgramListDialog(title, programList, channel, ADDON.getSetting('listing_sort_time') == 'true')
        d.doModal()
        index = d.index
        action = d.action
        self.context = False
        if action == ACTION_RIGHT:
            self.showNext(programList[index].channel)
        elif action == ACTION_LEFT:
            self.showListing(programList[index].channel)
        elif action == KEY_NAV_BACK:
            self.index = -1
            d = xbmcgui.Dialog()
            list = d.select(strings(30309), [strings(30315), strings(30310), strings(30311), strings(30312), strings(30336), strings(30337)])
            if list < 0:
                if xbmc.getCondVisibility('Control.IsVisible(5001)'): 
                    self.onRedrawEPG(self.channelIdx, self.viewStartDate)
                else:
                    return
            if list == 0:
                self.programSearchSelect(channel)
            elif list == 1:
                index = self.database.getCurrentChannelIdx(channel)
                programList = self.database.getChannelListing(channel)
                self.showListing(programList[index].channel)
            elif list == 2:
                index = self.database.getCurrentChannelIdx(channel)
                programList = self.database.getChannelListing(channel)
                self.showNow(programList[index].channel)
            elif list == 3:
                index = self.database.getCurrentChannelIdx(channel)
                programList = self.database.getChannelListing(channel)
                self.showNext(programList[index].channel)
            elif list == 4:
                self.showFullReminders(channel)
            elif list == 5:
                self.showFullRecordings(channel)

        elif action == KEY_CONTEXT_MENU:
            if index > -1:
                if xbmc.getCondVisibility('!Control.IsVisible(5001)'):
                    try:
                        self.osd.closeOSD()
                    except:
                        pass
                self.context = True
                channelIdx = int(self.database.getCurrentChannelIdx(programList[index].channel))

                self.viewStartDate = programList[index].startDate + datetime.timedelta(minutes=int(timebarAdjust()))
                self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)

                self.onRedrawEPG(channelIdx, self.viewStartDate, self._getCurrentProgramFocus)

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

        elif action == KEY_RECORD:
            if index > -1:
                self.recordProgram(programList[index])
                if xbmc.getCondVisibility('!Window.IsVisible(okdialog)'):
                    with self.busyDialog():
                        time.sleep(1)
                        self.showReminders(programList[index].channel)
                else:
                    if xbmc.getCondVisibility('!Control.IsVisible(5001)'):
                        try:
                            self.osd.closeOSD()
                        except:
                            pass 

        elif action == ACTION_STOP:
            return

        else:
            if index > -1:
                program = programList[index]
                now = datetime.datetime.now()
                start = program.startDate
                end = program.endDate
                self.playChannel2(program)
                with self.busyDialog():
                    time.sleep(1)
                    self.showReminders(programList[index].channel)

    def showFullReminders(self, channel):
        programList = self.database.getFullNotifications(int(ADDON.getSetting('listing_days')))
        title = (strings(30336))
        d = ProgramListDialog(title, programList, channel, ADDON.getSetting('listing_sort_time') == 'true')
        d.doModal()
        index = d.index
        action = d.action
        self.context = False
        if action == ACTION_RIGHT:
            self.showNext(programList[index].channel)
        elif action == ACTION_LEFT:
            self.showListing(programList[index].channel)
        elif action == KEY_NAV_BACK:
            self.index = -1
            d = xbmcgui.Dialog()
            list = d.select(strings(30309), [strings(30315), strings(30310), strings(30311), strings(30312), strings(30336), strings(30337)])
            if list < 0:
                if xbmc.getCondVisibility('Control.IsVisible(5001)'): 
                    self.onRedrawEPG(self.channelIdx, self.viewStartDate)
                else:
                    return
            if list == 0:
                self.programSearchSelect(channel)
            elif list == 1:
                index = self.database.getCurrentChannelIdx(channel)
                programList = self.database.getChannelListing(channel)
                self.showListing(programList[index].channel)
            elif list == 2:
                index = self.database.getCurrentChannelIdx(channel)
                programList = self.database.getChannelListing(channel)
                self.showNow(programList[index].channel)
            elif list == 3:
                index = self.database.getCurrentChannelIdx(channel)
                programList = self.database.getChannelListing(channel)
                self.showNext(programList[index].channel)
            elif list == 4:
                self.showFullReminders(channel)
            elif list == 5:
                self.showFullRecordings(channel)

        elif action == KEY_CONTEXT_MENU:
            if index > -1:
                if xbmc.getCondVisibility('!Control.IsVisible(5001)'):
                    try:
                        self.osd.closeOSD()
                    except:
                        pass
                self.context = True
                channelIdx = int(self.database.getCurrentChannelIdx(programList[index].channel))

                self.viewStartDate = programList[index].startDate + datetime.timedelta(minutes=int(timebarAdjust()))
                self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)

                self.onRedrawEPG(channelIdx, self.viewStartDate, self._getCurrentProgramFocus)

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

        elif action == KEY_RECORD:
            if index > -1:
                self.recordProgram(programList[index])
                if xbmc.getCondVisibility('!Window.IsVisible(okdialog)'):
                    with self.busyDialog():
                        time.sleep(1)
                        self.showFullReminders(programList[index].channel)
                else:
                    if xbmc.getCondVisibility('!Control.IsVisible(5001)'):
                        try:
                            self.osd.closeOSD()
                        except:
                            pass

        elif action == ACTION_STOP:
            return

        else:
            if index > -1:
                program = programList[index]
                now = datetime.datetime.now()
                start = program.startDate
                end = program.endDate
                self.playChannel2(program)
                with self.busyDialog():
                    time.sleep(1)
                    self.showFullReminders(programList[index].channel)

    def showFullRecordings(self, channel):
        programList = self.database.getFullRecordings(int(ADDON.getSetting('listing_days')))
        title = (strings(30337))
        d = ProgramListDialog(title, programList, channel, ADDON.getSetting('listing_sort_time') == 'true')
        d.doModal()
        index = d.index
        action = d.action
        self.context = False
        if action == ACTION_RIGHT:
            self.showNext(programList[index].channel)
        elif action == ACTION_LEFT:
            self.showListing(programList[index].channel)
        elif action == KEY_NAV_BACK:
            self.index = -1
            d = xbmcgui.Dialog()
            list = d.select(strings(30309), [strings(30315), strings(30310), strings(30311), strings(30312), strings(30336), strings(30337)])
            if list < 0:
                if xbmc.getCondVisibility('Control.IsVisible(5001)'): 
                    self.onRedrawEPG(self.channelIdx, self.viewStartDate)
                else:
                    return
            if list == 0:
                self.programSearchSelect(channel)
            elif list == 1:
                index = self.database.getCurrentChannelIdx(channel)
                programList = self.database.getChannelListing(channel)
                self.showListing(programList[index].channel)
            elif list == 2:
                index = self.database.getCurrentChannelIdx(channel)
                programList = self.database.getChannelListing(channel)
                self.showNow(programList[index].channel)
            elif list == 3:
                index = self.database.getCurrentChannelIdx(channel)
                programList = self.database.getChannelListing(channel)
                self.showNext(programList[index].channel)
            elif list == 4:
                self.showFullReminders(channel)
            elif list == 5:
                self.showFullRecordings(channel)

        elif action == KEY_CONTEXT_MENU:
            if index > -1:
                if xbmc.getCondVisibility('!Control.IsVisible(5001)'):
                    try:
                        self.osd.closeOSD()
                    except:
                        pass
                self.context = True
                channelIdx = int(self.database.getCurrentChannelIdx(programList[index].channel))

                self.viewStartDate = programList[index].startDate + datetime.timedelta(minutes=int(timebarAdjust()))
                self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)

                self.onRedrawEPG(channelIdx, self.viewStartDate, self._getCurrentProgramFocus)

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

        elif action == KEY_RECORD:
            if index > -1:
                self.recordProgram(programList[index])
                if xbmc.getCondVisibility('!Window.IsVisible(okdialog)'):
                    with self.busyDialog():
                        time.sleep(1)
                        self.showFullRecordings(programList[index].channel)
                else:
                    if xbmc.getCondVisibility('!Control.IsVisible(5001)'):
                        try:
                            self.osd.closeOSD()
                        except:
                            pass

        elif action == ACTION_STOP:
            return

        else:
            if index > -1:
                program = programList[index]
                now = datetime.datetime.now()
                start = program.startDate
                end = program.endDate
                self.playChannel2(program)
                with self.busyDialog():
                    time.sleep(1)
                    self.showFullRecordings(programList[index].channel)


    def reloadList(self, add=""):
        with self.busyDialog():
            time.sleep(1)
            self.database.reloadServices()
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)

    def channelsRemove(self):
        p = re.compile('\s<channel id="(.*?)"', re.DOTALL)

        with open(os.path.join(self.profilePath, 'basemap_extra.xml'), 'rb') as f:
            if PY3:
                base = str(f.read(), 'utf-8')
            else:
                base = f.read().decode('utf-8')

            channList = sorted(p.findall(base))

            res = xbmcgui.Dialog().multiselect(strings(70125), channList)
            if res:
                for item in res:
                    p = re.compile('<channel id="{}".*/>\n'.format(channList[item]))
                    base = p.sub('', base)

                with open(os.path.join(self.profilePath, 'basemap_extra.xml'), 'wb') as f:
                    f.write(base.encode('utf-8'))

                removeList = []

                for item in res:
                    removeList.append(channList[item])

                self.database.removeChannel(removeList)
                self.reloadList()

            else:
                return

    def channelsSelect(self):
        res = xbmcgui.Dialog().select(strings(70116), [strings(30374), strings(59995), strings(70119)])

        if res < 0:
            return

        if res == 0:
            channels = 0
            self.letterSort(channels)

        elif res == 1:
            channels = 1
            self.letterSort(channels)

        elif res == 2:
            kb = xbmc.Keyboard('','')
            kb.setHeading(strings(70119))
            kb.setHiddenInput(False)
            kb.doModal()
            c = kb.getText() if kb.isConfirmed() else None
            if PY3:
                c = c
            else:
                c = c.decode('utf-8')
            if c == '': c = None

            if c is None:
                self.channelsSelect()

            else:
                epgChann = c
                logo = ''

                ret = xbmcgui.Dialog().yesno(strings(60010), strings(70120))

                if ret:
                    res = xbmcgui.Dialog().select(strings(70122), [strings(59919), strings(59908)])

                    if res < 0:
                        self.channelsSelect()

                    if res == 0:
                        kb = xbmc.Keyboard('','')
                        kb.setHeading(strings(70124))
                        kb.setHiddenInput(False)
                        kb.doModal()
                        c = kb.getText() if kb.isConfirmed() else None
                        if PY3:
                            c = c
                        else:
                            c = c.decode('utf-8')
                        if c == '': c = None

                        logo = c

                        if c is None:
                            self.channelsSelect()

                    elif res == 1:
                        fn = xbmcgui.Dialog().browse(1, strings(70123), '')
                        if fn != '':
                            logo = fn
                        else:
                            self.channelsSelect()

                else:
                    logo = ''

                if epgChann != '':
                    newChannel = epgChann
                    self.channelsFromStream(epgChann=epgChann, newChannel=newChannel, logo=logo)

    def letterSort(self, channels):
        epgList = []

        v = ([channel.title.upper() for channel in self.database.getChannelList(customCategory=strings(30325)) if channel.title.upper()])
        n = ([channel.title.upper() for channel in self.database.getAllChannelList() if channel.title.upper()])

        epgList = v + n
        epgList = list(collections.OrderedDict.fromkeys(epgList)) #list(dict.fromkeys(epgList))

        if channels < 2:
            if channels == 0:
                res = xbmcgui.Dialog().select(strings(59994), [strings(30988), strings(59997)])

                if res < 0:
                    self.channelsSelect()

                if res == 0:
                    epgList = sorted(epgList)

                    if epgList:
                        self.channelsFromEPG(epgList, channels)
                    else:
                        xbmcgui.Dialog().ok(strings(31009), strings(30376))
                        self.channelsSelect()

                elif res == 1:
                    letterList = [chr(chNum) for chNum in list(range(ord('0'), ord('9')+1)) + list(range(ord('A'), ord('Z')+1))]
                    res = xbmcgui.Dialog().select(strings(59994), letterList)

                    if res < 0:
                        self.letterSort(channels)

                    else:
                        check = letterList[res]
                        epgList = [idx for idx in epgList if idx[0].lower() == check.lower()] 
                        epgList = sorted(epgList)

                        if epgList:
                            self.channelsFromEPG(epgList, channels)
                        else:
                            xbmcgui.Dialog().ok(strings(31009), strings(30376))
                            self.channelsSelect()

            elif channels == 1:
                res = xbmcgui.Dialog().select(strings(59994), [strings(30988), strings(59997)])

                if res < 0:
                    self.channelsSelect()

                if res == 0:
                    epgList = [idx for idx in n if not idx in v]
                    epgList = sorted(epgList)

                    if epgList:
                        self.channelsFromEPG(epgList, channels)
                    else:
                        xbmcgui.Dialog().ok(strings(31009), strings(30376))
                        self.channelsSelect()

                elif res == 1:
                    letterList = [chr(chNum) for chNum in list(range(ord('0'), ord('9')+1)) + list(range(ord('A'), ord('Z')+1))]
                    res = xbmcgui.Dialog().select(strings(59994), letterList)

                    if res < 0:
                        self.letterSort(channels)

                    else:
                        check = letterList[res]
                        epgList = [idx for idx in n if idx[0].lower() == check.lower() and idx not in v]
                        epgList = sorted(epgList)

                        if epgList:
                            self.channelsFromEPG(epgList, channels)
                        else:
                            xbmcgui.Dialog().ok(strings(31009), strings(30376))
                            self.channelsSelect()
        else:
            self.channelsSelect()

    def channelsFromEPG(self, epgList, channels):
        res = xbmcgui.Dialog().select(strings(59991), epgList)

        if res < 0:
            self.letterSort(channels)

        else:
            epgChann = epgList[res]
            self.channelsFromStream(epgChann=epgChann, epgList=epgList, channels=channels)

    def channelsFromStream(self, epgChann="", epgList="", channels="", newChannel="", logo=""):
        file = xbmcvfs.File(os.path.join(self.profilePath, 'custom_channels.list'), 'r')
        strmList = file.read().splitlines()

        strmList = sorted(set(strmList))
        strmList = [x.split(',')[0].strip('(\'\')').strip() for x in strmList if x.split(',')[0].strip('(\'\')').strip()]

        res = xbmcgui.Dialog().select(strings(59994), [strings(30988), strings(59997)])

        if res < 0:
            if epgList != '':
                self.channelsFromEPG(epgList, channels)
            else:
                self.channelsSelect()

        elif res == 0:
            if strmList:
                res = xbmcgui.Dialog().select(strings(59992) + ': [COLOR gold]' + epgChann + '[/COLOR]', strmList)
                if res < 0:
                    if epgList != '':
                        self.channelsFromStream(epgChann=epgChann, epgList=epgList, channels=channels)
                    else:
                        self.channelsSelect()
                else:
                    regChann = strmList[res]
                    self.channelRegex(epgChann, regChann, newChannel)
            else:
                xbmcgui.Dialog().ok(strings(31009), strings(30376))
                if epgList != '':
                    self.channelsFromStream(epgChann=epgChann, epgList=epgList, channels=channels)
                else:
                    self.channelsSelect()

        elif res == 1:
            letterList = [chr(chNum) for chNum in list(range(ord('0'), ord('9')+1)) + list(range(ord('A'), ord('Z')+1))]
            res = xbmcgui.Dialog().select(strings(59994), letterList)

            if res < 0:
                if epgList != '':
                    self.channelsFromStream(epgChann=epgChann, epgList=epgList, channels=channels)
                else:
                    self.channelsSelect()

            else:
                check = letterList[res]
                strmList = [idx for idx in strmList if idx[0].lower() == check.lower()] 
                strmList = sorted(strmList)

                if strmList:
                    res = xbmcgui.Dialog().select(strings(59992) + ': [COLOR gold]' + epgChann + '[/COLOR]', strmList)

                    if res < 0:
                        if epgList != '':
                            self.channelsFromStream(epgChann=epgChann, epgList=epgList, channels=channels)
                        else:
                            self.channelsSelect()
                    else:
                        regChann = strmList[res]
                        self.channelRegex(epgChann, regChann, newChannel)
                else:
                    xbmcgui.Dialog().ok(strings(31009), strings(30376))
                    if epgList != '':
                        self.channelsFromStream(epgChann=epgChann, epgList=epgList, channels=channels)
                    else:
                        self.channelsSelect()

        #elif res == 2:
            #self.channelRegex(epgChann, epgChann, newChannel)


    def channelRegex(self, epgChann, regChann, newChannel="", logo=""):
        # regex format
        if PY3:
            regChann = unidecode(regChann)
        else:
            regChann = unidecode(regChann.decode('utf-8'))

        regChann = re.sub('[ ](?=[ ])|[^-_,^A-Za-z0-9 ]+', '.?', regChann)

        regex = '(?='+regChann.upper()+'$)'.replace(' ', r'\s*')

        regex = re.sub('  ', ' ', str(regex))
        regex = re.sub(' ', '\\ s *', str(regex))
        regex = re.sub('\+', '(\\ +|PLUS)', str(regex))
        regex = re.sub('\-', '(\\ -|\\ s *)', str(regex))
        regex = re.sub('&', '(and|&amp;)', str(regex))
        regex = re.sub(' ', '', str(regex))

        # add to basemap
        item = '<channel id="{}"\t\t\t\t\t\t\t\t\ttitle="{}" strm=""/>'.format(epgChann, regex)

        # add to database
        if newChannel != '' or newChannel is not None:
            add = Channel(newChannel, newChannel, logo)
            self.database.addChannel(add)

        with open(os.path.join(self.profilePath, 'basemap_extra.xml'), mode='rb+') as f:
            s = f.read()
            s = s.decode('utf-8')
            new_str = re.sub(r'^(.*{}.*)$'.format(re.escape('strm=""/>')), lambda g: g.group(0) + '\n\t'+item, s, count=1, flags=re.MULTILINE)
            f.seek(0)
            f.write(new_str.encode('utf-8'))
            f.close()
            xbmcgui.Dialog().notification(strings(57051), strings(59993).format(epgChann.upper()))
            self.reloadList(add=True)

    def getLog(self, filename):
        import codecs
        if os.path.isfile(filename):
            content = None
            if PY3:
                with open(filename, 'r', encoding='utf-8') as content_file:
                    content = content_file.read()
            else:
                with codecs.open(filename, 'r', encoding='utf-8') as content_file:
                    content = content_file.read()

            if content is None:
                deb('LogUploader upload ERROR could not get content of log file')
            return content
        return None

    def _debugMenu(self, program):
        deb('Debug')
        res = xbmcgui.Dialog().contextmenu(['Reinitialize guide', 'Reload services', 'Upload log file', 'Read log', 'Guide information', 'Response status', 'Python version', 'System information'])

        if res < 0:
            self._showContextMenu(program)

        if res == 0:
            epgDbSize = self.database.source.getEpgSize()
            self.onRedrawEPG(self.channelIdx, self.viewStartDate, force=True)
            ADDON.setSetting('epg_size', str(epgDbSize))

        elif res == 1:
            self.refreshStreamsLoop()

        elif res == 2:
            import logUploader
            self._debugMenu(program)

        elif res == 3:
            if PY3:
                LOGPATH  = xbmcvfs.translatePath('special://logpath')
            else:
                LOGPATH  = xbmc.translatePath('special://logpath')

            LOGFILE  = os.path.join(LOGPATH, 'kodi.log')
            LOGFILE2 = os.path.join(LOGPATH, 'spmc.log')
            LOGFILE3 = os.path.join(LOGPATH, 'xbmc.log')

            if os.path.isfile(LOGFILE):
                logContent = self.getLog(LOGFILE)
            elif os.path.isfile(LOGFILE2):
                logContent = self.getLog(LOGFILE2)
            elif os.path.isfile(LOGFILE3):
                logContent = self.getLog(LOGFILE3)
            else:
                xbmcgui.Dialog().ok(strings(30150),"\n" + "Unable to find kodi log file")
                self._debugMenu(program)

            xbmcgui.Dialog().textviewer('Log - ' + strings(57051), logContent, True)
            self._debugMenu(program)

        elif res == 4:
            size, updated = self.database.getDbEPGSize()

            xbmcgui.Dialog().textviewer('Guide information - ' + strings(57051), 'Content-Size: ' + str(formatFileSize(int( size ) )) + '[CR]Updated on: ' + str(updated.strftime("%Y-%m-%d %H:%M")), True)
            self._debugMenu(program)

        elif res == 5:
            UA = xbmc.getUserAgent()

            headers = {
                'User-Agent': UA,
            }

            # Internet connection
            response = requests.get('https://www.google.com', headers=headers)

            if response.status_code < 400:
                conn = '[COLOR green][B]Online[/B][/COLOR]'
            else:
                conn = '[COLOR green][B]Offline[/B][/COLOR]'

            headers_r = {
                'authority': 'raw.githubusercontent.com',
                'upgrade-insecure-requests': '1',
                'user-agent': UA,
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'referer': 'https://github.com/Mariusz89B/mods-kodi/blob/master/mods-kodi-addons.xml',
                'accept-language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6,fr;q=0.5',
            }

            # Repository connection
            response_repo = requests.get('https://raw.githubusercontent.com/Mariusz89B/mods-kodi/master/mods-kodi-addons.xml', headers=headers_r)

            if response_repo.status_code < 400:
                conn_r = '[COLOR green][B]Online[/B][/COLOR]'
            else:
                conn_r = '[COLOR green][B]Offline[/B][/COLOR]'

            xbmcgui.Dialog().textviewer('Response status - ' + strings(57051), 'HTTP/S status: ' + str(response.status_code) + '[CR]Internet connection: ' + conn + '[CR]Repository connection: ' + conn_r, True)
            self._debugMenu(program)

        elif res == 6:
            xbmcgui.Dialog().textviewer('Python version - ' + strings(57051), 'Python ' + str(sys.version), True)
            self._debugMenu(program)

        elif res == 7:
            try:
                import platform
                uname = platform.uname()

                info = 'System: {0} {1}, release {2}\nUser: {3}\nMachine: {4}\nProcessor: {5}'.format(uname.system, uname.release, uname.version, uname.node, uname.machine, uname.processor)
                xbmcgui.Dialog().textviewer('System information - ' + strings(57051), info, True)
            except:
                xbmcgui.Dialog().textviewer('System information - ' + strings(57051), 'System information not available.', True)
            self._debugMenu(program)

    def _showContextMenu(self, program):
        deb('_showContextMenu')
        self._hideControl(self.C_MAIN_MOUSEPANEL_CONTROLS)

        self.currentChannel = program.channel
        self.program = program

        if program.notificationScheduled:
            remindControl = (strings(DONT_REMIND_PROGRAM))
        else:
            remindControl = (strings(REMIND_PROGRAM))

        if program.endDate < datetime.datetime.now():
            if program.recordingScheduled:
                programRecordControl = (strings(DOWNLOAD_PROGRAM_CANCEL_STRING))
            else:
                programRecordControl = (strings(DOWNLOAD_PROGRAM_STRING))
        else:
            if program.recordingScheduled:
                programRecordControl = (strings(RECORD_PROGRAM_CANCEL_STRING))
            else:
                programRecordControl = (strings(RECORD_PROGRAM_STRING))

        removeStrm = False

        if self.database.getCustomStreamUrl(program.channel):
            chooseStrmControl = (strings(REMOVE_STRM_FILE))
            removeStrm = True
        else:
            chooseStrmControl = (strings(CHOOSE_STRM_FILE))

        if ADDON.getSetting('debug') == 'true':
            debug = True
        else:
            debug = False

        menu = [strings(30346), strings(58000), strings(30356), remindControl, programRecordControl, strings(30337), strings(30377), strings(31022), strings(30309), strings(68005), strings(30913), strings(30602), chooseStrmControl, strings(30308)]
        if debug:
            menu.insert(0, 'Debug')

        ret = xbmcgui.Dialog().contextmenu(menu)

        if debug:
            ret = int(ret) - 1

        if ret == -1 and debug:
            self._debugMenu(program)

        if ret == 0:
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
                    else:
                        self._showContextMenu(program)

        elif ret == 1:
            deb('Info')
            self.infoDialog = InfoDialog(program, self.playChannel2, self.recordProgram, self.notification,
                                         self.ExtendedInfo, self.onRedrawEPG, self.channelIdx, self.viewStartDate)
            self.infoDialog.setChannel(program)
            self.infoDialog.doModal()

            del self.infoDialog
            self.infoDialog = None

        elif ret == 2:
            deb('ExtendedInfo')
            self.ExtendedInfo(program)

        elif ret == 3:
            if program.notificationScheduled:
                self.notification.removeNotification(program)
            else:
                self.notification.addNotification(program, onlyOnce = True)

            self.onRedrawEPG(self.channelIdx, self.viewStartDate)

        elif ret == 4:
            if program.recordingScheduled:
                self.recordProgram(program)

            elif program.endDate <= datetime.datetime.now():
                self.recordProgram(program)

            else:
                res = xbmcgui.Dialog().select(strings(70006) + ' - ' + strings(57051), [strings(30622), strings(30623)])
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

        elif ret == 5:
            if PY3:
                record_folder = ADDON.getSetting('record_folder')
                xbmc.executebuiltin('ActivateWindow(Videos,{record_folder},return)'.format(record_folder=record_folder))
            else:
                record_folder = native(ADDON.getSetting('record_folder'))
                xbmc.executebuiltin(b'ActivateWindow(Videos,{record_folder},return)'.format(record_folder=record_folder))

        elif ret == 6:
            d = ChannelsMenu(self.database, program.channel)
            d.doModal()

            del d
            self.onRedrawEPG(self.channelIdx, self.viewStartDate)


        elif ret == 7:
            categories = {}
            new_category = None

            lst = list(self.categories)

            if not lst:
                new_category = xbmcgui.Dialog().input(strings(30984), type=xbmcgui.INPUT_ALPHANUM)
                if new_category:
                    cats = set(self.categories)
                    cats.add(new_category)
                    self.categories = list(set(cats))
                    lst.append(new_category)
                else:
                    return

            res = xbmcgui.Dialog().select(strings(31023), lst)
            if res < 0:
                return

            xbmc.executebuiltin('ActivateWindow(busydialognocancel)')

            cat = lst[res]
            categories[cat] = []

            for name, cat in self.database.getCategoryMap():

                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(name)

            channel = program.channel.title
            if channel not in categories[cat]:
                categories[cat].append(channel)

                self.database.saveCategoryMap(categories)
                self.categories = [category for category in categories if category]
                self._clearEpg()
                self.onRedrawEPG(self.channelIdx, self.viewStartDate)
                xbmc.executebuiltin('Dialog.Close(busydialognocancel)')
                xbmcgui.Dialog().notification(strings(57051), strings(31025).format(cat))

            else:
                xbmc.executebuiltin('Dialog.Close(busydialognocancel)')
                xbmcgui.Dialog().notification(strings(57051), strings(31024))

        elif ret == 8:
            d = xbmcgui.Dialog()
            lst = d.select(strings(30309), [strings(30315), strings(30310), strings(30311), strings(30312), strings(30336), strings(30337)])

            if lst < 0:
                self.onRedrawEPG(self.channelIdx, self.viewStartDate)
            elif lst == 0:
                self.programSearchSelect(program.channel)
            elif lst == 1:
                self.showListing(program.channel)
            elif lst == 2:
                self.showNow(program.channel)
            elif lst == 3:
                self.showNext(program.channel)
            elif lst == 4:
                self.showFullReminders(program.channel)
            elif lst == 5:
                self.showFullRecordings(program.channel)
            else:
                return

        elif ret == 9:
            self.popupMenu(program)

        elif ret == 10:
            xbmcaddon.Addon(id=ADDON_ID).openSettings()

        elif ret == 11:
            xbmc.executebuiltin("ActivateWindow(10134)")

        elif ret == 12:
            if removeStrm:
                self.database.deleteCustomStreamUrl(program.channel)
            d = StreamSetupDialog(self.database, program.channel, self)
            d.doModal()
            del d

        elif ret == 13:
            self.close()

    def popupMenu(self, program):
        if not xbmc.getCondVisibility('Window.IsVisible(script-tvguide-menu.xml)'):
            d = PopupMenu(self.database, program, self.predefinedCategories)
            d.doModal()
            buttonClicked = d.buttonClicked
            new_category = d.category
            del d

            if buttonClicked == PopupMenu.C_POPUP_PLAY:
                self.playChannel(program.channel)

            elif buttonClicked == PopupMenu.C_POPUP_RECORDINGS:
                if PY3:
                    record_folder = ADDON.getSetting('record_folder')
                    xbmc.executebuiltin('ActivateWindow(Videos,{record_folder},return)'.format(record_folder=record_folder))
                else:
                    record_folder = native(ADDON.getSetting('record_folder'))
                    xbmc.executebuiltin(b'ActivateWindow(Videos,{record_folder},return)'.format(record_folder=record_folder))

            elif buttonClicked == PopupMenu.C_POPUP_FAQ:
                xbmcgui.Dialog().textviewer(strings(30994), strings(99996), True)
                self.popupMenu(program)

            elif buttonClicked == PopupMenu.C_POPUP_CATEGORY:
                self.database.setCategory(new_category)
                ADDON.setSetting('category', new_category)
                with self.busyDialog():
                    self.onRedrawEPG(self.channelIdx == 1, self.viewStartDate)
                    self.popupMenu(program)

            elif buttonClicked == PopupMenu.C_POPUP_ADD_CHANNEL:
                deb('AddChannel')
                self.channelsSelect()
                self.popupMenu(program)

            elif buttonClicked == PopupMenu.C_POPUP_REMOVE_CHANNEL:
                deb('RemoveChannel')
                self.channelsRemove()
                self.popupMenu(program)


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

        if controlId == self.C_MAIN_SLIDE and xbmc.getCondVisibility('!Control.IsVisible(4100)'):
            self.popupMenu(self.program)

    def realtimeDate(self, program):
        #Realtime date & weekday
        startDate = str(program.startDate)
        try:
            now = datetime.proxydt.strptime(startDate, '%Y-%m-%d %H:%M:%S')
        except:
            now = datetime.proxydt.strptime(str(datetime.datetime.now()), '%Y-%m-%d %H:%M:%S.%f')

        nowDay = now.strftime("%a").replace('Mon', xbmc.getLocalizedString(11)).replace('Tue', xbmc.getLocalizedString(12)).replace('Wed', xbmc.getLocalizedString(13)).replace('Thu', xbmc.getLocalizedString(14)).replace('Fri', xbmc.getLocalizedString(15)).replace('Sat', xbmc.getLocalizedString(16)).replace('Sun', xbmc.getLocalizedString(17))

        nowDate = now.strftime("%d %B %Y").replace('January', xbmc.getLocalizedString(21)).replace('Februari', xbmc.getLocalizedString(22)).replace('Mars', xbmc.getLocalizedString(23)).replace('April', xbmc.getLocalizedString(24)).replace('May', xbmc.getLocalizedString(25)).replace('June', xbmc.getLocalizedString(26)).replace('July', xbmc.getLocalizedString(27)).replace('August', xbmc.getLocalizedString(28)).replace('September', xbmc.getLocalizedString(29)).replace('October', xbmc.getLocalizedString(30)).replace('November', xbmc.getLocalizedString(31)).replace('December', xbmc.getLocalizedString(32))

        self.setControlLabel(C_MAIN_DAY, '{}'.format(nowDay))
        self.setControlLabel(C_MAIN_REAL_DATE, '{}'.format(nowDate))

    def calctimeLeft(self, program):
        #Calc time EPG
        startDelta = datetime.datetime.now() - program.startDate
        endDelta = datetime.datetime.now() - program.endDate

        calcTime = startDelta - endDelta

        self.setControlLabel(C_MAIN_CALC_TIME_EPG, '{}'.format(calcTime))

    def getLastPlayingChannel(self):
        idx, start, end, played = self.database.getLastChannel()

        channelList = self.database.getChannelList(onlyVisible=True)
        try:
            idx = int(idx)
            chann = channelList[idx]
        except:
            try:
                chann = channelList[0]
            except:
                return None, 0

        program = self.database.getProgramStartingAt(chann, start, end)

        return program, idx

    def getLastPreviousChannel(self):
        return self.lastChannel

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
        self.setControlLabel(C_MAIN_TITLE, '{} '.format(program.title))
        self.setControlLabel(C_MAIN_TIME, '{} - {}'.format(self.formatTime(program.startDate), self.formatTime(program.endDate)))

        if xbmc.Player().isPlaying():
            if ADDON.getSetting('info_osd') == "false" or self.program is None:
                program, idx = self.getLastPlayingChannel()

                if not program:
                    program = self.program

                try:
                    self.setControlLabel(C_MAIN_CHAN_PLAY, '{}'.format(program.channel.title))
                    self.setControlLabel(C_MAIN_PROG_PLAY, '{}'.format(program.title))
                    self.setControlLabel(C_MAIN_TIME_PLAY, '{} - {}'.format(self.formatTime(program.startDate), self.formatTime(program.endDate)))
                    self.setControlLabel(C_MAIN_NUMB_PLAY, '{}'.format((str(int(idx) + 1))))

                except:
                    self.setControlLabel(C_MAIN_CHAN_PLAY, '{}'.format('N/A'))
                    self.setControlLabel(C_MAIN_PROG_PLAY, '{}'.format(strings(55016)))
                    self.setControlLabel(C_MAIN_TIME_PLAY, '{} - {}'.format('N/A','N/A'))
                    self.setControlLabel(C_MAIN_NUMB_PLAY, '{}'.format('-'))
                    return

        if program.description:
            description = program.description
            if not description:
                strings(NO_DESCRIPTION)
        elif program.categoryA:
            category = program.categoryA
            description = program.description
            if not category:
                category = strings(NO_CATEGORY)
        else:
            description = strings(NO_DESCRIPTION)
            category = strings(NO_CATEGORY)

        if skin_separate_category or skin_separate_year_of_production or skin_separate_director or skin_separate_episode or skin_separate_allowed_age_icon or skin_separate_program_progress or skin_separate_program_progress_epg or skin_separate_program_actors:
            # This mean we'll need to parse program description
            descriptionParser = src.ProgramDescriptionParser(description)
            if skin_separate_category:
                try:
                    category = descriptionParser.extractCategory()
                    if category == '':
                        category = program.categoryA
                        if category == '':
                            category = strings(NO_CATEGORY)
                    self.setControlText(C_PROGRAM_CATEGORY, category)
                except:
                    pass
            if skin_separate_year_of_production:
                try:
                    year = descriptionParser.extractProductionDate()
                    if year == '':
                        year = program.productionDate
                    self.setControlText(C_PROGRAM_PRODUCTION_DATE, year)
                except:
                    pass
            if skin_separate_director:
                try:
                    director = descriptionParser.extractDirector()
                    if director == '':
                        director = program.director
                    self.setControlText(C_PROGRAM_DIRECTOR, director)
                except:
                    pass
            if skin_separate_episode:
                try:
                    episode = descriptionParser.extractEpisode()
                    if episode == '':
                        episode = program.episode
                    self.setControlText(C_PROGRAM_EPISODE, episode)
                except:
                    pass
            if skin_separate_allowed_age_icon:
                try:
                    icon, age = descriptionParser.extractAllowedAge()
                    if icon == '':
                        if PY3:
                            addonPath = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
                        else:
                            addonPath = xbmc.translatePath(ADDON.getAddonInfo('path'))

                        number_regex = re.compile('(\d+)')

                        r = number_regex.search(str(program.rating))
                        age = r.group(1) if r else ''

                        if age == '3':
                            age = '0'

                        icon = os.path.join(addonPath, 'icons', 'age_rating', 'icon_{}.png'.format(age))
                    self.setControlImage(C_PROGRAM_AGE_ICON, icon)
                except:
                    pass
            if skin_separate_program_actors:
                try:
                    actors = descriptionParser.extractActors()
                    if actors == '':
                        actors = program.actor
                    self.setControlText(C_PROGRAM_ACTORS, actors)
                except:
                    pass
            if skin_separate_rating:
                try:
                    rating = descriptionParser.extractRating()
                    if rating == '':
                        rating = program.rating
                    self.setControlText(C_PROGRAM_RATING, rating)
                except:
                    pass
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

        if program.channel.logo is not None:
            self.setControlImage(C_MAIN_LOGO, program.channel.logo)
        if program.imageSmall is not None and ADDON.getSetting('show_program_logo') == "true":
            self.setControlImage(C_MAIN_IMAGE, program.imageSmall)
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

            if ret:
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

    def updateCurrentChannel(self, channel, program=None):
        deb('updateCurrentChannel: {}'.format(channel))
        self.lastChannel = self.currentChannel
        self.currentChannel = channel

        idx = self.database.getCurrentChannelIdx(self.currentChannel)

        self.played = datetime.datetime.now()

        if not program:
            program = self.program
            if not program:
                program = self.database.getCurrentProgram(channel)

        if program:
            self.program = program
            self.start = program.startDate
            self.end = program.endDate

        else:
            self.start = self.played
            self.end = self.played

        self.database.lastChannel(idx, self.start, self.end, self.played)

    def elapsedInterval(self, start, end):
        elapsed = end - start
        min, secs = divmod(elapsed.days * 86400 + elapsed.seconds, 60)
        hour, minutes = divmod(min, 60)
        return '%.2d:%.2d:%.2d' % (hour, minutes, secs)

    def playChannel2(self, program):
        deb('playChannel2: {}'.format(program))

        if xbmc.Player().isPlaying():
            time.sleep(0.2)

        self.program = program

        dt = datetime.datetime.now() + datetime.timedelta(minutes=int(timebarAdjust()))

        # Playback for services
        if ADDON.getSetting('archive_support') == 'true':
            try:
                ProgramEndDate = datetime.proxydt.strptime(str(self.program.endDate), '%Y-%m-%d %H:%M:%S')
                ProgramStartDate = datetime.proxydt.strptime(str(self.program.startDate), '%Y-%m-%d %H:%M:%S')
            except:
                ProgramEndDate = datetime.proxydt.strptime(str(dt), '%Y-%m-%d %H:%M:%S.%f')
                ProgramStartDate = datetime.proxydt.strptime(str(dt), '%Y-%m-%d %H:%M:%S.%f')

            try:
                ProgramNowDate = datetime.proxydt.strptime(str(dt), '%Y-%m-%d %H:%M:%S.%f')
            except:
                ProgramNowDate = datetime.proxydt.strptime(str(dt), '%Y-%m-%d %H:%M:%S')

            if ADDON.getSetting('archive_finished_program') == 'true':
                finishedProgram = ProgramEndDate
            else:
                finishedProgram = ProgramStartDate

            catchupList = self.getStreamsCid(self.catchupChannels)

            day = ''

            catchupList = catchupList.items()

            try:
                if catchupList:
                    if program.channel.title.upper() in [k for k,v in catchupList]:
                        day = [v for k,v in catchupList if k == program.channel.title.upper()][0]

                if day == '':
                    day = ADDON.getSetting('archive_reverse_days')

                if day == '3H':
                    reverseTime = dt - datetime.timedelta(hours = int(3)) - datetime.timedelta(minutes = 5)

                elif ADDON.getSetting('archive_reverse_auto') == '0' and day != '':
                    try:
                        reverseTime = dt - datetime.timedelta(hours = int(day)) * 24 - datetime.timedelta(minutes = 5)
                    except:
                        reverseTime = dt - datetime.timedelta(hours = int(1)) * 24 - datetime.timedelta(minutes = 5)
                else:
                    try:
                        reverseTime = dt - datetime.timedelta(hours = int(ADDON.getSetting('archive_manual_days'))) * 24 - datetime.timedelta(minutes = 5)
                    except:
                        reverseTime = dt - datetime.timedelta(hours = int(1)) * 24 - datetime.timedelta(minutes = 5)

                if day == '3H':
                    reverseTime = dt - datetime.timedelta(hours = int(3)) - datetime.timedelta(minutes = 5)

                elif ADDON.getSetting('archive_reverse_auto') == '0' and day != '':
                    try:
                        reverseTime = dt - datetime.timedelta(hours = int(day)) * 24 - datetime.timedelta(minutes = 5)
                    except:
                        reverseTime = dt - datetime.timedelta(hours = int(1)) * 24 - datetime.timedelta(minutes = 5)

                else:
                    try:
                        reverseTime = dt - datetime.timedelta(hours = int(ADDON.getSetting('archive_manual_days'))) * 24 - datetime.timedelta(minutes = 5)
                    except:
                        reverseTime = dt - datetime.timedelta(hours = int(1)) * 24 - datetime.timedelta(minutes = 5)
            except:
                reverseTime = dt

            try:
                if finishedProgram < dt and ADDON.getSetting('archive_support') == 'true' and program.title != program.channel.title:

                    if (program.channel.title.upper() in [k for k,v in catchupList] and program.startDate > reverseTime):
                        res = xbmcgui.Dialog().yesno(strings(30998), strings(30999).format(program.title))

                        if res:
                            # archiveService
                            if ADDON.getSetting('archive_finished_program') == 'true': 
                                if program.channel.title.upper() in [k for k,v in catchupList] and program.endDate < dt:
                                    from time import mktime

                                    n = dt
                                    t = ProgramStartDate
                                    e = ProgramEndDate

                                    # Duration
                                    durationCalc = int(((ProgramEndDate - ProgramStartDate).total_seconds() / 60.0))
                                    duration = str(durationCalc)

                                    # Offset
                                    offsetCalc = int(((dt - ProgramStartDate).total_seconds() / 60.0))
                                    offset = str(offsetCalc)

                                    # UTC/LUTC
                                    if PY3:
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

                                    self.archiveService = dt - ProgramStartDate

                                else:
                                    self.archivePlaylist = ''
                                    self.archiveService = ''
                            else:
                                if program.channel.title.upper() in [k for k,v in catchupList] and program.startDate < dt:
                                    from time import mktime

                                    n = dt
                                    t = ProgramStartDate
                                    e = ProgramEndDate

                                    # Duration
                                    durationCalc = int(((ProgramEndDate - ProgramStartDate).total_seconds() / 60.0))
                                    duration = str(durationCalc)

                                    # Offset
                                    offsetCalc = int(((dt - ProgramStartDate).total_seconds() / 60.0))
                                    offset = str(offsetCalc)

                                    # UTC/LUTC
                                    if PY3:
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

                                    self.archiveService = dt - ProgramStartDate

                                else:
                                    self.archivePlaylist = ''
                                    self.archiveService = ''

                        else:
                            if ADDON.getSetting('archive_finished_program') == 'false':
                                if ProgramEndDate > dt:
                                    self.archiveService = ''
                                    self.archivePlaylist = ''
                                else:
                                    return 'None'
                            else:
                                return 'None'

                    else:
                        if program.endDate > dt:
                            self.archiveService = ''
                            self.archivePlaylist = ''
                        else:
                            res = xbmcgui.Dialog().yesno(strings(30998), strings(59980))
                            if res:
                                self.archiveService = ''
                                self.archivePlaylist = ''
                            else:
                                return 'None'

                else:
                    self.archiveService = ''
                    self.archivePlaylist = ''

            except:
                self.archiveService = ''
                self.archivePlaylist = ''

        else:
            self.archiveService = ''
            self.archivePlaylist = ''

        self.updateCurrentChannel(program.channel, program)
        if self.playRecordedProgram(program):
            return True

        urlList = self.database.getStreamUrlList(program.channel)
        if len(urlList) > 0:
            if ADDON.getSetting('start_video_minimalized') == 'false' and xbmc.Player().isPlaying():
                xbmc.executebuiltin("Action(FullScreen)")
            if ADDON.getSetting('info_osd') == "true":
                self.createOSD(program, urlList)
            else:
                self.playService.playUrlList(urlList, self.archiveService, self.archivePlaylist, resetReconnectCounter=True)
        return len(urlList) > 0

    def playChannel(self, channel, program=None):
        deb('playChannel: {}'.format(program))

        if xbmc.Player().isPlaying():
            time.sleep(0.2)

        dt = datetime.datetime.now() + datetime.timedelta(minutes=int(timebarAdjust()))

        # Playback for services
        if ADDON.getSetting('archive_support') == 'true':
            try:
                ProgramEndDate = datetime.proxydt.strptime(str(self.program.endDate), '%Y-%m-%d %H:%M:%S')
                ProgramStartDate = datetime.proxydt.strptime(str(self.program.startDate), '%Y-%m-%d %H:%M:%S')
            except:
                ProgramEndDate = datetime.proxydt.strptime(str(dt), '%Y-%m-%d %H:%M:%S.%f')
                ProgramStartDate = datetime.proxydt.strptime(str(dt), '%Y-%m-%d %H:%M:%S.%f')

            try:
                ProgramNowDate = datetime.proxydt.strptime(str(dt), '%Y-%m-%d %H:%M:%S.%f')
            except:
                ProgramNowDate = datetime.proxydt.strptime(str(dt), '%Y-%m-%d %H:%M:%S')

            if ADDON.getSetting('archive_finished_program') == 'true':
                finishedProgram = ProgramEndDate
            else:
                finishedProgram = ProgramStartDate

            catchupList = self.getStreamsCid(self.catchupChannels)

            day = ''

            catchupList = catchupList.items()

            try:
                if catchupList:
                    if program.channel.title.upper() in [k for k,v in catchupList]:
                        day = [v for k,v in catchupList if k == program.channel.title.upper()][0]

                if day == '':
                    day = ADDON.getSetting('archive_reverse_days')

                if day == '3H':
                    reverseTime = dt - datetime.timedelta(hours = int(3)) - datetime.timedelta(minutes = 5)

                elif ADDON.getSetting('archive_reverse_auto') == '0' and day != '':
                    try:
                        reverseTime = dt - datetime.timedelta(hours = int(day)) * 24 - datetime.timedelta(minutes = 5)
                    except:
                        reverseTime = dt - datetime.timedelta(hours = int(1)) * 24 - datetime.timedelta(minutes = 5)
                else:
                    try:
                        reverseTime = dt - datetime.timedelta(hours = int(ADDON.getSetting('archive_manual_days'))) * 24 - datetime.timedelta(minutes = 5)
                    except:
                        reverseTime = dt - datetime.timedelta(hours = int(1)) * 24 - datetime.timedelta(minutes = 5)

                if day == '3H':
                    reverseTime = dt - datetime.timedelta(hours = int(3)) - datetime.timedelta(minutes = 5)

                elif ADDON.getSetting('archive_reverse_auto') == '0' and day != '':
                    try:
                        reverseTime = dt - datetime.timedelta(hours = int(day)) * 24 - datetime.timedelta(minutes = 5)
                    except:
                        reverseTime = dt - datetime.timedelta(hours = int(1)) * 24 - datetime.timedelta(minutes = 5)

                else:
                    try:
                        reverseTime = dt - datetime.timedelta(hours = int(ADDON.getSetting('archive_manual_days'))) * 24 - datetime.timedelta(minutes = 5)
                    except:
                        reverseTime = dt - datetime.timedelta(hours = int(1)) * 24 - datetime.timedelta(minutes = 5)
            except:
                reverseTime = dt

            try:
                if finishedProgram < dt and ADDON.getSetting('archive_support') == 'true' and program.title != program.channel.title:

                    if (program.channel.title.upper() in [k for k,v in catchupList] and program.startDate > reverseTime):
                        res = xbmcgui.Dialog().yesno(strings(30998), strings(30999).format(program.title))

                        if res:
                            # archiveService
                            if ADDON.getSetting('archive_finished_program') == 'true': 
                                if program.channel.title.upper() in [k for k,v in catchupList] and program.endDate < dt:
                                    self.archiveService = dt - ProgramStartDate
                                else:
                                    self.archiveService = ''
                            else:
                                if program.channel.title.upper() in [k for k,v in catchupList] and program.startDate < dt:
                                    self.archiveService = dt - ProgramStartDate
                                else:
                                    self.archiveService = ''

                            if ADDON.getSetting('archive_finished_program') == 'true': 
                                if program.channel.title.upper() in [k for k,v in catchupList] and program.endDate < dt:
                                    from time import mktime

                                    n = dt
                                    t = ProgramStartDate
                                    e = ProgramEndDate

                                    # Duration
                                    durationCalc = int(((ProgramEndDate - ProgramStartDate).total_seconds() / 60.0))
                                    duration = str(durationCalc)

                                    # Offset
                                    offsetCalc = int(((dt - ProgramStartDate).total_seconds() / 60.0))
                                    offset = str(offsetCalc)

                                    # UTC/LUTC
                                    if PY3:
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
                                if program.channel.title.upper() in [k for k,v in catchupList] and program.startDate < dt:
                                    from time import mktime

                                    n = dt
                                    t = ProgramStartDate
                                    e = ProgramEndDate

                                    # Duration
                                    durationCalc = int(((ProgramEndDate - ProgramStartDate).total_seconds() / 60.0))
                                    duration = str(durationCalc)

                                    # Offset
                                    offsetCalc = int(((dt - ProgramStartDate).total_seconds() / 60.0))
                                    offset = str(offsetCalc)

                                    # UTC/LUTC
                                    if PY3:
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
                                if ProgramEndDate > dt:
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

        else:
            self.archiveService = ''
            self.archivePlaylist = ''

        self.updateCurrentChannel(channel, program)
        if program:
            self.program = program
            if self.playRecordedProgram(program):
                return True

        urlList = self.database.getStreamUrlList(channel)
        if len(urlList) > 0:
            if ADDON.getSetting('start_video_minimalized') == 'false' and xbmc.Player().isPlaying():
                xbmc.executebuiltin("Action(FullScreen)")
            if ADDON.getSetting('info_osd') == "true":
                self.createOSD(program, urlList)
            else:
                self.playService.playUrlList(urlList, self.archiveService, self.archivePlaylist, resetReconnectCounter=True)
        return len(urlList) > 0

    def recordProgram(self, program, watch='', length=''):
        deb('recordProgram')
        catchupList = self.getStreamsCid(self.catchupChannels)

        if watch and length != '':
            if self.recordService.recordProgramGui(program=program, watch=watch, length=length, catchupList=catchupList):
                self.onRedrawEPG(self.channelIdx, self.viewStartDate)
                self.playAndWatchRecordedProgram(program)

        else:
            if self.recordService.recordProgramGui(program=program, catchupList=catchupList):
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
        try:
            if self.end < self.played:
                self.viewStartDate = self.program.startDate + datetime.timedelta(minutes=int(timebarAdjust()))
            else:
                self.viewStartDate = datetime.datetime.today() + datetime.timedelta(minutes=int(timebarAdjust()))
        except:
            self.viewStartDate = datetime.datetime.today() + datetime.timedelta(minutes=int(timebarAdjust()))

        self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30, seconds=self.viewStartDate.second)

        if self.currentChannel:
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

    def onTimebarEPG(self):
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

            matchAddon = re.findall('<texture colordiffuse="(.*?)">.*osd/back.png</texture>', str(line))
        except:
            pass

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

            matchAddon = re.findall('<texture colordiffuse="(.*?)">.*tvguide-timebar.png</texture>', str(line))
        except:
            pass

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

        tmp_control = self.getControl(self.C_MAIN_TIMEBAR)
        tmp_background = self.getControl(self.C_MAIN_TIMEBAR_BACK)

        if self.timebar:
            try:
                self.removeControl(self.timebar)
            except:
                pass  # happens if we try to remove a control that doesn't exist
            self.timebar = None

        if self.timebarBack:
            try:
                self.removeControl(self.timebarBack)
            except:
                pass  # happens if we try to remove a control that doesn't exist
            self.timebarBack = None

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

    def onRedrawEPGPlaying(self, channelStart, startTime, initializing=False, startup=False):
        deb('onRedrawEPGVideo')
        if self.redrawingEPG or (self.database is not None and self.database.updateInProgress) or self.isClosing or strings2.M_TVGUIDE_CLOSING:
            deb('onRedrawEPGPlaying - already redrawing')
            return  # ignore redraw request while redrawing
        self.blockInputDueToRedrawing = True
        self.mode = MODE_TV

        try:
            self.channelIdx, channels, programs, cacheExpired = self.database.getEPGView(channelStart, startTime, self.onSourceProgressUpdate, initializing, startup, clearExistingProgramList=True)
        except src.SourceException:
            self.blockInputDueToRedrawing = False
            debug('onRedrawEPGPlaying onEPGLoadError')
            self.onEPGLoadError()
            return

        if not self.predefinedCategories:
            self.predefinedCategories = self.getPredefinedCategories()

        if cacheExpired == True and ADDON.getSetting('program_notifications_enabled') == 'true':
            # make sure notifications are scheduled for newly downloaded programs
            self.notification.scheduleNotifications()

        self._showControl(self.C_MAIN_LOADING_BACKGROUND)
        self._hideControl(self.C_MAIN_LOADING)

        debug('onRedrawEPGPlaying done')
        return


    def updateEPG(self, channelStart, startTime, initializing, startup, force):
        self._clearEpg()

        self.initialized = True
        self._hideControl(self.C_MAIN_MOUSEPANEL_CONTROLS)
        self._showControl(self.C_MAIN_LOADING)
        self._hideControl(self.C_MAIN_LOADING_BACKGROUND)
        self.setControlLabel(self.C_MAIN_LOADING_TIME_LEFT, strings(BACKGROUND_UPDATE_IN_PROGRESS))
        self.setFocusId(self.C_MAIN_LOADING_CANCEL)

        try:
            self.channelIdx, channels, programs, cacheExpired = self.database.getEPGView(channelStart, startTime, self.onSourceProgressUpdate, initializing, startup, force, clearExistingProgramList=True)
        except src.SourceException:
            self.blockInputDueToRedrawing = False
            debug('onRedrawEPG onEPGLoadError')
            self.onEPGLoadError()
            return

        self.onRedrawEPG(self.channelIdx, self.viewStartDate, self._getCurrentProgramFocus)


    def onRedrawEPG(self, channelStart, startTime, focusFunction=None, initializing=False, startup=False, force=False):
        try:
            deb('onRedrawEPG')
            if force:
                self.updateEPG(channelStart, startTime, initializing, startup, debug)
                return

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

            try:
                self.channelIdx, channels, programs, cacheExpired = self.database.getEPGView(channelStart, startTime, self.onSourceProgressUpdate, initializing, startup, force, clearExistingProgramList=True)

            except src.SourceException:
                self.blockInputDueToRedrawing = False
                debug('onRedrawEPG onEPGLoadError')
                self.onEPGLoadError()
                return

            if not self.predefinedCategories:
                self.predefinedCategories = self.getPredefinedCategories()

             # remove existing controls
            self._clearEpg()

            self.catchupChannels = channels

            if cacheExpired == True and ADDON.getSetting('program_notifications_enabled') == 'true':
                # make sure notifications are scheduled for newly downloaded programs
                self.notification.scheduleNotifications()

            # date and time row
            self.setControlLabel(self.C_MAIN_DATE, self.formatDate(self.viewStartDate))
            for col in range(1, 5):
                self.setControlLabel(4000 + col, self.formatTime(startTime))
                startTime += HALF_HOUR

            if programs is None:
                debug('onRedrawEPG onEPGLoadError2')
                #self.onEPGLoadError()
                return

            categories = self.getCategories()
            catchupList = self.getStreamsCid(self.catchupChannels)

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

                    noFocusTexture = self.backgroundTexture

                    try:
                        categoryA = program.categoryA.lower().split(' ')
                    except:
                        categoryA = ''

                    if any(x in categories['Movie'] for x in categoryA):
                        noFocusTexture = self.moviesTexture

                    elif any(x in categories['Series'] for x in categoryA):
                        noFocusTexture = self.seriesTexture

                    elif any(x in categories['Information'] for x in categoryA):
                        noFocusTexture = self.informationTexture

                    elif any(x in categories['Entertainment'] for x in categoryA):
                        noFocusTexture = self.entertainmentTexture

                    elif any(x in categories['Document'] for x in categoryA):
                        noFocusTexture = self.documentsTexture

                    elif any(x in categories['Kids'] for x in categoryA):
                        noFocusTexture = self.kidsTexture

                    elif any(x in categories['Sport'] for x in categoryA):
                        noFocusTexture = self.sportsTexture

                    elif any(x in categories['Interactive Entertainment'] for x in categoryA):
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

                    if cellWidth > 30 and cellWidth < 45:
                        title = '...'  # Text will overflow outside the button if it is too narrow
                    elif cellWidth < 30:
                        title = ' '
                    else:
                        title = program.title
                        if title.strip() == '':
                            title = program.channel.title
                            noFocusTexture = self.backgroundTexture

                    archive = self.catchupEPG(program, cellWidth, catchupList)

                    item = xbmcgui.ListItem(program.channel.title)
                    if program.imageSmall is not None:
                        item.setArt({'icon': program.imageSmall})

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

            self.onTimebarEPG()
            self.updateTimebar()

            self.redrawingEPG = False
            if self.redrawagain:
                debug('onRedrawEPG redrawing again')
                self.redrawagain = False
                self.onRedrawEPG(channelStart, self.viewStartDate, focusFunction)
            debug('onRedrawEPG done')

            return channels

        except Exception as ex:
            deb('onRedrawEPG Exception: {}'.format(ex))
            return self.catchupChannels

    def getPredefinedCategories(self):
        predefinedCategories = []

        categories = self.database.getPredefinedCategoriesDb()
        for cat in categories:
            predefinedCategories.append('{0}: {1}'.format(strings(30995), cat.upper()))

        predefinedCategories.insert(0, strings(30325))
        return predefinedCategories

    def _clearEpg(self):
        deb('_clearEpg')
        if self.timebar:
            try:
                self.removeControl(self.timebar)
            except:
                pass  # happens if we try to remove a control that doesn't exist

        if self.timebarBack:
            try:
                self.removeControl(self.timebarBack)
            except:
                pass  # happens if we try to remove a control that doesn't exist

        controls = [elem.control for elem in self.controlAndProgramList]
        try:
            self.removeControls(controls)

        except RuntimeError:
            for elem in self.controlAndProgramList:
                try:
                    self.removeControl(elem.control)
                except RuntimeError:
                    pass  # happens if we try to remove a control that doesn't exist

        try:
            self.category = self.database.category

            try:
                self.category = self.category
            except:
                self.category = ''

            self.categories = self.database.getAllCategories()

            listControl = self.getControl(self.C_MAIN_CATEGORY)
            listControl.reset()

            items = []

            categories = self.predefinedCategories + list(self.categories)

            for label in categories:
                item = xbmcgui.ListItem(label)
                items.append(item)

            listControl.addItems(items)

            if sys.version_info[0] < 3:
                self.category = self.category.decode('utf-8')

            if self.category and self.category in categories:
                index = categories.index(self.category)
                if index >= 0:
                    listControl.selectItem(index)

        except:
            deb('Categories not supported by current skin')
            self.category = None

        self.getListLenght = self.getChannelListLenght()

        del self.controlAndProgramList[:]
        debug('_clearEpg end')

    def onEPGLoadError(self):
        deb('onEPGLoadError, M_TVGUIDE_CLOSING: {}'.format(strings2.M_TVGUIDE_CLOSING))
        self.redrawingEPG = False
        self._hideControl(self.C_MAIN_LOADING)
        if not strings2.M_TVGUIDE_CLOSING:
            if ADDON.getSetting('source') == '0':
                xbmcgui.Dialog().ok(strings(LOAD_ERROR_TITLE), strings(LOAD_ERROR_LINE1) + '\n' + ADDON.getSetting('xmltv_file').strip() + '\n' + strings(LOAD_ERROR_LINE2))
            else:
                xbmcgui.Dialog().ok(strings(LOAD_ERROR_TITLE), strings(LOAD_ERROR_LINE1) + '\n' + ADDON.getSetting('m-TVGuide').strip() + '\n' + strings(LOAD_ERROR_LINE2))
        self.close()

    def onSourceNotConfigured(self):
        deb('onSourceNotConfigured')
        self.redrawingEPG = False
        self._hideControl(self.C_MAIN_LOADING)
        if ADDON.getSetting('source') == '0':
            xbmcgui.Dialog().ok(strings(LOAD_ERROR_TITLE), strings(LOAD_ERROR_LINE1) + '\n' + ADDON.getSetting('xmltv_file').strip() + '\n' + strings(LOAD_ERROR_LINE2))
        else:
            xbmcgui.Dialog().ok(strings(LOAD_ERROR_TITLE), strings(LOAD_ERROR_LINE1) + '\n' + ADDON.getSetting('m-TVGuide').strip() + '\n' + strings(LOAD_ERROR_LINE2))
        self.close()

    def isSourceInitializationCancelled(self):
        initialization_cancelled = strings2.M_TVGUIDE_CLOSING or self.isClosing
        deb('isSourceInitializationCancelled: {}'.format(initialization_cancelled))
        return initialization_cancelled

    def onSourceInitialized(self, success):
        deb('onSourceInitialized')

        result = Skin.checkForUpdates()
        if result:
            super(mTVGuide, self).close()

        if success:
            self.notification = Notification(self.database, ADDON.getAddonInfo('path'), self)
            if ADDON.getSetting('program_notifications_enabled') == 'true':
                self.notification.scheduleNotifications()

            if ADDON.getSetting('background_services') == 'true':
                background = True
            else:
                background = False

            if not background:
                self.recordService.scheduleAllRecordings()

            if ADDON.getSetting('service_notifications_enabled') == 'true':
                urls = [RSS_FILE, RSS_FILE_BACKUP]
                self.rssFeed = src.RssFeed(url=urls, last_message=self.database.getLastRssDate(), update_date_call=self.database.updateRssDate)

            if strings2.M_TVGUIDE_CLOSING == False:

                if ADDON.getSetting('channel_shortcut') == 'true':
                    self.disableUnusedChannelControls(self.C_CHANNEL_LABEL_START_INDEX)
                    self.disableUnusedChannelControls(self.C_CHANNEL_IMAGE_START_INDEX)
                else:
                    self.disableUnusedChannelControls(self.C_CHANNEL_LABEL_START_INDEX_SHORTCUT)
                    self.disableUnusedChannelControls(self.C_CHANNEL_IMAGE_START_INDEX_SHORTCUT)
                    self.disableUnusedChannelControls(self.C_CHANNEL_NUMBER_START_INDEX_SHORTCUT)

                category = ADDON.getSetting('category')

                if ADDON.getSetting('categories_remember') == 'true' or category != '':
                    self.database.setCategory(category)

                res = self.onRedrawEPG(0, self.viewStartDate, initializing=True)

                try:
                    if len(res) == 0:
                        self.database.setCategory(strings(30325))
                        ADDON.setSetting('category', strings(30325))
                        self._clearEpg()
                        self.onRedrawEPG(0, self.viewStartDate, initializing=False)
                        if not self.controlAndProgramList:
                            playlists = []
                            cached = []

                            for i in playService.SERVICES:
                                if 'playlist_' in i:
                                    if ADDON.getSetting('{}_append_country_code'.format(i)) == '':
                                        playlists.append(i)

                                    if ADDON.getSetting('{}_refr'.format(i)) == 'true':
                                        cached.append(i)

                            if xbmc.getCondVisibility('!Window.IsVisible(notification)'):
                                if not playService.SERVICES:
                                    info = xbmcgui.Dialog().ok(strings(57051), strings(30175))

                                elif cached:
                                    info = xbmcgui.Dialog().ok(strings(57051), strings(30176))

                                elif playlists:
                                    info = xbmcgui.Dialog().ok(strings(57051), strings(30167))

                                elif ADDON.getSetting('epg_display_name') == 'false':
                                    info = xbmcgui.Dialog().ok(strings(57051), strings(30166))

                                else:
                                    info = xbmcgui.Dialog().ok(strings(57051), strings(30168))

                                res = xbmcgui.Dialog().yesno(strings(57051), strings(30165))
                                if res:
                                    super(mTVGuide, self).close()
                            else:
                                res = xbmcgui.Dialog().yesno(strings(57051), strings(30169))
                                if res:
                                    super(mTVGuide, self).close()

                except:
                    pass

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
            self._showControl(self.C_MAIN_LOADING)
            self.setFocusId(self.C_MAIN_LOADING_CANCEL)
            self.setControlLabel(self.C_MAIN_LOADING_TIME_LEFT, strings(CALCULATING_REMAINING_TIME))

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

            if percentageComplete < 15:
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
            self.viewStartDate = datetime.datetime.today() + datetime.timedelta(minutes=int(timebarAdjust()))
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
        if self.getChannelNumber() == self.getListLenght and xbmc.getCondVisibility('Control.IsVisible(7900)'):
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
        if self.getChannelNumber() == 1 and xbmc.getCondVisibility('Control.IsVisible(7900)'):
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
                try:
                    program = self.program
                except:
                    program = self.database.getCurrentProgram(self.currentChannel)
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
        try:
            for controlId in controlIds:
                control = self.getControl(controlId)
                if control:
                    control.setVisible(True)
        except:
            pass

    def _showControl(self, *controlIds):
        debug('_showControl')
        """
        Visibility is inverted in skin
        """
        try:
            for controlId in controlIds:
                control = self.getControl(controlId)
                if control:
                    control.setVisible(False)
        except:
            pass

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
            timeDelta = datetime.datetime.today() - self.viewStartDate + datetime.timedelta(minutes=int(timebarAdjust()))

            control = self.getControl(self.C_MAIN_TIMEBAR)
            background = self.getControl(self.C_MAIN_TIMEBAR_BACK)

            if control and background:
                (x, y) = control.getPosition()
                try:
                    # Sometimes raises:
                    # exceptions.RuntimeError: Unknown exception thrown from the call "setVisible"
                    control.setVisible(timeDelta.days == 0)
                    background.setVisible(timeDelta.days == 0)
                except Exception as ex:
                    debug('updateTimebar error: {}'.format(ex))
                    pass

                xPositionBar = self._secondsToXposition(timeDelta.seconds)
                control.setPosition(xPositionBar, y)
                if self.timebar:
                    self.timebar.setPosition(xPositionBar, y)

                if self.viewStartDate.date() == self.lastKeystroke.date():
                    marker = self.getControl(self.C_MAIN_EPG_VIEW_MARKER)
                    p = marker.getWidth()

                    if self.timebarBack:
                        (x, y) = background.getPosition()
                        #w = background.getWidth()
                        background.setWidth(xPositionBar - x + 13)
                        self.timebarBack.setWidth(xPositionBar - x + 13)

                    if xPositionBar > (self.epgView.left + ((self.epgView.right - self.epgView.left) * 0.8)):
                        # Time bar exceeded EPG
                        # Check how long was since EPG was used
                        background.setWidth(p - int(cell_width))
                        self.timebarBack.setWidth(p - int(cell_width))

                        diff = datetime.datetime.now() - self.lastKeystroke
                        diffSeconds = (diff.days * 86400) + diff.seconds
                        #debug('updateTimebar seconds since last user action {}'.format(diffSeconds))
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
                    #debug('updateTimebar seconds since last user action {}'.format(diffSeconds))
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
                    if self.timebar is not None and self.timebarBack is not None:
                        if self.lastKeystroke >= self.viewStartDate:# and xbmc.getCondVisibility('!Control.IsVisible(5000)'):
                            if self.viewStartDate.date() == self.lastKeystroke.date():
                                self.timebar.setVisible(True)
                                self.timebarBack.setVisible(True)
                            else:
                                self.timebar.setVisible(False)
                                self.timebarBack.setVisible(True)

                        else:
                            self.timebar.setVisible(False)
                            self.timebarBack.setVisible(False)

                except Exception as ex:
                    debug('setVisible error: {}'.format(ex))

            if scheduleTimer and not strings2.M_TVGUIDE_CLOSING and not self.isClosing:
                if self.updateTimebarTimer is not None:
                    self.updateTimebarTimer.cancel()
                self.updateTimebarTimer = threading.Timer(20, self.updateTimebar)
                self.updateTimebarTimer.start()
        except Exception as ex:
            pass

    def refreshStreamsLoop(self):
        if self.autoUpdateCid == 'true':
            refreshTime = REFRESH_STREAMS_TIME
            if not strings2.M_TVGUIDE_CLOSING and not self.isClosing and self.database and self.recordService and self.playService and not self.playService.isWorking() and self.checkUrl():
                if datetime.datetime.now().hour < 8:
                    refreshTime = 3600
                else:
                    diff = datetime.datetime.now() - self.lastKeystroke
                    diffSeconds = (diff.days * 86400) + diff.seconds
                    if diffSeconds > 30:
                        deb('refreshStreamsLoop refreshing all services')
                        self.database.reloadServices()
                        if not self.recordService.isRecordOngoing() and not xbmc.Player().isPlaying():
                            self.onRedrawEPG(self.channelIdx, self.viewStartDate, self._getCurrentProgramFocus)
                    else:
                        deb('refreshStreamsLoop services will be refreshed if no activity for 60s, currently no activity for {} seconds'.format(diffSeconds))
                        refreshTime = 1
            else:
                refreshTime = 600
                deb('refreshStreamsLoop delaying service refresh for {} seconds due to playback or record'.format(refreshTime))

            if not strings2.M_TVGUIDE_CLOSING and not self.isClosing:
                self.refreshStreamsTimer = threading.Timer(refreshTime, self.refreshStreamsLoop)
                self.refreshStreamsTimer.start()
        else:
            self.refreshStreamsTimer = None

    def checkUrl(url='https://www.google.com'):
        try:
            if PY3:
                import urllib.request as Request
            else:
                import urllib2 as Request

            open = Request.urlopen(url, timeout=3)
            if (open):
                open.read()
                return True
        except:
            pass
        return False


class PopupMenu(xbmcgui.WindowXMLDialog):
    C_POPUP_PLAY = 4000
    C_POPUP_RECORDINGS = 4006
    C_POPUP_CHANNEL_LOGO = 4100
    C_POPUP_CHANNEL_TITLE = 4101
    C_POPUP_PROGRAM_TITLE = 4102
    C_POPUP_PROGRAM_TIME_RANGE = 4103
    C_POPUP_CATEGORY = 7004
    C_POPUP_GROUP = 4012
    C_POPUP_FAQ = 4013
    C_POPUP_FAVOURITES = 4014
    C_POPUP_ADD_CHANNEL = 4015
    C_POPUP_REMOVE_CHANNEL = 4016
    C_MAIN_SLIDE_CLICK = 4976

    def __new__(cls, database, program, predefinedCategories):
        return super(PopupMenu, cls).__new__(cls, 'script-tvguide-menu.xml', Skin.getSkinBasePath(), Skin.getSkinName(), skin_resolution)

    def __init__(self, database, program, predefinedCategories):
        """

        @type database: source.Database
        @param program:
        @type program: source.Program
        @param showRemind:
        """
        super(PopupMenu, self).__init__()
        self.database = database
        self.program = program
        self.predefinedCategories = predefinedCategories
        self.buttonClicked = None
        self.category = self.database.category
        self.categories = self.database.getAllCategories()

    def onInit(self):
        playControl = self.getControl(self.C_POPUP_PLAY)
        channelLogoControl = self.getControl(self.C_POPUP_CHANNEL_LOGO)
        channelTitleControl = self.getControl(self.C_POPUP_CHANNEL_TITLE)
        programTitleControl = self.getControl(self.C_POPUP_PROGRAM_TITLE)
        programTimeRangeControl = self.getControl(self.C_POPUP_PROGRAM_TIME_RANGE)

        try:
            listControl = self.getControl(self.C_POPUP_CATEGORY)
            listControl.reset()

            items = []

            categories = self.predefinedCategories + list(self.categories)
            categories = [label.replace('TV Group', strings(30995)) for label in categories]

            for label in categories:
                item = xbmcgui.ListItem(label)
                items.append(item)

            listControl.addItems(items)

            if sys.version_info[0] < 3:
                self.category = self.category.decode('utf-8')

            if self.category and self.category in categories:
                index = categories.index(self.category)
                if index >= 0:
                    listControl.selectItem(index)
        except:
            deb('Categories not supported by current skin')
            self.category = None

        if self.program is not None:
            if self.program.channel.title:
                playControl.setLabel(strings(WATCH_CHANNEL, self.program.channel.title))
                if not self.program.channel.isPlayable():
                    playControl.setEnabled(False)

            if self.program.channel.logo is not None:
                channelLogoControl.setImage(self.program.channel.logo)
                channelTitleControl.setVisible(False)
            else:
                channelTitleControl.setLabel(self.program.channel.title)
                channelLogoControl.setVisible(False)

            programTitleControl.setLabel(self.program.title)

            if programTimeRangeControl is not None:
                programTimeRangeControl.setLabel('{} - {}'.format(self.formatTime(self.program.startDate), self.formatTime(self.program.endDate)))

    def onAction(self, action):
        if action.getId() == self.C_MAIN_SLIDE_CLICK:
            self.close()
            return

        if action.getId() in [ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, KEY_NAV_BACK]:
            self.close()
            return

        elif action.getId() in [KEY_CONTEXT_MENU] and xbmc.getCondVisibility('!Control.HasFocus(7004)'):
            self.close()
            return

        elif action.getId() in [KEY_CONTEXT_MENU] and xbmc.getCondVisibility('Control.HasFocus(7004)'):
            cList = self.getControl(self.C_POPUP_CATEGORY)
            label = cList.getSelectedItem().getLabel()

            if label in self.predefinedCategories or cList.getSelectedPosition() == 0:
                return

            item = cList.getSelectedItem()
            if item:
                self.category = item.getLabel()

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
                channelList = sorted([channel.title for channel in self.database.getChannelList(onlyVisible=True, customCategory=None, excludeCurrentCategory=True)])

                try:
                    string = strings(30989).format(self.category)
                except:
                    string = strings(30989).format(self.category.decode('utf-8'))
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
                try:
                    string = strings(30990).format(self.category)
                except:
                    string = strings(30990).format(self.category.decode('utf-8'))
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
            self.close()

    def onClick(self, controlId):
        if controlId == self.C_POPUP_CATEGORY:
            cList = self.getControl(self.C_POPUP_CATEGORY)
            if cList.getSelectedPosition() == 0:
                self.category = None
            else:
                item = cList.getSelectedItem()
                if item:
                    self.category = item.getLabel()

            self.buttonClicked = controlId
            self.close()

        elif controlId == self.C_POPUP_GROUP:
            try:
                dialog = xbmcgui.Dialog()
                cat = dialog.input(strings(30984), type=xbmcgui.INPUT_ALPHANUM)
                if cat:
                    categories = set(self.categories)
                    categories.add(cat)
                    self.categories = list(set(categories))

                    items = []

                    categories = self.predefinedCategories + list(self.categories)

                    for label in categories:
                        item = xbmcgui.ListItem(label)
                        items.append(item)

                    listControl = self.getControl(self.C_POPUP_CATEGORY)
                    listControl.reset()

                    listControl.addItems(items)
                    listControl.selectItem(categories.index(cat))

                    self.setFocusId(self.C_POPUP_CATEGORY)
                    xbmc.sleep(300)
                    xbmc.executebuiltin('Action(ContextMenu)')
            except:
                deb('Categories not supported by current skin')
                self.category = None

        else:
            self.buttonClicked = controlId
            self.close()

    def formatTime(self, timestamp):
        #deb('formatTime')
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

    def close(self):
        super(ChannelsMenu, self).close()


class StreamSetupDialog(xbmcgui.WindowXMLDialog):
    C_STREAM_STRM_TAB = 101
    C_STREAM_FAVOURITES_TAB = 102
    C_STREAM_ADDONS_TAB = 103
    C_STREAM_BROWSE_TAB = 104
    C_STREAM_PLAYLIST_TAB = 108
    C_STREAM_STRM_BROWSE = 1001
    C_STREAM_STRM_PREVIEW = 1002
    C_STREAM_STRM_OK = 1003
    C_STREAM_STRM_CANCEL = 1004
    C_STREAM_STRM_FILE_LABEL = 1005
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
    C_STREAM_BROWSE_ADDONS = 4001
    C_STREAM_BROWSE_DIRS = 4002
    C_STREAM_BROWSE_NAME = 4003
    C_STREAM_BROWSE_DESCRIPTION = 4004
    C_STREAM_BROWSE_PREVIEW = 4005
    C_STREAM_BROWSE_OK = 4006
    C_STREAM_BROWSE_CANCEL = 4007
    C_STREAM_PLAYLIST_STREAMS = 8002
    C_STREAM_PLAYLIST_PREVIEW = 8005
    C_STREAM_PLAYLIST_OK = 8006
    C_STREAM_PLAYLIST_CANCEL = 8007

    C_STREAM_VISIBILITY_MARKER = 100

    VISIBLE_STRM = 'strm'
    VISIBLE_FAVOURITES = 'favourites'
    VISIBLE_ADDONS = 'addons'
    VISIBLE_BROWSE = 'browse'
    VISIBLE_PLAYLIST = 'playlist'

    def __new__(cls, database, channel, epg):
        return super(StreamSetupDialog, cls).__new__(cls, 'script-tvguide-streamsetup.xml', Skin.getSkinBasePath(), Skin.getSkinName(), skin_resolution)

    def __init__(self, database, channel, epg):
        """
        @type database: source.Database
        @type channel:source.Channel
        """
        super(StreamSetupDialog, self).__init__()
        self.epg = epg
        self.database = database
        self.channel = channel
        self.previousAddonId = None
        self.previousDirsId = None
        self.returnContent = None
        self.playable = None
        self.previousBrowseId = None
        self.strmFile = None
        self.streamingService = streaming.StreamsService()

        if PY3:
            try:
                self.profilePath  = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
            except:
                self.profilePath  = xbmcvfs.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')
        else:
            try:
                self.profilePath  = xbmc.translatePath(ADDON.getAddonInfo('profile'))
            except:
                self.profilePath  = xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')


    def onInit(self):
        xbmc.executebuiltin('ActivateWindow(busydialognocancel)')

        self.getControl(self.C_STREAM_VISIBILITY_MARKER).setLabel(self.VISIBLE_STRM)

        favourites = self.streamingService.loadFavourites()
        items = []
        for label, value in favourites:
            item = xbmcgui.ListItem(label)
            item.setProperty('stream', value)
            items.append(item)

        listControl = self.getControl(StreamSetupDialog.C_STREAM_FAVOURITES)
        listControl.addItems(items)

        items = []
        for id in self.streamingService.getAddons():
            if PY3:
                try:
                    addon = xbmcaddon.Addon(id)  # raises Exception if addon is not installed
                    item = xbmcgui.ListItem(addon.getAddonInfo('name'))
                    item.setArt({'icon': addon.getAddonInfo('icon'), 'thumb': addon.getAddonInfo('icon')})
                    item.setProperty('addon_id', id)
                    items.append(item)
                except Exception as ex:
                    pass
            else:
                try:
                    addon = xbmcaddon.Addon(id)  # raises Exception if addon is not installed
                    item = xbmcgui.ListItem(addon.getAddonInfo('name'), iconImage=addon.getAddonInfo('icon'))
                    item.setProperty('addon_id', id)
                    items.append(item)
                except Exception as ex:
                    pass
        listControl = self.getControl(StreamSetupDialog.C_STREAM_ADDONS)
        listControl.addItems(items)
        self.updateAddonInfo()

        response = json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Addons.GetAddons", "id":1}'))
        addons = response["result"]["addons"]
        items = []
        for id in addons:
            pattern = re.compile('^plugin')
            if pattern.match(str(id['addonid'])):
                if id.get('type', '') == 'xbmc.python.pluginsource':
                    try:
                        id = str(id['addonid'])
                        addon = xbmcaddon.Addon(id=id) # raises Exception if addon is not installed
                        item = xbmcgui.ListItem(addon.getAddonInfo('name'))
                        item.setArt({'icon': addon.getAddonInfo('icon'), 'thumb': addon.getAddonInfo('icon')})
                        item.setProperty('addon_id', id)
                        items.append(item)
                    except Exception as ex:
                        deb('Addons.GetAddons Exception: {}'.format(ex))
                        pass

        listControl = self.getControl(StreamSetupDialog.C_STREAM_BROWSE_ADDONS)
        listControl.addItems(items)
        self.updateDirsInfo()

        file = xbmcvfs.File(os.path.join(self.profilePath, 'custom_channels.list'), 'r')
        strmList = file.read().splitlines()

        strmList = sorted(set(strmList))

        items = []
        for i in strmList:
            playlist = i.split(',')
            if playlist:
                label = playlist[0].strip('(\'\')').strip()
                stream = playlist[-1].strip('(\'\')').strip()
                item = xbmcgui.ListItem(label)
                item.setProperty('stream', stream)
                items.append(item)

        listControl = self.getControl(StreamSetupDialog.C_STREAM_PLAYLIST_STREAMS)
        listControl.addItems(items)


    def onAction(self, action):
        if action.getId() in [ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, KEY_NAV_BACK, KEY_CONTEXT_MENU] or action.getButtonCode() in [KEY_CONTEXT]:
            if xbmc.Player().isPlaying():
                xbmc.Player().stop()
            else:
                self.close()
                return self.epg.onRedrawEPG(self.epg.channelIdx, self.epg.viewStartDate)

        if self.getFocusId() == self.C_STREAM_ADDONS:
            self.updateAddonInfo()

        elif self.getFocusId() == self.C_STREAM_BROWSE_ADDONS:
            self.updateDirsInfo()

    def onClick(self, controlId):
        try:
            if controlId == self.C_STREAM_BROWSE_ADDONS:
                self.updateDirsInfo()

            elif controlId == self.C_STREAM_BROWSE_DIRS:
                self.updateBrowseInfo()

            elif controlId == self.C_STREAM_STRM_BROWSE:
                stream = xbmcgui.Dialog().browse(1, ADDON.getLocalizedString(30304), 'video', '.strm')
                if stream:
                    self.database.setCustomStreamUrl(self.channel, stream)
                    self.getControl(self.C_STREAM_STRM_FILE_LABEL).setText(stream)
                    self.strmFile = stream

            elif controlId == self.C_STREAM_BROWSE_OK:
                listControl = self.getControl(self.C_STREAM_BROWSE_DIRS)
                item = listControl.getSelectedItem()
                if item and self.playable:
                    stream = self.strmFile
                    self.database.setCustomStreamUrl(self.channel, stream)
                    xbmcgui.Dialog().notification(self.channel.title, strings(59993).format(item.getLabel()))
                else:
                    return
                self.close()
                return self.epg.onRedrawEPG(self.epg.channelIdx, self.epg.viewStartDate, self.epg._getCurrentProgramFocus)

            elif controlId == self.C_STREAM_ADDONS_OK:
                listControl = self.getControl(self.C_STREAM_ADDONS_STREAMS)
                item = listControl.getSelectedItem()
                if item:
                    stream = item.getProperty('stream')
                    self.database.setCustomStreamUrl(self.channel, stream)
                    xbmcgui.Dialog().notification(self.channel.title, strings(59993).format(item.getLabel()))
                self.close()
                return self.epg.onRedrawEPG(self.epg.channelIdx, self.epg.viewStartDate, self.epg._getCurrentProgramFocus)

            elif controlId == self.C_STREAM_FAVOURITES_OK:
                listControl = self.getControl(self.C_STREAM_FAVOURITES)
                item = listControl.getSelectedItem()
                if item:
                    stream = item.getProperty('stream')
                    self.database.setCustomStreamUrl(self.channel, stream)
                    xbmcgui.Dialog().notification(self.channel.title, strings(59993).format(item.getLabel()))
                self.close()
                return self.epg.onRedrawEPG(self.epg.channelIdx, self.epg.viewStartDate, self.epg._getCurrentProgramFocus)

            elif controlId == self.C_STREAM_STRM_OK:
                listControl = self.getControl(self.C_STREAM_STRM_BROWSE)
                item = listControl.getSelectedItem()
                if item:
                    stream = item.getProperty('stream')
                    self.database.setCustomStreamUrl(self.channel, stream)
                    xbmcgui.Dialog().notification(self.channel.title, strings(59993).format(item.getLabel()))
                self.close()
                return self.epg.onRedrawEPG(self.epg.channelIdx, self.epg.viewStartDate, self.epg._getCurrentProgramFocus)

            elif controlId == self.C_STREAM_PLAYLIST_OK:
                listControl = self.getControl(self.C_STREAM_PLAYLIST_STREAMS)
                item = listControl.getSelectedItem()
                if item:
                    stream = item.getProperty('stream')
                    self.database.setCustomStreamUrl(self.channel, stream)
                    xbmcgui.Dialog().notification(self.channel.title, strings(59993).format(item.getLabel()))
                self.close()
                return self.epg.onRedrawEPG(self.epg.channelIdx, self.epg.viewStartDate, self.epg._getCurrentProgramFocus)

            elif controlId in [self.C_STREAM_ADDONS_CANCEL, self.C_STREAM_FAVOURITES_CANCEL, self.C_STREAM_STRM_CANCEL, self.C_STREAM_BROWSE_CANCEL, self.C_STREAM_PLAYLIST_CANCEL]:
                self.close()
                return self.epg.onRedrawEPG(self.epg.channelIdx, self.epg.viewStartDate)

            elif controlId in [self.C_STREAM_ADDONS_PREVIEW, self.C_STREAM_FAVOURITES_PREVIEW, self.C_STREAM_STRM_PREVIEW, self.C_STREAM_BROWSE_PREVIEW, self.C_STREAM_PLAYLIST_PREVIEW]:
                if xbmc.Player().isPlaying():
                    xbmc.Player().stop()
                    self.getControl(self.C_STREAM_ADDONS_PREVIEW).setLabel(strings(PREVIEW_STREAM))
                    self.getControl(self.C_STREAM_FAVOURITES_PREVIEW).setLabel(strings(PREVIEW_STREAM))
                    self.getControl(self.C_STREAM_STRM_PREVIEW).setLabel(strings(PREVIEW_STREAM))
                    self.getControl(self.C_STREAM_BROWSE_PREVIEW).setLabel(strings(PREVIEW_STREAM))
                    self.getControl(self.C_STREAM_PLAYLIST_PREVIEW).setLabel(strings(PREVIEW_STREAM))
                    return

        except:
            self.close()
            return self.epg.onRedrawEPG(self.epg.channelIdx, self.epg.viewStartDate, self.epg._getCurrentProgramFocus)

            stream = None
            visible = self.getControl(self.C_STREAM_VISIBILITY_MARKER).getLabel()
            if visible == self.VISIBLE_ADDONS:
                listControl = self.getControl(self.C_STREAM_ADDONS_STREAMS)
                item = listControl.getSelectedItem()
                if item:
                    stream = item.getProperty('stream')

            if visible == self.VISIBLE_FAVOURITES:
                listControl = self.getControl(self.C_STREAM_FAVOURITES)
                item = listControl.getSelectedItem()
                if item:
                    stream = item.getProperty('stream')

            if visible == self.VISIBLE_STRM:
                stream = self.strmFile

            if visible == self.VISIBLE_BROWSE:
                listControl = self.getControl(self.C_STREAM_BROWSE_ADDONS)
                item = listControl.getSelectedItem()
                if item and self.playable:
                    stream = self.strmFile

            if visible == self.VISIBLE_PLAYLIST:
                listControl = self.getControl(self.C_STREAM_PLAYLIST_STREAMS)
                item = listControl.getSelectedItem()
                if item:
                    stream = item.getProperty('stream')

            if stream is not None:
                self.playChannel(stream)
                if xbmc.Player().isPlaying():
                    self.getControl(self.C_STREAM_ADDONS_PREVIEW).setLabel(strings(STOP_PREVIEW))
                    self.getControl(self.C_STREAM_FAVOURITES_PREVIEW).setLabel(strings(STOP_PREVIEW))
                    self.getControl(self.C_STREAM_STRM_PREVIEW).setLabel(strings(STOP_PREVIEW))
                    self.getControl(self.C_STREAM_BROWSE_PREVIEW).setLabel(strings(STOP_PREVIEW))
                    self.getControl(self.C_STREAM_PLAYLIST_PREVIEW).setLabel(strings(STOP_PREVIEW))

    def onFocus(self, controlId):
        if controlId == self.C_STREAM_STRM_TAB:
            self.getControl(self.C_STREAM_VISIBILITY_MARKER).setLabel(self.VISIBLE_STRM)

        if controlId == self.C_STREAM_FAVOURITES_TAB:
            self.getControl(self.C_STREAM_VISIBILITY_MARKER).setLabel(self.VISIBLE_FAVOURITES)

        if controlId == self.C_STREAM_ADDONS_TAB:
            self.getControl(self.C_STREAM_VISIBILITY_MARKER).setLabel(self.VISIBLE_ADDONS)

        if controlId == self.C_STREAM_BROWSE_TAB:
            self.getControl(self.C_STREAM_VISIBILITY_MARKER).setLabel(self.VISIBLE_BROWSE)

        if controlId == self.C_STREAM_PLAYLIST_TAB:
            self.getControl(self.C_STREAM_VISIBILITY_MARKER).setLabel(self.VISIBLE_PLAYLIST)

    def playChannel(self, stream):
        #debug('Pla playChannel: {}'.format(stream))

        channel = Channel(id='StreamSetupDialog', title='StreamSetupDialog', logo='', titles='', streamUrl=stream, visible='', weight='')

        urlList = self.database.getStreamUrlList(channel)
        if len(urlList) > 0:
            self.epg.playService.playUrlList(urlList, '', '', resetReconnectCounter=True)

    def updateAddonInfo(self):
        listControl = self.getControl(self.C_STREAM_ADDONS)
        item = listControl.getSelectedItem()
        if item is None:
            return

        if item.getProperty('addon_id') == self.previousAddonId:
            return

        self.previousAddonId = item.getProperty('addon_id')
        addon = xbmcaddon.Addon(id=item.getProperty('addon_id'))
        self.getControl(self.C_STREAM_ADDONS_NAME).setLabel('[B]%s[/B]' % addon.getAddonInfo('name'))
        self.getControl(self.C_STREAM_ADDONS_DESCRIPTION).setText(addon.getAddonInfo('description'))

        streams = self.streamingService.getAddonStreams(item.getProperty('addon_id'))
        items = []
        for (label, stream) in streams:
            if item.getProperty('addon_id') == "plugin.video.meta":
                label = self.channel.title
                stream = stream.replace("<channel>", self.channel.title.replace(" ","%20"))
            item = xbmcgui.ListItem(label)
            item.setProperty('stream', stream)
            items.append(item)
        listControl = self.getControl(StreamSetupDialog.C_STREAM_ADDONS_STREAMS)
        listControl.reset()
        listControl.addItems(items)

    def updateDirsInfo(self):
        try:
            listControl = self.getControl(self.C_STREAM_BROWSE_ADDONS)
            item = listControl.getSelectedItem()
            if item is None:
                return

            self.previousBrowseId = item.getProperty('addon_id')

            try:
                addon = xbmcaddon.Addon(id=item.getProperty('addon_id'))
            except:
                return

            self.getControl(self.C_STREAM_BROWSE_NAME).setLabel('[B]%s[/B]' % addon.getAddonInfo('name'))
            self.getControl(self.C_STREAM_BROWSE_DESCRIPTION).setText(addon.getAddonInfo('description'))

            id = addon.getAddonInfo('id')
            if id == xbmcaddon.Addon().getAddonInfo('id'):
                return

            path = "plugin://%s" % id
            self.previousDirsId = path
            self.returnContent = path

            response = json.loads(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Files.GetDirectory", "params": {"directory": "%s", "media":"files"}, "id": 100}' % path))
            files = response["result"]["files"]

            dirs = dict([[f["label"], f["file"]] for f in files if f["filetype"] == "directory"])

            items = []
            item = xbmcgui.ListItem(addon.getAddonInfo('name'))
            item.setProperty('stream', path)
            items.append(item)
            
            for label in dirs:
                stream = dirs[label]
                if item.getProperty('addon_id') == "plugin.video.meta":
                    label = self.channel.title
                stream = stream.replace("<channel>", self.channel.title.replace(" ","%20"))
                item = xbmcgui.ListItem(label)
                item.setProperty('stream', stream)
                items.append(item)

            listControl = self.getControl(StreamSetupDialog.C_STREAM_BROWSE_DIRS)
            listControl.reset()
            listControl.addItems(items)

        except:
            pass

        xbmc.executebuiltin('Dialog.Close(busydialognocancel)')

    def updateBrowseInfo(self):
        listControl = self.getControl(self.C_STREAM_BROWSE_DIRS)
        item = listControl.getSelectedItem()
        if item is None:
            return

        previousDirsId = self.previousDirsId
        self.previousDirsId = item.getProperty('stream')

        if item.getLabel() == '[B]..[/B]':
            item.setProperty('stream', self.returnContent)
            self.previousDirsId = item.getProperty('stream')
            self.playable = False

        else:
            if self.playable:
                self.previousDirsId = previousDirsId
                self.playable = False
        
        try:
            response = json.loads(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Files.GetDirectory", "params": {"directory": "%s", "media":"files"}, "id": 100}' % self.previousDirsId))
            files = response["result"]["files"]
            
            dirs = {}
            items = []

            item = xbmcgui.ListItem('[B]..[/B]')
            item.setProperty('stream', self.returnContent)
            items.append(item)

            for prop in files:
                dirs.update(prop)
                stream = dirs.get('file')
                label = dirs.get('label')
                if dirs.get('filetype') == 'file':
                    self.playable = True
                    self.strmFile = item.getProperty('stream')
                item = xbmcgui.ListItem(label)
                item.setProperty('stream', stream)
                items.append(item)
            
            listControl = self.getControl(StreamSetupDialog.C_STREAM_BROWSE_DIRS)
            listControl.reset()
            listControl.addItems(items)
        
        except:
            self.previousDirsId = previousDirsId
            if self.playable:
                self.playable = False

    def close(self):
        super(StreamSetupDialog, self).close()

class ChooseStreamAddonDialog(xbmcgui.WindowXMLDialog):
    C_SELECTION_LIST = 1000

    def __new__(cls, addons):
        return super(ChooseStreamAddonDialog, cls).__new__(cls, 'script-tvguide-streamaddon.xml', Skin.getSkinBasePath(), Skin.getSkinName(), skin_resolution)

    def __init__(self, addons):
        super(ChooseStreamAddonDialog, self).__init__()
        self.addons = addons
        self.stream = None

    def onInit(self):
        items = []
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

    def close(self):
        super(ChooseStreamAddonDialog, self).close()


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
        self.ignoreMissingControlIds = []

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

        nowDay = now.strftime("%a").replace('Mon', xbmc.getLocalizedString(11)).replace('Tue', xbmc.getLocalizedString(12)).replace('Wed', xbmc.getLocalizedString(13)).replace('Thu', xbmc.getLocalizedString(14)).replace('Fri', xbmc.getLocalizedString(15)).replace('Sat', xbmc.getLocalizedString(16)).replace('Sun', xbmc.getLocalizedString(17))
        nowDate = now.strftime("%d.%m.%Y")

        self.setControlLabel(C_MAIN_DAY, '{}'.format(nowDate))
        self.setControlLabel(C_MAIN_REAL_DATE, '{}'.format(nowDay))

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
                    if icon == '':
                        if PY3:
                            addonPath = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
                        else:
                            addonPath = xbmc.translatePath(ADDON.getAddonInfo('path'))

                        number_regex = re.compile('(\d+)')

                        r = number_regex.search(str(self.program.rating))
                        age = r.group(1) if r else ''

                        if age == '3':
                            age = '0'

                        icon = os.path.join(addonPath, 'icons', 'age_rating', 'icon_{}.png'.format(age))

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

            if skin_separate_rating:
                try:
                    ratingControl = self.getControl(C_PROGRAM_RATING)
                    rating = descriptionParser.extractRating()
                    if rating == '':
                        rating = self.program.rating
                    ratingControl.setText(rating)
                except:
                    pass

            description = descriptionParser.description

        self.setControlText(C_MAIN_DESCRIPTION, description)

        if self.program.channel.logo is not None:
            self.setControlImage(C_MAIN_LOGO, self.program.channel.logo)
        if self.program.imageSmall is not None and ADDON.getSetting('show_program_logo') == "true":
            self.setControlImage(C_MAIN_IMAGE, self.program.imageSmall)
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
                    self.notification.addNotification(self.program, onlyOnce = True)
                else:
                    self.notification.addNotification(self.program, onlyOnce = True)
                    self.onRedrawEPG(self.channelIdx, self.viewStartDate)
                    return

        elif controlId == self.C_INFO_EXTENDED:
            self.ExtendedInfo(self.program)
            return

    def close(self):
        super(InfoDialog, self).close()

class Guide(xbmcgui.WindowXMLDialog):
    C_PROGRAM_LIST = 7000

    def __new__(cls, programs, database, program, epg):
        return super(Guide, cls).__new__(cls, 'script-tvguide-guide.xml', Skin.getSkinBasePath(), Skin.getSkinName(), skin_resolution)

    def __init__(self, programs, database, program, epg):
        # debug('Guide __init__')
        super(Guide, self).__init__()
        self.epg = epg
        self.database = database
        self.programs = programs
        self.program = program
        self.index = -1
        self.action = None

    def formatTime(self, timestamp):
        format = xbmc.getRegion('time').replace(':%S', '').replace('%H%H', '%H')
        return timestamp.strftime(format)

    def setControlLabel(self, controlId, label):
        control = self.getControl(controlId)
        if control:
            control.setLabel(label)

    def setControlText(self, controlId, text):
        control = self.getControl(controlId)
        if control:
            control.setText(text)

    def setControlImage(self, controlId, image):
        control = self.getControl(controlId)
        if control:
            control.setImage(image)

    def setFocusId(self, controlId):
        debug('setFocusId')
        control = self.getControl(controlId)
        if control:
            self.setFocus(control)

    def onInit(self):
        date = datetime.datetime.now()

        listControl = self.getControl(Guide.C_PROGRAM_LIST)
        listControl.reset()

        items = []
        idxs = []

        index = 0

        for program in self.programs:
            label = program.title
            if not label:
                label = program.channel.title
            item = xbmcgui.ListItem(label)

            item.setProperty('index', str(index))
            if program.channel.id == self.program.channel.id:
                idxs.append(index)

            index = index + 1

            description = program.description
            descriptionParser = src.ProgramDescriptionParser(description)
            episode = descriptionParser.extractEpisode()
            if episode != '':
                se_label = '{} : '.format(episode)
            else:
                se_label = ''
            try:
                episode = program.episode
                if episode:
                    se_label = '{} : '.format(episode)
            except:
                se_label = ''

            episode_regex = re.compile(r'E(\d+)', re.DOTALL)
            season_regex = re.compile(r'S(\d+)', re.DOTALL)

            r = episode_regex.search(episode)
            episode_str = r.group(1) if r else ''

            r = season_regex.search(episode)
            season_str = r.group(1) if r else ''

            label = se_label.replace(' E', 'E') + label

            icon = program.channel.logo

            startDate = str(program.startDate)
            try:
                now = datetime.proxydt.strptime(startDate, '%Y-%m-%d %H:%M:%S')
            except:
                now = datetime.proxydt.strptime(str(datetime.datetime.now()), '%Y-%m-%d %H:%M:%S.%f')

            nowDay = now.strftime("%a").replace('Mon', xbmc.getLocalizedString(11)).replace('Tue', xbmc.getLocalizedString(12)).replace('Wed', xbmc.getLocalizedString(13)).replace('Thu', xbmc.getLocalizedString(14)).replace('Fri', xbmc.getLocalizedString(15)).replace('Sat', xbmc.getLocalizedString(16)).replace('Sun', xbmc.getLocalizedString(17))
            nowDate = now.strftime("%d %m %Y")

            item.setProperty('ChannelName', replace_formatting(program.channel.title))
            item.setProperty('Plot', replace_formatting(program.description))
            item.setProperty('startDate', str(nowDay + ', ' + nowDate))

            start = program.startDate
            end = program.endDate
            duration = end - start

            now = datetime.datetime.now() + datetime.timedelta(minutes=int(timebarAdjust()))

            if now > start:
                when = datetime.timedelta(-1)
                elapsed = now - start
            else:
                when = start - now
                elapsed = datetime.timedelta(0)

            if elapsed.seconds > 0:
                progress = 100.0 * float(timedelta_total_seconds(elapsed)) // float(duration.seconds + 0.001)
                progress = str(int(progress))
            else:
                # TODO hack for progress bar with 0 time
                progress = "0"

            if progress and (int(progress) < 100):
                item.setProperty('Completed', progress)

            start_str = start.strftime("%H:%M")
            start_str = "{}".format(start_str)

            end_str = end.strftime("%H:%M")
            end_str = "{}".format(end_str)

            item.setProperty('StartTime', str(start_str))
            item.setProperty('EndTime', str(end_str))

            duration_str = "{} min".format(duration.seconds // 60)
            item.setProperty('Duration', duration_str)

            item.setInfo('video', {'title': label,  'plot': program.description, 'episode': episode_str, 'season': season_str})
            item.setArt({'thumb': icon})
            items.append(item)

        if idxs:
            idx = idxs[0]
        else:
            idx = 0

        listControl.addItems(items)
        listControl.selectItem(int(idx))
        self.setFocusId(self.C_PROGRAM_LIST)

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

        elif action in [ACTION_STOP, KEY_NAV_BACK]:
            self.action = ACTION_STOP
            self.epg.playService.stopPlayback()
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

        elif controlId == 1000:
            self.close()

    def onFocus(self, controlId):
        pass

    def close(self):
        super(Guide, self).close()

class Pla(xbmcgui.WindowXMLDialog):
    def __new__(cls, program, database, urlList, archiveService, archivePlaylist, epg):
        return super(Pla, cls).__new__(cls, 'Vid.xml', Skin.getSkinBasePath(), Skin.getSkinName(), skin_resolution)

    def __init__(self, program, database, urlList, archiveService, archivePlaylist, epg):
        # debug('Pla __init__')
        super(Pla, self).__init__()
        self.epg = epg
        self.database = database
        self.controlAndProgramList = []
        self.programs = []
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

        if PY3:
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
            self.program = self.getCurrentProgram(self.epg.currentChannel)
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

        self.programs = self.database.getNowList(self.program.channel)

        if ADDON.getSetting('info_osd') == "true":
            program, idx = self.epg.getLastPlayingChannel()

            if not program:
                program = self.program

            try:
                self.epg.setControlLabel(C_MAIN_CHAN_PLAY, '{}'.format(program.channel.title))
                self.epg.setControlLabel(C_MAIN_PROG_PLAY, '{}'.format(program.title))
                self.epg.setControlLabel(C_MAIN_TIME_PLAY, '{} - {}'.format(self.epg.formatTime(program.startDate), self.epg.formatTime(program.endDate)))
                self.epg.setControlLabel(C_MAIN_NUMB_PLAY, '{}'.format((str(int(idx) + 1))))

            except:
                self.epg.setControlLabel(C_MAIN_CHAN_PLAY, '{}'.format('N/A'))
                self.epg.setControlLabel(C_MAIN_PROG_PLAY, '{}'.format(strings(55016)))
                self.epg.setControlLabel(C_MAIN_TIME_PLAY, '{} - {}'.format('N/A', 'N/A'))
                self.epg.setControlLabel(C_MAIN_NUMB_PLAY, '{}'.format('-'))
                return

        if ADDON.getSetting('show_time') == "true":
            nowtime = '$INFO[System.Time]'

            alignLeft = 0
            alignRight = 1

            skin_resolution = config.get("Skin", "resolution")
            currentSkin = xbmc.getSkinDir()
            chkSkinKodi = currentSkin

            smallList = []
            mediumList = []
            largeList = []

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
        self.viewStartDate = datetime.datetime.today() + datetime.timedelta(minutes=int(timebarAdjust()))
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

        try:
            index = channelList[self.channelIdx]
        except:
            if channelList:
                index = channelList[0]
            else:
                return

        now = datetime.datetime.now()

        if PY3:
            start = str(datetime.datetime.timestamp(now))
        else:
            start = str(int(time.mktime(now.timetuple())))

        program = self.database.getProgramStartingAt(index, start, None)
        if not program:
            program = Program(channel=index, title='', startDate='', endDate='', description='', productionDate='', director='', actor='', episode='', 
                imageLarge='', imageSmall='', categoryA='', categoryB='')

        self.playChannel(program.channel, program)

    def onAction(self, action):
        debug('Pla onAction keyId {}, buttonCode {}'.format(action.getId(), action.getButtonCode()))

        if action.getId() == ACTION_PREVIOUS_MENU or action.getId() == ACTION_STOP or (action.getButtonCode() == KEY_STOP and KEY_STOP != 0) or (action.getId() == KEY_STOP and KEY_STOP != 0):
            self.epg.playService.stopPlayback()
            self.closeOSD()

        elif action.getId() == ACTION_LEFT and self.key_right_left_show_next == 'false':
            d = Guide(self.programs, self.database, self.program, self.epg)
            d.doModal()
            index = d.index
            action = d.action

            if action == KEY_NAV_BACK:
                return

            elif action == ACTION_STOP:
                return

            else:
                if index > -1:
                    program = self.programs[index]
                    self.epg.playChannel2(program)

        elif action.getButtonCode() == KEY_LIST and KEY_LIST != 0 or action.getId() == KEY_LIST and KEY_LIST != 0:
            program = self.program
            d = xbmcgui.Dialog()
            list = d.select(strings(30309), [strings(30315), strings(30310), strings(30311), strings(30312), strings(30336), strings(30337)])

            if list < 0:
                return
            if list == 0:
                self.epg.programSearchSelect(program.channel)
            elif list == 1:
                index = self.database.getCurrentChannelIdx(program.channel)
                programList = self.database.getChannelListing(program.channel)
                self.epg.showListing(program.channel)
            elif list == 2:
                index = self.database.getCurrentChannelIdx(program.channel)
                programList = self.database.getChannelListing(program.channel)
                self.epg.showNow(program.channel)
            elif list == 3:
                index = self.database.getCurrentChannelIdx(program.channel)
                programList = self.database.getChannelListing(program.channel)
                self.epg.showNext(program.channel)
            elif list == 4:
                self.epg.showFullReminders(program.channel)
            elif list == 5:
                self.epg.showFullRecordings(program.channel)
            return

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
                    self.program = self.getCurrentProgram(self.program.channel)
                    self.epg.Info(self.program, self.epg.playChannel2, self.epg.recordProgram, self.epg.notification, self.epg.ExtendedInfo, self.epg.onRedrawEPG, self.epg.channelIdx, self.epg.viewStartDate)
                elif list == 1:
                    self.program = self.getCurrentProgram(self.program.channel)
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
                    self.program = self.getCurrentProgram(self.program.channel)
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

        if action.getButtonCode() == KEY_SWITCH_TO_LAST:
            deb('Pla play last channel')
            channel = self.epg.getLastPreviousChannel()
            if channel:
                program = self.database.getCurrentProgram(channel)
                if program:
                    self.playChannel(channel, program)
                else:
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
                    program = self.getCurrentProgram(self.program.channel)
                d = xbmcgui.Dialog()
                list = d.select(strings(31009), [strings(58000), strings(30356)])
                if list == 0:
                    self.epg.Info(program, self.epg.playChannel2, self.epg.recordProgram, self.epg.notification, self.epg.ExtendedInfo, self.epg.onRedrawEPG, self.epg.channelIdx, self.epg.viewStartDate)
                elif list == 1:
                    self.epg.ExtendedInfo(program)
            except:
                pass
            return

        elif action == ACTION_GUIDE:
            d = Guide(self.programs, self.database, program, self.epg)
            d.doModal()
            index = d.index
            action = d.action

            if action == KEY_NAV_BACK:
                return

            elif action == ACTION_STOP:
                return

            else:
                if index > -1:
                    program = self.programs[index]
                    self.epg.playChannel2(program)

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
        while self.epg.playService.isWorking() and not self.isClosing:
            xbmc.sleep(100)

        while self.wait and not self.isClosing:
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
                if not self.isClosing and (self.ChannelChanged == 1 or self.epg.playService.isWorking()):
                    while self.epg.playService.isWorking() and not self.isClosing:
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

    def playChannel(self, channel, program=None):
        debug('Pla playChannel: {}'.format(program))
        if channel.id != self.epg.currentChannel.id:
            self.ChannelChanged = 1
            if program:
                self.program = program
                self.epg.program = program

            self.epg.updateCurrentChannel(channel, program)
            urlList = self.database.getStreamUrlList(channel)
            if len(urlList) > 0:
                self.epg.playService.playUrlList(urlList, '', '', resetReconnectCounter=True)
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

    def getCurrentProgram(self, channel=None):
        deb('getCurrentProgram: {}'.format(channel))
        if channel is not None:
            channel = channel
        else:
            channel = self.epg.currentChannel

        return self.database.getCurrentProgram(channel)


    def showVidOsd(self, action=None):
        if self.program:
            if ADDON.getSetting('archive_support') == 'true' and (self.archiveService != '' or self.archivePlaylist != ''):
                self.program = self.program
            else:
                self.program = self.getCurrentProgram(self.program.channel)
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

    def close(self):
        super(Pla, self).close()

class ProgramListDialog(xbmcgui.WindowXMLDialog):
    C_PROGRAM_LIST = 1000
    C_PROGRAM_LIST_TITLE = 1001

    def __new__(cls, title, programs, channel=None, sort_time=False):
        return super(ProgramListDialog, cls).__new__(cls, 'script-tvguide-programlist.xml', Skin.getSkinBasePath(), Skin.getSkinName(), skin_resolution)

    def __init__(self, title, programs, channel=None, sort_time=False):
        # debug('ProgramListDialog __init__')
        super(ProgramListDialog, self).__init__()
        self.title = title
        self.programs = programs
        self.channel = channel
        self.index = -1
        self.action = None
        self.sort_time = sort_time

    def onInit(self):
        xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
        control = self.getControl(ProgramListDialog.C_PROGRAM_LIST_TITLE)
        control.setLabel(self.title)

        items = []
        idxs = []

        index = 0

        for program in self.programs:
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
                se_label = ''

            label = label + se_label.replace(' E', 'E')
            name = ''

            icon = program.channel.logo
            item = xbmcgui.ListItem(label, name)

            item.setArt({'icon':icon})

            item.setProperty('index', str(index))
            if self.channel:
                if program.channel.id == self.channel.id:
                    idxs.append(index)

            index = index + 1

            item.setProperty('ChannelName', replace_formatting(program.channel.title))
            item.setProperty('Plot', replace_formatting(program.description))
            item.setProperty('startDate', str(time.mktime(program.startDate.timetuple())))

            start = program.startDate
            end = program.endDate
            duration = end - start
            now = datetime.datetime.now() + datetime.timedelta(minutes=int(timebarAdjust()))

            if now > start:
                when = datetime.timedelta(-1)
                elapsed = now - start
            else:
                when = start - now
                elapsed = datetime.timedelta(0)

            day = self.formatDateTodayTomorrow(start)
            start_str = start.strftime("%H:%M")
            start_str = "{} {} - {}".format(start_str, start.strftime("%d-%m").replace('-', '/').replace(r'^0', '').replace('/0', '/'), day)

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

        if idxs:
            idx = idxs[0]
        else:
            idx = 0

        listControl = self.getControl(ProgramListDialog.C_PROGRAM_LIST)
        listControl.addItems(items)
        listControl.selectItem(int(idx))

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
        elif action.getButtonCode() == KEY_RECORD:
            self.action = KEY_RECORD
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
            today = datetime.datetime.today() + datetime.timedelta(minutes=int(timebarAdjust()))
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