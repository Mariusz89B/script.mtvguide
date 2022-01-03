#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2016 Andrzej Mleczko
#   Copyright (C) 2012 Tommy Winther

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

#from __future__ import unicode_literals

import sys

import datetime
import os
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, xbmcvfs
import source as src
import threading
from strings import *

class Notification(object):
    def __init__(self, database, addonPath, epg):
        """
        @param database: source.Database
        """
        self.database = database
        self.addonPath = addonPath
        self.icon = os.path.join(self.addonPath, 'icon.png')
        self.epg = epg
        self.channels = list()
        self.timers = list()

    def createAlarmClockName(self, programTitle, startTime):
        return 'mtvguide-%s-%s' % (programTitle, startTime)

    def scheduleNotifications(self):
        deb("[{}] Scheduling notifications".format(ADDON_ID))
        self.close()  #cleanup
        self.channels = self.database.getChannelList(True)
        for channelTitle, programTitle, startTime in self.database.getNotifications():
            self._scheduleNotification(channelTitle, programTitle, startTime)
        debug('Scheduling notification completed!')

    def _scheduleNotification(self, channelTitle, programTitle, startTime):
        if sys.version_info[0] > 2:
            debug('Notification _scheduleNotification program: {}, startTime {}'.format(programTitle, startTime))
        else:
            debug('Notification _scheduleNotification program: {}, startTime {}'.format(programTitle.encode('utf-8'), startTime))
        t = startTime - datetime.datetime.now()
        secToNotification  = (t.days * 86400) + t.seconds
        timeToNotification = secToNotification // 60
        if timeToNotification < 0:
            return

        name = self.createAlarmClockName(programTitle, startTime)

        description = strings(NOTIFICATION_5_MINS, channelTitle)
        if sys.version_info[0] > 2:
            xbmc.executebuiltin('CancelAlarm({}-5mins,True)'.format(name))
            xbmc.executebuiltin('AlarmClock({}-5mins,Notification({},{},10000,{}),{},True)'.format(name, programTitle, description, self.icon, timeToNotification - 5))

        else:
            xbmc.executebuiltin('CancelAlarm({}-5mins,True)'.format(name.encode('utf-8', 'replace')))
            xbmc.executebuiltin('AlarmClock({}-5mins,Notification({},{},10000,{}),{},True)'.format(name.encode('utf-8', 'replace'), programTitle.encode('utf-8', 'replace'), description.encode('utf-8', 'replace'), self.icon, timeToNotification - 5))


        description = strings(NOTIFICATION_NOW, channelTitle)
        if sys.version_info[0] > 2:
            xbmc.executebuiltin('CancelAlarm({}-now,True)'.format(name))
            xbmc.executebuiltin('AlarmClock({}-now,Notification({},{},10000,{}),{},True)'.format(name, programTitle, description, self.icon, timeToNotification))
        else:
            xbmc.executebuiltin('CancelAlarm({}-now,True)'.format(name.encode('utf-8', 'replace')))
            xbmc.executebuiltin('AlarmClock({}-now,Notification({},{},10000,{}),{},True)'.format(name.encode('utf-8', 'replace'), programTitle.encode('utf-8', 'replace'), description.encode('utf-8', 'replace'), self.icon, timeToNotification))

        if ADDON.getSetting('program_notifications_enabled') == 'true' and timeToNotification > 0:
            for chann in self.channels:
                if chann.title == channelTitle:
                    program = self.database.getProgramStartingAt(chann, startTime)
                    element = self.getScheduledNotificationForThisTime(program.startDate)
                    if element is not None:
                        programList = element[2]    #Fetch already scheduled list of programs
                        programList.append(program) #And add one more
                    else:
                        programList = list()
                        programList.append(program)
                        timer = threading.Timer(secToNotification, self.playScheduledProgram, [startTime])
                        self.timers.append([program.startDate, timer, programList])
                        timer.start()


    def _unscheduleNotification(self, programTitle, startTime):
        debug('_unscheduleNotification program %s' % (programTitle))
        name = self.createAlarmClockName(programTitle, startTime)
        if sys.version_info[0] > 2:
            xbmc.executebuiltin('CancelAlarm({}-5mins,True)'.format(name))
            xbmc.executebuiltin('CancelAlarm({}-now,True)'.format(name))
        else:
            xbmc.executebuiltin('CancelAlarm({}-5mins,True)'.format(name.encode('utf-8', 'replace')))
            xbmc.executebuiltin('CancelAlarm({}-now,True)'.format(name.encode('utf-8', 'replace')))

        #element = self.getScheduledNotificationForThisTime(startTime)
        for element in self.timers[:]:
            if element is not None:
                programList = element[2]
                for program in programList[:]:
                    if program.title == programTitle:
                        try:
                            programList.remove(program)
                        except:
                            pass
                        #break
                if len(programList) == 0:
                    element[1].cancel()
                    self.timers.remove(element)

    def addNotification(self, program, onlyOnce = False):
        self.database.addNotification(program, onlyOnce)
        self._scheduleNotification(program.channel.title, program.title, program.startDate)

    def removeNotification(self, program):
        self.database.removeNotification(program)
        self._unscheduleNotification(program.title, program.startDate)

    def playScheduledProgram(self, startTime):
        debug('Notification playScheduledProgram')
        programToPlay = None
        element = self.getScheduledNotificationForThisTime(startTime)
        if element is None:
            return
        programList = element[2]
        self.timers.remove(element)

        if len(programList) == 1:
            program = programList[0]
            if self.epg.currentChannel is not None and program.channel.id == self.epg.currentChannel.id:# and xbmc.Player().isPlaying():
                return
            if sys.version_info[0] > 2:
                ret = xbmcgui.Dialog().yesno(strings(NOTIFICATION_POPUP_NAME), '{} {}?'.format(strings(NOTIFICATION_POPUP_QUESTION), program.title))
            else:
                ret = xbmcgui.Dialog().yesno(strings(NOTIFICATION_POPUP_NAME).encode('utf-8', 'replace'), '{} {}?'.format(strings(NOTIFICATION_POPUP_QUESTION).encode('utf-8', 'replace'), program.title.encode('utf-8', 'replace')))
            if ret == True:
                programToPlay = program
        else:
            programs = list()
            if sys.version_info[0] > 2:
                programs.append(strings(NOTIFICATION_CANCEL))
            else:
                programs.append(strings(NOTIFICATION_CANCEL).encode('utf-8', 'replace'))
            for prog in programList:
                if sys.version_info[0] > 2:
                    programs.append(prog.title)
                else:
                    programs.append(prog.title.encode('utf-8', 'replace'))
            if sys.version_info[0] > 2:
                ret = xbmcgui.Dialog().select(strings(NOTIFICATION_POPUP_NAME), programs)
            else:
                ret = xbmcgui.Dialog().select(strings(NOTIFICATION_POPUP_NAME).encode('utf-8', 'replace'), programs)
            if ret > 0:
                programToPlay = programList[ret-1]

        if programToPlay is not None:
            #xbmc.Player().stop()
            if ADDON.getSetting('info_osd') == "true":
                self.epg.playChannel2(programToPlay)
            else:
                self.epg.playChannel(programToPlay.channel, programToPlay)

    def getScheduledNotificationForThisTime(self, startDate):
        for element in self.timers:
            if element[0] == startDate:
                debug('getScheduledNotificationForThisTime found programs starting at {}'.format(startDate))
                return element
        debug('getScheduledNotificationForThisTime no programs starting at {}'.format(startDate))
        return None

    def isScheduled(self, program):
        element = self.getScheduledNotificationForThisTime(program.startDate)
        if element is not None:
            programList = element[2]
            for prog in programList:
                if prog.channel.id == program.channel.id:
                    return True
        return False

    def close(self):
        debug('Notification close')
        for element in self.timers:
            element[1].cancel()
        self.timers = list()

if __name__ == '__main__':
    database = src.Database()

    def onNotificationsCleared():
        xbmcgui.Dialog().ok(strings(CLEAR_NOTIFICATIONS), strings(30971)+'.')

    def onInitialized(success):
        if success:
            database.clearAllNotifications()
            database.close(onNotificationsCleared)
        else:
            database.close()

    database.initialize(onInitialized)
