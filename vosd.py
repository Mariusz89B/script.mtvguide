#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2018 Mariusz89B
#   Copyright (C) 2013 Szakalit

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

if PY3:
    import configparser
else:
    import ConfigParser

import datetime, time, re, os, threading
import xbmc, xbmcgui, xbmcvfs
from strings import *
from skins import Skin
import source as src
from source import Program, Channel

if PY3:
    config = configparser.RawConfigParser()
else:
    config = ConfigParser.RawConfigParser()

try:
    config.read(os.path.join(Skin.getSkinPath(), 'settings.ini'))
except:
    Skin.deleteCustomSkins(show_dialog=False)
    exit()

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
    skin_separate_program_actors = config.getboolean("Skin", "program_show_actors")
except:
    skin_separate_program_actors = False
try:
    skin_separate_rating = config.getboolean("Skin", "program_show_rating")
except:
    skin_separate_rating = False
try:
    skin_resolution = config.getboolean("Skin", "resolution")
except:
    skin_resolution = '720p'

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
ACTION_SHOW_UP = 16
ACTION_SHOW_DOWN = 17

C_MAIN_CHAN_NAME = 4919
C_MAIN_TITLE = 4920
C_MAIN_TIME = 4921
C_MAIN_DESCRIPTION = 4922
C_MAIN_IMAGE = 4923
C_MAIN_CHAN_NUMBER = 4925
C_MAIN_AGE_ICON = 4932
C_MAIN_RATING = 4933
C_MAIN_START_TIME = 4950
C_MAIN_END_TIME = 4951
C_MAIN_CHAN_PLAY = 4952
C_MAIN_PROG_PLAY = 4953
C_MAIN_TIME_PLAY = 4954
C_MAIN_NUMB_PLAY = 4955
C_MAIN_CALC_TIME = 4956
C_MAIN_NEXT_PROGRAM = 4957
C_MAIN_CALC_TIME_LEFT = 4958
C_MAIN_CALC_TIME_PASS = 4959
C_MAIN_DAY = 4960
C_MAIN_DATE = 4961
C_MAIN_EPISODE = 4962
C_STOP = 101
C_SHOW_INFO = 102
C_PAGE_DOWN = 103
C_PAGE_UP = 104
C_PLAY = 105
C_SETUP = 106
C_SCHEDULE = 107
C_UNSCHEDULE = 108
C_SUBS = 109
C_LANG = 110
C_ACTION_RIGHT = 111
C_ACTION_BACK = 112
C_ACTION_DESC = 118
C_ACTION_NUMBER = 113
C_PAUSE = 114
C_CLOSE_WINDOW = 1000
C_VIDEO_OSD_WINDOW = 100

ACTION_MOUSE_WHEEL_UP = 104
ACTION_MOUSE_WHEEL_DOWN = 105
ACTION_MOUSE_MOVE = 107

KEY_NAV_BACK = 92
KEY_CONTEXT_MENU = 117
KEY_HOME = 159
AUTO_OSD = 666

try:
     KEY_STOP = int(ADDON.getSetting('stop_key'))
except:
     KEY_STOP = -1
try:
     KEY_CONTEXT = int(ADDON.getSetting('context_key'))
except:
     KEY_CONTEXT = -1
try:
     KEY_INFO = int(ADDON.getSetting('info_key'))
except:
     KEY_INFO = -1
try:
     KEY_SWITCH_TO_LAST = int(ADDON.getSetting('switch_to_last_key'))
except:
     KEY_SWITCH_TO_LAST = -1
try:
     KEY_PP = int(ADDON.getSetting('pp_key'))
except:
     KEY_PP = 0
try:
     KEY_PM = int(ADDON.getSetting('pm_key'))
except:
     KEY_PM = 0
try:
    KEY_LIST = int(ADDON.getSetting('list_key'))
except:
    KEY_LIST = -1

class proxydt(datetime.datetime):
    @staticmethod
    def strptime(date_string, format):
        import time
        return datetime.datetime(*(time.strptime(date_string, format)[0:6]))

datetime.proxydt = proxydt

class VideoOSD(xbmcgui.WindowXMLDialog):
    def __new__(cls, gu, controlledByMouse = True, action = None):
        return super(VideoOSD, cls).__new__(cls, 'VidOSD.xml', Skin.getSkinBasePath(), Skin.getSkinName(), skin_resolution)

    def __init__(self, gu, controlledByMouse = True, action = None):
        self.gu = gu
        self.playService = self.gu.epg.playService
        self.isClosing = False
        self.extVideoOsd = ADDON.setSetting('vosd.arg', 'false')
        self.mouseCount = 0
        self.program = self.gu.program
        self.controlledByMouse = controlledByMouse
        self.keyRightLeftChangeProgram = False
        self.showConfigButtons = False
        self.initialized = False
        self.osdDisplayTime = int(ADDON.getSetting('osd_time'))
        self.blockOsd = False
        self.channelIdx = 0
        self.timer = None
        self.channel_number_input = False
        self.channel_number = ADDON.getSetting('channel.arg')
        self.keyboardTime = None
        self.mousetime = None
        if ADDON.getSetting('show_osd_buttons') == 'true':
            self.showConfigButtons = True
        if not self.showConfigButtons and ADDON.getSetting('key_right_left_show_next') == 'true':
            self.keyRightLeftChangeProgram = True

        if action is not None:
            if action == ACTION_UP:
                self.program = self.gu.getProgramDown(self.program)
            elif action == ACTION_DOWN:
                self.program = self.gu.getProgramUp(self.program)
            elif action == ACTION_LEFT:
                self.showPreviousProgram()
            elif action == ACTION_RIGHT:
                self.showNextProgram()
            elif action == AUTO_OSD:
                self.osdDisplayTime = int(ADDON.getSetting('osd_on_play_time'))
            if not self.program:
                self.program = self.gu.getCurrentProgram()

        super(VideoOSD, self).__init__()

    def onInit(self):
        if not self.controlledByMouse:
            closeWindowControl = self.getControl(C_CLOSE_WINDOW)
            closeWindowControl.setVisible(False)
            closeWindowControl.setEnabled(False)
            threading.Timer(1, self.waitForKeyboard).start()
        else:
            threading.Timer(1, self.waitForMouse).start()

        self.playControl = self.getControl(C_PLAY)
        self.pausePlaybackControl = self.getControl(C_PAUSE)
        self.stopPlaybackControl = self.getControl(C_STOP)
        self.pageUpControl = self.getControl(C_PAGE_UP)
        self.pageDownControl = self.getControl(C_PAGE_DOWN)
        self.infoControl = self.getControl(C_SHOW_INFO)
        self.setupControl = self.getControl(C_SETUP)
        self.nextSubtitle = self.getControl(C_SUBS)
        self.audioNextLanguage = self.getControl(C_LANG)
        self.scheduleControl = self.getControl(C_SCHEDULE)
        self.unscheduleControl = self.getControl(C_UNSCHEDULE)
        self.videoOsdWindowControl = self.getControl(C_VIDEO_OSD_WINDOW)
        self.actionback = self.getControl(C_ACTION_BACK)
        self.actionright = self.getControl(C_ACTION_RIGHT)
        self.actionnumber = self.getControl(C_ACTION_NUMBER)
        self.actiondesc = self.getControl(C_ACTION_DESC)

        if self.showConfigButtons:
            self.pausePlaybackControl.controlRight(self.infoControl)
            self.infoControl.controlLeft(self.pausePlaybackControl)
            self.infoControl.controlRight(self.setupControl)
            self.setupControl.controlLeft(self.infoControl)
            self.setupControl.controlRight(self.nextSubtitle)
            self.pageDownControl.controlLeft(self.actionright)
            self.pageDownControl.controlRight(self.pageUpControl)
            self.pageUpControl.controlLeft(self.pageDownControl)
            self.stopPlaybackControl.controlLeft(self.pageUpControl)
            self.stopPlaybackControl.controlRight(self.pausePlaybackControl)
            self.playControl.controlRight(self.pausePlaybackControl)
            self.playControl.controlLeft(self.pageUpControl)
            self.scheduleControl.controlRight(self.pausePlaybackControl)
            self.scheduleControl.controlLeft(self.pageUpControl)
            self.unscheduleControl.controlRight(self.pausePlaybackControl)
            self.unscheduleControl.controlLeft(self.pageUpControl)
            self.nextSubtitle.controlLeft(self.setupControl)
            self.nextSubtitle.controlRight(self.audioNextLanguage)
            self.audioNextLanguage.controlLeft(self.nextSubtitle)
            self.audioNextLanguage.controlRight(self.actionnumber)
            self.actionnumber.controlLeft(self.audioNextLanguage)
            self.actionnumber.controlRight(self.actionback)
            self.actionback.controlLeft(self.actionnumber)
            self.actionback.controlRight(self.actionright)
            self.actionright.controlLeft(self.actionback)
            self.actionright.controlRight(self.pageDownControl)
        else:
            self.pageUpControl.setVisible(False)
            self.pageDownControl.setVisible(False)
            self.pausePlaybackControl.setVisible(False)
            self.infoControl.setVisible(False)
            self.setupControl.setVisible(False)
            self.nextSubtitle.setVisible(False)
            self.audioNextLanguage.setVisible(False)
            self.actionnumber.setVisible(False)

            self.pageUpControl.setEnabled(False)
            self.pageDownControl.setEnabled(False)
            self.pausePlaybackControl.setEnabled(False)
            self.infoControl.setEnabled(False)
            self.setupControl.setEnabled(False)
            self.nextSubtitle.setEnabled(False)
            self.audioNextLanguage.setEnabled(False)
            self.actionnumber.setEnabled(False)
            self.unscheduleControl.setVisible(True)
            self.unscheduleControl.setEnabled(True)
            if self.keyRightLeftChangeProgram:
                self.actiondesc.setVisible(True)
                self.actiondesc.setEnabled(True)
                self.actionback.setVisible(True)
                self.actionright.setVisible(True)
                self.actionback.setEnabled(True)
                self.actionright.setEnabled(True)
            else:
                self.actiondesc.setVisible(False)
                self.actiondesc.setEnabled(False)
                self.actionback.setVisible(False)
                self.actionright.setVisible(False)
                self.actionback.setEnabled(False)
                self.actionright.setEnabled(False)

        self.playControl.setVisible(False)
        self.stopPlaybackControl.setVisible(False)
        self.scheduleControl.setVisible(False)
        if self.keyRightLeftChangeProgram:
            self.actionback.setVisible(True)
            self.actionright.setVisible(True)
        self.stopPlaybackControl.setEnabled(False)
        self.playControl.setEnabled(True)
        self.scheduleControl.setEnabled(False)
        self.unscheduleControl.setVisible(False)
        self.unscheduleControl.setEnabled(False)

        self.actionright.controlLeft(self.actiondesc)
        self.actionback.controlRight(self.actiondesc)
        self.actiondesc.controlLeft(self.actionback)
        self.actiondesc.controlRight(self.actionright)

        self.ctrlServiceName    = self.getControl(C_MAIN_SERVICE_NAME)
        self.ctrlChanName       = self.getControl(C_MAIN_CHAN_NAME)
        self.ctrlChanNamePlay       = self.getControl(C_MAIN_CHAN_PLAY)
        self.ctrlProgNamePlay       = self.getControl(C_MAIN_PROG_PLAY)
        self.ctrlMainTitle      = self.getControl(C_MAIN_TITLE)
        self.ctrlProgramTitle   = self.getControl(C_MAIN_TITLE)
        self.ctrlProgramTime    = self.getControl(C_MAIN_TIME)
        self.ctrlProgramTimePlay    = self.getControl(C_MAIN_TIME_PLAY)
        self.ctrlStartProgramTime    = self.getControl(C_MAIN_START_TIME)
        self.ctrlEndProgramTime    = self.getControl(C_MAIN_END_TIME)
        self.ctrlCalcProgramTime    = self.getControl(C_MAIN_CALC_TIME)
        self.ctrlCalcProgramTimeLeft    = self.getControl(C_MAIN_CALC_TIME_LEFT)
        self.ctrlCalcProgramTimeNext    = self.getControl(C_MAIN_CALC_TIME_PASS)
        self.ctrlNextProgram    = self.getControl(C_MAIN_NEXT_PROGRAM)
        self.ctrlProgramDesc    = self.getControl(C_MAIN_DESCRIPTION)
        self.ctrlProgramLogo    = self.getControl(C_MAIN_LOGO)
        self.ctrlProgramImg     = self.getControl(C_MAIN_IMAGE)
        self.ctrlMainLive       = self.getControl(C_MAIN_LIVE)
        self.ctrlProgramSlider = self.getControl(C_PROGRAM_SLIDER)
        self.ctrlProgramProgress = self.getControl(C_PROGRAM_PROGRESS)
        self.ctrlChanNumber     = self.getControl(C_MAIN_CHAN_NUMBER)
        self.ctrlChanNumberPlay    = self.getControl(C_MAIN_NUMB_PLAY)
        self.ctrlWeekDay        = self.getControl(C_MAIN_DAY)
        self.ctrlDate          = self.getControl(C_MAIN_DATE)
        self.ctrlEpisode       = self.getControl(C_MAIN_EPISODE)

        self.mousetime = time.mktime(datetime.datetime.now().timetuple())
        self.keyboardTime = time.mktime(datetime.datetime.now().timetuple())
        threading.Timer(1, self.waitForPlayBackStopped).start()

        self.initialized = True
        self.refreshControls()

    def setControlVisibility(self):
        currentlyPlayedProgram = self.gu.getCurrentProgram()
        timeDiff = self.program.startDate - datetime.datetime.now()
        secToStartProg = (timeDiff.days * 86400) + timeDiff.seconds

        self.playControl.setVisible(False)
        self.stopPlaybackControl.setVisible(False)
        self.scheduleControl.setVisible(False)
        self.unscheduleControl.setVisible(False)
        self.playControl.setEnabled(False)
        self.stopPlaybackControl.setEnabled(False)
        self.scheduleControl.setEnabled(False)
        self.unscheduleControl.setEnabled(False)

        if secToStartProg > 0:
            #Future program, not started yet
            if ADDON.getSetting('program_notifications_enabled') == 'true':
                if not self.gu.epg.notification.isScheduled(self.program):
                    self.scheduleControl.setVisible(True)
                    self.scheduleControl.setEnabled(True)
                    self.pausePlaybackControl.controlLeft(self.scheduleControl)
                    self.pageUpControl.controlRight(self.scheduleControl)
                    self.setFocusIfNeeded(C_SCHEDULE)
                else:
                    self.pausePlaybackControl.controlLeft(self.unscheduleControl)
                    self.pageUpControl.controlRight(self.unscheduleControl)
                    self.unscheduleControl.setVisible(True)
                    self.unscheduleControl.setEnabled(True)
                    self.setFocusIfNeeded(C_UNSCHEDULE)
            else:
                self.pausePlaybackControl.controlLeft(self.pageUpControl)
                self.pageUpControl.controlRight(self.pausePlaybackControl)
                self.setFocusIfNeeded(C_PLAY)

        elif not self.controlledByMouse and not (currentlyPlayedProgram.channel.id == self.program.channel.id):
            #Program executed on different channel than currently is on, False if mouse controlled
            self.playControl.setEnabled(True)
            self.playControl.setVisible(True)
            self.pausePlaybackControl.controlLeft(self.playControl)
            self.pageUpControl.controlRight(self.playControl)
            self.setFocusIfNeeded(C_PLAY)

        elif currentlyPlayedProgram.startDate == self.program.startDate:
            self.stopPlaybackControl.setEnabled(True)
            self.stopPlaybackControl.setVisible(True)
            self.pausePlaybackControl.controlLeft(self.stopPlaybackControl)
            self.pageUpControl.controlRight(self.stopPlaybackControl)
            self.setFocusIfNeeded(C_STOP)
            
        elif self.controlledByMouse or self.showConfigButtons:
            self.stopPlaybackControl.setEnabled(True)
            self.stopPlaybackControl.setVisible(True)
            self.pausePlaybackControl.controlLeft(self.stopPlaybackControl)
            self.pageUpControl.controlRight(self.stopPlaybackControl)
            self.setFocusIfNeeded(C_STOP)

    def setFocusIfNeeded(self, controlId):
        if self.controlledByMouse:
            return
        try:
            currFocus = self.getFocus()
            currFocusVisible = xbmc.getCondVisibility("Control.IsVisible(%s)" % currFocus.getId())
            if not currFocusVisible or currFocus.getId() == controlId:
                self.setFocusId(controlId)
        except:
            self.setFocusId(controlId)

    def playShortcut(self):
        self.channel_number_input = False
        self.viewStartDate = datetime.datetime.today() + datetime.timedelta(minutes=int(self.timebarAdjust()))
        self.viewStartDate -= datetime.timedelta(minutes=self.viewStartDate.minute % 30,
                                                 seconds=self.viewStartDate.second)
        channelList = self.gu.database.getChannelList(onlyVisible=True)
        if ADDON.getSetting('channel_shortcut') == 'false':
            for i in range(len(channelList)):
                if self.channel_number == channelList[i].id:
                     self.channelIdx = i
                     break
        else:
            self.channelIdx = (int(self.channel_number) -1)
            self.channel_number = ""
            self.getControl(9999).setLabel(self.channel_number)

        channel = Channel(id='', title='', logo='', titles='', streamUrl='', visible='', weight='')
        try:
            index = channelList[self.channelIdx]
        except:
            index = channelList[0]
        program = Program(channel=index, title='', startDate='', endDate='', description='', imageLarge='', imageSmall='', categoryA='',categoryB='')
        self.gu.playChannel(program.channel, program)
        self.isClosing = True

    def onAction(self, action):
        debug('VideoOSD onAction keyId %d, buttonCode %d' % (action.getId(), action.getButtonCode()))
        self.keyboardTime = time.mktime(datetime.datetime.now().timetuple())

        if action.getId() in [ACTION_PREVIOUS_MENU, KEY_NAV_BACK, ACTION_PARENT_DIR, 101]:
            self.isClosing = True

        if action.getId() in [ACTION_STOP] or action.getButtonCode() == KEY_STOP:
            self.isClosing = True
            self.playService.stopPlayback()

        elif action.getId() == ACTION_MOUSE_MOVE:
            self.mouseCount = self.mouseCount + 1
            if self.mouseCount > 2:
                self.mouseCount =  0
                self.mousetime = time.mktime(datetime.datetime.now().timetuple())
                #self.refreshControls()

        elif action.getId() == KEY_CONTEXT_MENU or action.getButtonCode() == KEY_CONTEXT:
            self.isClosing = True
            self.gu.changeStream()

        elif self.controlledByMouse:
            return #remaining are for keyboard

        elif (action.getId() == ACTION_UP):
            self.program = self.gu.getProgramDown(self.program)
            self.refreshControls()

        elif (action.getId() == ACTION_DOWN):
            self.program = self.gu.getProgramUp(self.program)
            self.refreshControls()

        elif (action.getId() == ACTION_LEFT) and self.keyRightLeftChangeProgram:
            if not self.showConfigButtons:
                self.showPreviousProgram()

        elif (action.getId() == ACTION_RIGHT) and self.keyRightLeftChangeProgram:
            if not self.showConfigButtons:
                self.showNextProgram()

        elif (action.getId() == ACTION_SELECT_ITEM):
            currentlyPlayedProgram = self.gu.getCurrentProgram()
            if not self.showConfigButtons and currentlyPlayedProgram.channel.id == self.program.channel.id and currentlyPlayedProgram.startDate == self.program.startDate:
                self.isClosing = True

        elif action.getId() == ACTION_SHOW_INFO or action.getButtonCode() == KEY_INFO or action.getId() == KEY_INFO:
            try:
                self.blockOsd = True
                self.videoOsdWindowControl.setVisible(False)
                d = xbmcgui.Dialog()
                list = d.select(strings(31009), [strings(58000), strings(30356)])

                if list == 0:
                    self.gu.epg.Info(self.program, self.gu.epg.playChannel2, self.gu.epg.recordProgram, self.gu.epg.notification, self.gu.epg.ExtendedInfo, self.gu.epg.onRedrawEPG, self.gu.epg.channelIdx, self.gu.epg.viewStartDate)
                elif list == 1:
                    self.gu.epg.ExtendedInfo(self.program)
            except:
                pass
            self.keyboardTime = time.mktime(datetime.datetime.now().timetuple())
            self.videoOsdWindowControl.setVisible(True)
            self.blockOsd = False

        elif action.getButtonCode() == KEY_LIST:
            program = self.program
            d = xbmcgui.Dialog()
            list = d.select(strings(30309), [strings(30315), strings(30310), strings(30311), strings(30312), strings(30336), strings(30337)])

            if list < 0:
                return
            if list == 0:
                self.gu.epg.programSearchSelect(program.channel)
            elif list == 1:
                index = self.gu.database.getCurrentChannelIdx(program.channel)
                programList = self.gu.database.getChannelListing(program.channel)
                self.gu.epg.showListing(program.channel)
            elif list == 2:
                index = self.gu.database.getCurrentChannelIdx(program.channel)
                programList = self.gu.database.getChannelListing(program.channel)
                self.gu.epg.showNow(program.channel)
            elif list == 3:
                index = self.gu.database.getCurrentChannelIdx(program.channel)
                programList = self.gu.database.getChannelListing(program.channel)
                self.gu.epg.showNext(program.channel)
            elif list == 4:
                self.gu.epg.showFullReminders(program.channel)
            elif list == 5:
                self.gu.epg.showFullRecordings(program.channel)
            return

        elif action.getButtonCode() == KEY_SWITCH_TO_LAST:
            self.isClosing = True
            self.gu.onAction(action)

        elif action.getId() == ACTION_PAGE_UP or (action.getButtonCode() == KEY_PP and KEY_PP != 0) or (action.getId() == KEY_PP and KEY_PP != 0):
            self.program = self.gu.getProgramDown(self.program)
            self.refreshControls()
            xbmc.executebuiltin('Action(Select)')

        elif action.getId() == ACTION_PAGE_DOWN or (action.getButtonCode() == KEY_PM and KEY_PM != 0) or (action.getId() == KEY_PM and KEY_PM != 0):
            self.program = self.gu.getProgramUp(self.program)
            self.refreshControls()
            xbmc.executebuiltin('Action(Select)')

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
                        self.channel_number = "%s%d" % (self.channel_number.strip('_'),digit)
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
                    xbmcgui.Dialog().notification(strings(30353).encode('UTF-8'), strings(30354).encode('UTF-8'))
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
                        xbmcgui.Dialog().notification(strings(30353).encode('UTF-8'), strings(30354).encode('UTF-8'))
                        return

    def showNextProgram(self):
        program = self.gu.getProgramRight(self.program)
        if program is not None:
            self.program = program
            self.refreshControls()

    def showPreviousProgram(self):
        program = self.gu.getProgramLeft(self.program)
        if program is not None:
            timeDiff = program.endDate - datetime.datetime.now()
            diffSec = (timeDiff.days * 86400) + timeDiff.seconds
            if diffSec > 0:
                self.program = program
                self.refreshControls()

    def showNextChannel(self):
        program = self.gu.getProgramDown(self.program)
        if program is not None:
            self.program = program
            self.refreshControls()

    def showPreviousChannel(self):
        program = self.gu.getProgramUp(self.program)
        if program is not None:
            self.program = program
            self.refreshControls()

    def onClick(self, controlId):
        self.keyboardTime = time.mktime(datetime.datetime.now().timetuple())

        if controlId == 1000:
            self.isClosing = True
        elif controlId == C_STOP:
            self.isClosing = True
            self.gu.onAction2(ACTION_STOP)
        elif controlId == C_PLAY:
            self.isClosing = True
            self.gu.playChannel(self.program.channel, self.program)
        elif controlId == C_PAUSE:
            self.isClosing = False
            xbmc.executebuiltin('Action(PlayPause)')
        elif controlId == C_SHOW_INFO:
            self.isClosing = False
            self.gu.onAction2(ACTION_SHOW_INFO, self.program)
        elif controlId == C_SETUP:
            self.isClosing = True
            xbmc.executebuiltin('ActivateWindow(videoosd)')
            self.extVideoOsd = ADDON.setSetting('vosd.arg', 'true') 
        elif controlId == C_SUBS:
            self.isClosing = False
            xbmc.executebuiltin('Action(NextSubtitle)')
        elif controlId == C_LANG:
            self.isClosing = False
            xbmc.executebuiltin('Action(AudioNextLanguage)')
        elif controlId == C_ACTION_BACK:
            self.isClosing = False
            self.showPreviousProgram()
        elif controlId == C_ACTION_RIGHT:
            self.isClosing = False
            self.showNextProgram()
        elif controlId == C_ACTION_NUMBER:
            if ADDON.getSetting('channel_shortcut') == 'false':
                xbmcgui.Dialog().notification(strings(30353).encode('UTF-8'), strings(30354).encode('UTF-8'))
            else:
                if ADDON.getSetting('channel_shortcut') == 'true':
                    d = xbmcgui.Dialog()
                    number = d.input(strings(30346),type=xbmcgui.INPUT_NUMERIC)
                    if number:
                        self.channel_number = number
                        if self.timer and self.timer.is_alive():
                            self.timer.cancel()
                        self.playShortcut()
        else:
            if self.controlledByMouse:
                self.onClickMouse(controlId)
            else:
                self.onClickKeyboard(controlId)

    def onClickMouse(self, controlId):
        if controlId == C_PAGE_DOWN:
            self.isClosing = True
            self.gu.onAction2(ACTION_PAGE_DOWN)
        elif controlId == C_PAGE_UP:
            self.isClosing = True
            self.gu.onAction2(ACTION_PAGE_UP)

    def onClickKeyboard(self, controlId):
        if controlId == C_PAGE_DOWN:
            #self.showPreviousProgram()
            self.showPreviousChannel()
            self.setFocusId(C_PAGE_DOWN)
        elif controlId == C_PAGE_UP:
            #self.showNextProgram()
            self.showNextChannel()
            self.setFocusId(C_PAGE_UP)
        elif controlId == C_SCHEDULE:
            if self.gu.epg.notification:
                self.gu.epg.notification.addNotification(self.program, onlyOnce = True)
                self.refreshControls()
        elif controlId == C_UNSCHEDULE:
            if self.gu.epg.notification:
                self.gu.epg.notification.removeNotification(self.program)
                self.refreshControls()

    def refreshControls(self):
        if not self.initialized:
            return

        if self.program.title is None or self.program.title == '':
            self.program = self.gu.database.getCurrentProgram(self.program.channel)

        if self.ctrlServiceName is not None and ADDON.getSetting('show_service_name') == 'true':
            self.ctrlServiceName.setLabel('%s' % self.playService.getCurrentServiceString())
        if self.ctrlChanName is not None:
            self.ctrlChanName.setLabel('%s' % (self.program.channel.title))
        if self.ctrlChanNamePlay is not None:
            self.ctrlChanNamePlay.setLabel('%s' % (self.program.channel.title))
        if self.ctrlProgNamePlay is not None:
            self.ctrlProgNamePlay.setLabel('%s' % (self.program.title))
        if self.ctrlMainTitle is not None:
            self.ctrlMainTitle.setLabel('%s' % (self.program.title))
        if self.ctrlProgramTime is not None:
            self.ctrlProgramTime.setLabel('%s - %s' % (self.formatTime(self.program.startDate), self.formatTime(self.program.endDate)))
        if self.ctrlProgramTimePlay is not None:
            self.ctrlProgramTimePlay.setLabel('%s - %s' % (self.formatTime(self.program.startDate), self.formatTime(self.program.endDate)))
        if self.ctrlStartProgramTime is not None:
            self.ctrlStartProgramTime.setLabel('%s' % (self.formatTime(self.program.startDate)))
        if self.ctrlEndProgramTime is not None:
            self.ctrlEndProgramTime.setLabel('%s' % (self.formatTime(self.program.endDate)))
        if self.ctrlEpisode is not None:
            self.ctrlEpisode.setLabel('%s' % (self.program.episode))

        if self.ctrlWeekDay is not None:
            startDate = str(self.program.startDate)
            try:
                now = datetime.proxydt.strptime(startDate, '%Y-%m-%d %H:%M:%S')
            except:
                now = datetime.proxydt.strptime(startDate, '%Y-%m-%d %H:%M:%S.%f')
                
            try:
                nowDay = now.strftime("%a").replace('Mon', strings(70109)).replace('Tue', strings(70110)).replace('Wed', strings(70111)).replace('Thu', strings(70112)).replace('Fri', strings(70113)).replace('Sat', strings(70114)).replace('Sun', strings(70115))
            except:
                nowDay = now.strftime("%a").replace('Mon', strings(70109).encode('UTF-8')).replace('Tue', strings(70110).encode('UTF-8')).replace('Wed', strings(70111).encode('UTF-8')).replace('Thu', strings(70112).encode('UTF-8')).replace('Fri', strings(70113).encode('UTF-8')).replace('Sat', strings(70114).encode('UTF-8')).replace('Sun', strings(70115).encode('UTF-8'))
            
            self.ctrlWeekDay.setLabel('%s' % (nowDay))

        if self.ctrlDate is not None:
            startDate = str(self.program.startDate)
            try:
                now = datetime.proxydt.strptime(startDate, '%Y-%m-%d %H:%M:%S')
            except:
                now = datetime.proxydt.strptime(startDate, '%Y-%m-%d %H:%M:%S.%f')
            nowDate = now.strftime("%d-%m-%Y")
            self.ctrlDate.setLabel('%s' % (nowDate))

        if self.ctrlCalcProgramTime is not None:
            start_date = datetime.datetime.now() - self.program.startDate
            end_date = datetime.datetime.now() - self.program.endDate
            self.ctrlCalcProgramTime.setLabel('%s' % (start_date - end_date))

        if self.ctrlCalcProgramTimeLeft is not None:
            if self.program.endDate < datetime.datetime.now():
                start_date = time.mktime(self.program.startDate.timetuple()) - 60 * float(self.timebarAdjust())
                end_date = time.mktime(self.program.endDate.timetuple()) - 60 * float(self.timebarAdjust())
                result = (end_date - start_date)
                dt_obj = datetime.datetime.utcfromtimestamp(result)
                rt_obj = dt_obj.strftime('%H:%M')
                rt_obj = self.formatMinutes(rt_obj)
                self.ctrlCalcProgramTimeLeft.setLabel('%s' % (rt_obj))
            else:
                now_date = time.mktime(datetime.datetime.now().timetuple())
                end_date = time.mktime(self.program.endDate.timetuple()) - 60 * float(self.timebarAdjust())
                result = (end_date - now_date + float(60))
                dt_obj = datetime.datetime.utcfromtimestamp(result)
                rt_obj = dt_obj.strftime('%H:%M')
                rt_obj = self.formatMinutes(rt_obj)
                self.ctrlCalcProgramTimeLeft.setLabel('%s' % (rt_obj))

        if self.ctrlCalcProgramTimeNext is not None:
            try:
                programs = self.gu.database.getNextProgram(self.program)
                for program in [programs]:
                    if program is None:
                        startDate = self.program.startDate
                        endDate = self.program.endDate
                    else:
                        startDate = program.startDate
                        endDate = program.endDate

                    start_date = time.mktime(startDate.timetuple())
                    end_date = time.mktime(endDate.timetuple()) - 60 * float(self.timebarAdjust())
                    result = (end_date - start_date)
                    dt_obj = datetime.datetime.utcfromtimestamp(result)
                    rt_obj = dt_obj.strftime('%H:%M')
                    rt_obj = self.formatMinutes(rt_obj)

                self.ctrlCalcProgramTimeNext.setLabel('%s' % (rt_obj))
            except:
                self.ctrlCalcProgramTimeNext.setLabel('%s' % ('N/A'))

        if self.ctrlNextProgram is not None:
            programs = self.gu.database.getNextProgram(self.program)
            for program in [programs]:
                if program is None:
                    title = self.program.title
                else:
                    title = program.title

                self.ctrlNextProgram.setLabel('%s' % (title))

        if self.ctrlProgramDesc is not None:
            if self.program.description and self.ctrlProgramDesc:
                descriptionParser = src.ProgramDescriptionParser(self.program.description)
                if skin_separate_category:
                    category = descriptionParser.extractCategory()
                    if category == '':
                        category = self.program.categoryA
                        if category == '':
                            category = strings(NO_CATEGORY)
                if skin_separate_year_of_production:
                    year = descriptionParser.extractProductionDate()
                    if year == '':
                        year = self.program.productionDate
                if skin_separate_director:
                    director = descriptionParser.extractDirector()
                    if director == '':
                        director = self.program.director
                if skin_separate_episode:
                    episode = descriptionParser.extractEpisode()
                    if episode == '':
                        episode = self.program.episode
                if skin_separate_allowed_age_icon:
                    icon, age = descriptionParser.extractAllowedAge()
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
                    self.setControlImage(C_MAIN_AGE_ICON, icon)
                if skin_separate_program_actors:
                    actors = descriptionParser.extractActors()
                    if actors == '':
                        actors = self.program.actor
                if skin_separate_rating:
                    rating = descriptionParser.extractRating()
                    if rating == '':
                        rating = self.program.rating
                    self.setControlText(C_MAIN_RATING, rating)
                
                description = descriptionParser.description
                self.setControlText(C_MAIN_DESCRIPTION, description)
            else:
                self.ctrlProgramDesc.setText(strings(NO_DESCRIPTION))

        if self.program.channel.logo and self.ctrlProgramLogo:
            self.ctrlProgramLogo.setImage(self.program.channel.logo)

        if self.program.imageSmall is not None and self.ctrlProgramImg:
            self.ctrlProgramImg.setImage(self.program.imageSmall)
        else:
            if self.ctrlProgramImg is not None:
                self.ctrlProgramImg.setImage('tvguide-logo-epg.png')

        if self.program.imageLarge == 'live' and self.ctrlMainLive:
            self.ctrlMainLive.setImage('live.png')
        else:
            if self.ctrlMainLive is not None:
                self.ctrlMainLive.setImage('')

        if self.ctrlProgramSlider:
            self.stdat = time.mktime(self.program.startDate.timetuple())
            self.endat = time.mktime(self.program.endDate.timetuple())
            self.nodat = time.mktime(datetime.datetime.now().timetuple()) + 60 * float(self.timebarAdjust())
            try:
                self.per =  100 -  ((self.endat - self.nodat)/ ((self.endat - self.stdat)/100))
            except:
                self.per = 0
            if self.per > 0 and self.per < 100:
                self.ctrlProgramSlider.setVisible(True)
                self.ctrlProgramSlider.setPercent(self.per)
            else:
                self.ctrlProgramSlider.setVisible(False)

        if self.ctrlProgramProgress:
            self.stdat = time.mktime(self.program.startDate.timetuple())
            self.endat = time.mktime(self.program.endDate.timetuple())
            self.nodat = time.mktime(datetime.datetime.now().timetuple()) + 60 * float(self.timebarAdjust())
            try:
                self.per =  100 -  ((self.endat - self.nodat)/ ((self.endat - self.stdat)/100))
            except:
                self.per = 0
            if self.per > 0 and self.per < 100:
                self.ctrlProgramProgress.setVisible(True)
                self.ctrlProgramProgress.setPercent(self.per)
            else:
                self.ctrlProgramProgress.setVisible(False)

        if (ADDON.getSetting('channel_shortcut') != 'false'):
            if self.ctrlChanNumber is not None:
               self.ctrlChanNumber.setLabel('%s' % (self.gu.database.getCurrentChannelIdx(self.program.channel) + 1))
            if self.ctrlChanNumberPlay is not None:
               self.ctrlChanNumberPlay.setLabel('%s' % (self.gu.database.getCurrentChannelIdx(self.program.channel) + 1))

        self.setControlVisibility()

    def getControl(self, controlId):
        try:
            return super(VideoOSD, self).getControl(controlId)
        except:
            pass
        return None

    def onPlayBackStopped(self):
        self.close()

    def waitForPlayBackStopped(self):
        while xbmc.Player().isPlaying() and not self.isClosing:
            time.sleep(0.1)
        self.onPlayBackStopped()

    def waitForMouse(self):
        if self.mousetime is None:
            self.mousetime = time.mktime(datetime.datetime.now().timetuple())

        while time.mktime(datetime.datetime.now().timetuple()) < self.mousetime + self.osdDisplayTime and not self.isClosing:
            time.sleep(0.1)
        self.isClosing = True

    def waitForKeyboard(self):
        if self.keyboardTime is None:
            self.keyboardTime = time.mktime(datetime.datetime.now().timetuple())

        while (time.mktime(datetime.datetime.now().timetuple()) < self.keyboardTime + self.osdDisplayTime or self.blockOsd) and not self.isClosing:
            time.sleep(0.1)
        self.isClosing = True

    def timebarAdjust(self):
        timebar_adjust = ADDON.getSetting('timebar_adjust')
        if timebar_adjust == '':
            timebar_adjust = 0
        return timebar_adjust

    def formatMinutes(self, rt_obj):
        rt_obj = re.sub(r'^0', '', rt_obj)
        rt_obj = re.sub('0:0', '', rt_obj)
        rt_obj = re.sub('0:', '', rt_obj)
        rt_obj = re.sub(':', 'h ', rt_obj)
        rt_obj = re.sub(r'$', r' min', rt_obj)

        return rt_obj

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

    def close(self):
        if self.timer and self.timer.is_alive():
            self.timer.cancel()
        super(VideoOSD, self).close()