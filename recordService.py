#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2020 Mariusz89B
#   Copyright (C) 2016 Andrzej Mleczko

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

import sys

if sys.version_info[0] > 2:
    import configparser
else:
    import ConfigParser

import os, threading, datetime, subprocess, unicodedata, time, re, copy
import xbmcgui, xbmc, xbmcvfs
from strings import *
import strings as strings2
from playService import BasePlayService
from contextlib import contextmanager
import serviceLib
from skins import Skin

if sys.version_info[0] > 2:
    import urllib.request, urllib.parse, urllib.error
else:
    import urllib

import requests

recordIcon = 'recordIcon.png'
downloadIcon = 'downloadIcon.png'

downloadNotificationName        = strings(59985)
finishedDownloadNotificationName = strings(59986)
recordNotificationName          = strings(69004)
finishedRecordNotificationName  = strings(69005)
nonExistingRecordDirName        = strings(69006)
nonExistingDownloadDirName      = strings(69061)
failedRecordDialogName          = strings(69007)
failedDownloadDialogName        = strings(69059)
missingRecordBinaryString       = strings(69008)
missingDownloadBinaryString     = strings(69060)

maxNrOfReattempts               = int(ADDON.getSetting('max_reattempts'))
minRecordedFileSize             = 4097152 #Less then 4MB, remove downloaded data

ACTION_PARENT_DIR = 9
ACTION_PREVIOUS_MENU = 10
KEY_NAV_BACK = 92

sess = requests.Session()

try:
    if sys.version_info[0] > 2:
        config = configparser.RawConfigParser()
    else:
        config = ConfigParser.RawConfigParser()
    config.read(os.path.join(Skin.getSkinPath(), 'settings.ini'))
    skin_resolution = config.getboolean("Skin", "resolution")
except:
    skin_resolution = '720p'

class proxydt(datetime.datetime):
    @staticmethod
    def strptime(date_string, format):
        import time
        return datetime.datetime(*(time.strptime(date_string, format)[0:6]))

datetime.proxydt = proxydt

class RecordTimer:
    def __init__(self, startDate, startOffset, timer, programList):
        self.startDate = startDate
        self.startOffset = startOffset
        self.timer = timer
        self.programList = programList

class DownloadTimer:
    def __init__(self, startDate, startOffset, timer, programList):
        self.startDate = startDate
        self.startOffset = startOffset
        self.timer = timer
        self.programList = programList

class RecordService(BasePlayService):
    def __init__(self, epg):
        BasePlayService.__init__(self)
        if sys.version_info[0] > 2:
            self.rtmpdumpExe        = xbmcvfs.translatePath(ADDON.getSetting('rtmpdumpExe'))
            self.ffmpegdumpExe      = xbmcvfs.translatePath(ADDON.getSetting('ffmpegExe'))
            self.icon               = os.path.join(xbmcvfs.translatePath(ADDON.getAddonInfo('path')), recordIcon)
            self.dwicon             = os.path.join(xbmcvfs.translatePath(ADDON.getAddonInfo('path')), downloadIcon)
            self.recordDestinationPath = xbmcvfs.translatePath(ADDON.getSetting('record_folder'))

        else:
            self.rtmpdumpExe        = xbmc.translatePath(ADDON.getSetting('rtmpdumpExe'))
            self.ffmpegdumpExe      = xbmc.translatePath(ADDON.getSetting('ffmpegExe'))
            self.icon               = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('path')), recordIcon)
            self.dwicon             = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('path')), downloadIcon)
            self.recordDestinationPath = xbmc.translatePath(ADDON.getSetting('record_folder'))

        self.rtmpdumpAvailable   = os.path.isfile(self.rtmpdumpExe)
        self.ffmpegdumpAvailable = os.path.isfile(self.ffmpegdumpExe)
        self.useOnlyFFmpeg       = ADDON.getSetting('use_only_ffmpeg')
        self.epg                 = epg
        self.threadList          = list()
        self.threadDownloadList  = list()
        self.timers              = list()
        self.timersdw            = list()
        self.cleanupTimer        = None
        self.cleanupDownloadTimer = None
        self.ffmpegFormat        = 'mpegts'
        self.isDownload          = False
        self.program             = None
        self.processIsCanceled   = False
        self.strmUrl             = None
        self.archiveString       = None
        self.downloadDuration    = 0
        self.progress            = None
        self.downloadSize        = 0
        self.startOffsetDownload = 0
        self.endOffsetDownload   = 0
        self.license             = None
        self.downloading         = False 


        if ADDON.getSetting('ffmpeg_dis_cop_un') == 'true':
            self.ffmpegDisableCopyUnknown = True
        else:
            self.ffmpegDisableCopyUnknown = False

        if 'avconv' in self.ffmpegdumpExe:
            self.force_h264_mp4toannexb = True
        else:
            self.force_h264_mp4toannexb = False

        if ADDON.getSetting('record_stop_playback') == 'true':
            self.recordingStopsPlayback = True
        else:
            self.recordingStopsPlayback = False

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

    def convertTimedelta(self, duration):
        days, seconds = duration.days, duration.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = (seconds % 60)
        return minutes


    def getTimeshift(self):
        try:
            file_name = os.path.join(self.profilePath, 'playlist_ts.json')
            f = xbmcvfs.File(file_name, 'r')
            ArchivePlayList = f.read()
            f.close()
        except:
            ArchivePlayList += ''

        return ArchivePlayList


    def formatFileSize(self, num):
        step_unit = 1000.0
        for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
            if num < step_unit:
                return "%3.1f %s" % (num, x)
            num /= step_unit


    def calcFileSize(self, threadData, bitrate, depth):
        duration = threadData['downloadDuration']
        result = float(bitrate / depth * duration * 1000)
        return result


    def createProgressDialog(self):
        self.progress = xbmcgui.DialogProgressBG()
        self.progress.create(strings(69056))
        #xbmc.sleep(1000)
        return self.progress


    def recordProgramGui(self, program):
        self.program = program
        self.isDownload = False
        updateDB = False
        try:
            if self.calculateTimeDifference(program.endDate) <= 0:
                archiveList = self.getTimeshift()

                if program.channel.id.upper() in archiveList and ADDON.getSetting('archive_support') == 'true' and program.startDate < datetime.datetime.now():
                    self.isDownload = True
                    if self.isProgramDownloadScheduled(program):
                        ret = xbmcgui.Dialog().yesno(strings(69000), strings(69009))
                        if ret == True:
                            self.epg.database.removeRecording(program)
                            self.cancelProgramDownload(program)
                            updateDB = True

                    elif program.recordingScheduled != 1:
                        if sys.version_info[0] > 2:
                            res = xbmcgui.Dialog().yesno(strings(70006) + ' - m-TVGuide [COLOR gold]EPG[/COLOR]', strings(31000).format(program.title) )
                        else:
                            res = xbmcgui.Dialog().yesno(strings(70006) + ' - m-TVGuide [COLOR gold]EPG[/COLOR]', strings(31000).format(program.title).encode('utf-8') )
                        if res == True:
                            downloadMenu = DownloadMenu(program)
                            downloadMenu.doModal()
                            saveRecording, chkdate, self.startOffsetDownload, self.endOffsetDownload = downloadMenu.getOffsets()

                            if saveRecording == True:
                                self.startOffsetDownload *= 60
                                self.endOffsetDownload *= 60
                                if self.scheduleDownload(program, self.startOffsetDownload, self.endOffsetDownload):
                                    self.epg.database.addRecording(program, self.startOffsetDownload, self.endOffsetDownload)
                                    updateDB = True
                            elif chkdate == False:
                                xbmcgui.Dialog().ok(failedDownloadDialogName, strings(59998))

                    else:
                        self.epg.database.removeRecording(program)
                        updateDB = True

                else:
                    xbmcgui.Dialog().ok(strings(70006) + ' - m-TVGuide [COLOR gold]EPG[/COLOR]', strings(59987) )
                    return

            if program.endDate > datetime.datetime.now() and self.isProgramRecordScheduled(program):
                ret = xbmcgui.Dialog().yesno(strings(69000), strings(69009))
                if ret == True:
                    self.epg.database.removeRecording(program)
                    self.cancelProgramRecord(program)
                    updateDB = True

            elif program.recordingScheduled != 1:
                if self.isDownload == False:
                    recordMenu = RecordMenu(program)
                    recordMenu.doModal()
                    saveRecording, startOffset, endOffset = recordMenu.getOffsets()

                    if saveRecording == True:
                        startOffset *= 60
                        endOffset *= 60
                        if self.scheduleRecording(program, startOffset, endOffset):
                            self.epg.database.addRecording(program, startOffset, endOffset)
                            updateDB = True

            else:
                self.epg.database.removeRecording(program)
                updateDB = True

        except:
            deb('recordProgramGui exception: %s' % getExceptionString())
        return updateDB


    def scheduleDownload(self, program, startOffset, endOffset, delayRecording = 0):

        program = copy.deepcopy(program)
        program.endDate += datetime.timedelta(seconds=endOffset)

        if sys.version_info[0] > 2:
            deb('DownloadService scheduling download for program {}, starting at {}, start offset {}'.format(program.title, program.startDate, startOffset))
        else:
            deb('DownloadService scheduling download for program {}, starting at {}, start offset {}'.format(program.title.encode('utf-8'), program.startDate, startOffset))

        if self.rtmpdumpAvailable == False and self.ffmpegdumpAvailable == False:
            deb('DownloadService - no record application installed!')
            self.showThreadedDialog(failedDownloadDialogName, "\n" + missingDownloadBinaryString + ' RTMPDUMP & FFMPEG.')
            return False

        if not self.checkIfDownloadDirExist():
            return False

        secToRecording = self.calculateTimeDifference(program.startDate, timeOffset = startOffset + 5 )
        if secToRecording < 0:
            secToRecording = delayRecording #start now

        for element in self.getScheduledDownloadingsForThisTime(program.startDate):
            if element.startOffset == startOffset:
                programList = element.programList #Fetch already scheduled list of programs
                for prog in programList:
                    if program.channel == prog.channel and program.startDate == prog.startDate:
                        return False #already on list
                programList.append(program) #add one more
                return True

        programList = list()
        programList.append(program)
        timer = threading.Timer(secToRecording, self.downloadChannel, [program.startDate, startOffset])
        self.timersdw.append(DownloadTimer(program.startDate, startOffset, timer, programList))
        timer.start()
        return True


    def downloadChannel(self, startTime, startOffset):
        deb('DownloadService downloadChannel startTime {}, startOffset {}'.format(startTime, startOffset))
        for element in self.getScheduledDownloadingsForThisTime(startTime):
            if element.startOffset == startOffset:
                programList = element.programList
                self.timersdw.remove(element)
                for program in programList:
                    urlList = self.epg.database.getStreamUrlList(program.channel)
                    threadData = {'urlDownloadList' : urlList, 'program' : program, 'downloadHandle' : None, 'stopDownloadTimer' : None, 'terminateDownloadThread' : False}
                    thread = threading.Thread(name='downloadLoop', target = self.downloadLoop, args=[threadData])
                    self.threadDownloadList.append([thread, threadData])

                for thread, threadData in self.threadDownloadList:
                    thread.start()
                    if not self.downloading:
                        self.processIsCanceled = False
                        self.startDownload(threadData)


    def startDownload(self, threadData):
        deb('startDownload')
        diag = self.createProgressDialog()

        iDownsize = 0

        while not (self.processIsCanceled or diag.isFinished()):
            try:
                program = self.getOutputFilename(threadData['program'], threadData['partNumber'])
                dest = os.path.join(self.recordDestinationPath, self.getOutputFilename(threadData['program'], threadData['partNumber']))

                if xbmcvfs.exists(dest):
                    stat = os.stat(dest)
                    iDownsize = stat.st_size
            except:
                program = ''
                iDownsize = 1000


            if float(self.downloadSize) > 1:
                iTotalSize = float(self.downloadSize)
            else:
                iTotalSize = 1000
            
            self.stateCallBackFunction(program, iDownsize, iTotalSize)

        self.processIsCanceled = True
        self.downloading = False
        self.progress.close()

    def stateCallBackFunction(self, program, iDownsize, iTotalSize):
        if self.progress.isFinished():
            self.createProgressDialog()

        iPercent = int(float(iDownsize * 100) / iTotalSize)
        if iTotalSize <= 1000:
            TotalSize = '-'
        elif iTotalSize < 5000000:
            TotalSize = '0 MB'
        else:
            TotalSize = self.formatFileSize(iTotalSize)

        if iDownsize < 5000000:
            Downsize = '0 MB'
        else:
            Downsize = self.formatFileSize(float(iDownsize))

        self.progress.update(iPercent, program, Downsize + ' / ' + TotalSize)
    
        if (self.progress.isFinished()) and not (self.processIsCanceled):
            self.processIsCanceled = True
            self.progress.close()


    def StopAll(self):
        self.processIsCanceled = True
        self.downloading = False

        try:
            self.progress.close()
        except:
            pass

        return

    
    def downloadLoop(self, threadData):
        threadData['success']               = False
        threadData['notificationDisplayed'] = False
        threadData['destinationFile']       = os.path.join(self.recordDestinationPath, self.getOutputFilename(threadData['program']))
        threadData['partNumber']            = 1
        threadData['nrOfReattempts']        = 0     
        threadData['downloadOptions']       = { 'forceRTMPDump' : False, 'settingsChanged' : False, 'force_h264_mp4toannexb' : self.force_h264_mp4toannexb }
        threadData['downloadDuration']      = self.calculateDownloadTimeDifference(threadData['program'].startDate, threadData['program'].endDate, timeOffset = -5 )

        while self.checkIfDownloadShouldContinue(threadData):
            for url in threadData['urlDownloadList']:
                if not self.checkIfDownloadShouldContinue(threadData):
                    break

                threadData['downloadOptions']['forceRTMPDump'] = False

                self.downloadUrl(url, threadData)
                if threadData['downloadOptions']['settingsChanged'] == True and self.checkIfDownloadShouldContinue(threadData):
                    deb('DownloadService - detected settings change for downloaded stream - retrying download')
                    self.downloadUrl(url, threadData)

            #Go to sleep, maybe after that any service will be free to use
            for sleepTime in range(5):
                if not self.checkIfDownloadShouldContinue(threadData):
                    break
                time.sleep(1)

        if sys.version_info[0] > 2:
            deb('DownloadService - end of download program: {}'.format(threadData['program'].title))
        else:
            deb('DownloadService - end of download program: {}'.format(threadData['program'].title.encode('utf-8')))
        
        self.epg.database.removeRecording(threadData['program'])
        self.showEndDownloadNotification(threadData)
        
        if self.cleanupDownloadTimer is not None:
            self.cleanupDownloadTimer.cancel()
        self.cleanupDownloadTimer = threading.Timer(0.2, self.cleanupFinishedDownloadThreads)
        self.cleanupDownloadTimer.start()

    
    def downloadProgram(self, startDate, endDate):
        startDate += datetime.timedelta(seconds=self.startOffsetDownload)
        endDate += datetime.timedelta(seconds=self.endOffsetDownload)

        try:
            ProgramEndDate = datetime.proxydt.strptime(str(endDate), '%Y-%m-%d %H:%M:%S')
            ProgramStartDate = datetime.proxydt.strptime(str(startDate), '%Y-%m-%d %H:%M:%S')
        except:
            ProgramEndDate = datetime.proxydt.strptime(str(datetime.datetime.now()), '%Y-%m-%d %H:%M:%S.%f')
            ProgramStartDate = datetime.proxydt.strptime(str(datetime.datetime.now()), '%Y-%m-%d %H:%M:%S.%f')

        try:
            ProgramNowDate = datetime.proxydt.strptime(str(datetime.datetime.now()), '%Y-%m-%d %H:%M:%S.%f')
        except:
            ProgramNowDate = datetime.proxydt.strptime(str(datetime.datetime.now()), '%Y-%m-%d %H:%M:%S')

        downloadProgram = ''

        from time import mktime

        n = datetime.datetime.now()
        t = ProgramStartDate
        e = ProgramEndDate

        # Duration
        durationCalc = ((ProgramEndDate - ProgramStartDate).total_seconds() / 60.0)
        duration = re.sub('.\d+$', '', str(durationCalc))

        # Offset
        offsetCalc = ((datetime.datetime.now() - ProgramStartDate).total_seconds() / 60.0)
        offset = re.sub('.\d+$', '', str(offsetCalc))

        # UTC/LUTC
        utc = mktime(t.timetuple())
        utc = re.sub('.0$', '', str(utc))
        lutc = mktime(n.timetuple())
        lutc = re.sub('.0$', '', str(lutc))

        # Datestring
        year = t.strftime("%Y")
        month = t.strftime("%m")
        day = t.strftime("%d")
        hour = t.strftime("%H")
        minute = t.strftime("%M")
        second = t.strftime("%S")

        archivePlaylist = '{duration}, {offset}, {utc}, {lutc}, {y}, {m}, {d}, {h}, {min}, {s}'.format(
            duration=duration, offset=offset, utc=utc, lutc=lutc, y=year, m=month, d=day, h=hour, min=minute, s=second)

        mktime_duration = mktime(e.timetuple()) - mktime(t.timetuple())

        return archivePlaylist, mktime_duration


    def downloadUrl(self, url, threadData):
        self.archiveString, self.downloadDuration = self.downloadProgram(self.program.startDate, self.program.endDate)

        threadData['downloadOptions']['settingsChanged'] = False
        threadData['downloadDuration'] = self.downloadDuration

        if threadData['downloadDuration'] <= 0:
            deb('DownloadService - downloadUrl duration is 0, aborting download')
            return

        if self.recordingStopsPlayback and (xbmc.Player().isPlaying() or self.epg.playService.isWorking()):
            deb('DownloadService - stopping ongoing playback')
            self.epg.playService.stopPlayback()
            xbmc.sleep(500)

        cid, service = self.parseUrl(url)
        channelInfo = self.getChannelDownload(cid, service)
        
        strmUrl_catchup = ''
        strmUrl = ''

        if channelInfo is not None:
            if channelInfo.catchup:
                strmUrl_catchup = channelInfo.catchup
            else:
                strmUrl = channelInfo.strm

        # Catchup format string
        if ADDON.getSetting('archive_support') == 'true':
            if str(self.archiveString) != '':
                archivePlaylist = str(self.archiveString)
                catchupList = archivePlaylist.split(', ')

                # Catchup strings
                duration = catchupList[0]
                offset = catchupList[1]
                utc = catchupList[2]
                lutc = catchupList[3]
                year = catchupList[4]
                month = catchupList[5]
                day = catchupList[6]
                hour = catchupList[7]
                minute = catchupList[8]
                second = catchupList[9]

                if strmUrl_catchup or ADDON.getSetting('archive_type') == '4':
                    if strmUrl_catchup:
                        try:
                            strmUrl = strmUrl_catchup.format(start=utc, timestamp=lutc)
                        except:
                            strmUrl = strmUrl_catchup.format(utc=utc, lutc=lutc)

                        if 'mono' in strmUrl:
                            strmUrl = re.sub('\$', '', str(strmUrl))
                            strmUrl = re.sub('mono', 'video', str(strmUrl))
                    else:
                        deb('archive_type(4) wrong type')
                        self.cancelProgramDownload(self.program)
                        updateDB = True
                        xbmcgui.Dialog().ok(strings(30998), strings(59979))
                        self.processIsCanceled = True
                        return False
                else:

                    # Default
                    if ADDON.getSetting('archive_type') == '0':
                        matches = re.compile('^(http[s]?://[^/]+)/([^/]+)/([^/]*)(mpegts|\\.m3u8)(\\?.+=.+)?$')

                        if matches.match(strmUrl):
                            fsHost = matches.search(strmUrl).group(1)
                            fsChannelId = matches.search(strmUrl).group(2)
                            fsListType = matches.search(strmUrl).group(3)
                            fsStreamType = matches.search(strmUrl).group(4)
                            fsUrlAppend = matches.search(strmUrl).group(5)

                            if fsStreamType == 'mpegts':
                                m_catchupSource = str(fsHost) + "/" + str(fsChannelId) + '/timeshift_abs-$' + str(utc) + '.ts' + str(fsUrlAppend)
                            else:
                                offset = str(int(offset) * 60)

                                if fsListType == 'index':
                                    m_catchupSource = str(fsHost) + '/' + str(fsChannelId) + '/timeshift_rel-' + str(offset) + '.m3u8' + str(fsUrlAppend)
                                    
                                elif fsListType == 'video':
                                    m_catchupSource = str(fsHost) + '/' + str(fsChannelId) + '/video-' + str(utc) + '-' + str(lutc) + '.m3u8' + str(fsUrlAppend)
                                
                                elif 'hls-custom' in fsListType:
                                    new_url = strmUrl + '?utc={utc}&lutc={lutc}'.format(utc=utc, lutc=lutc)
                                    response = requests.get(new_url, allow_redirects=False, verify=False, timeout=2)
                                    strmUrlNew = response.headers.get('Location', None) if 'Location' in response.headers else strmUrl

                                    if strmUrlNew:
                                        strmUrlNew
                                    else:
                                        strmUrlNew = strmUrl

                                    fsHost = matches.search(strmUrlNew).group(1)
                                    fsChannelId = matches.search(strmUrlNew).group(2)
                                    fsListType = matches.search(strmUrlNew).group(3)
                                    fsStreamType = matches.search(strmUrlNew).group(4)
                                    fsUrlAppend = matches.search(strmUrlNew).group(5)
                                    
                                    fsUrlAppend = re.sub('&.*$', '', str(fsUrlAppend))
                                    fsListType = 'video'

                                    m_catchupSource = str(fsHost) + '/' + str(fsChannelId) + '/' + str(fsListType) + '-' + str(utc) + '-' + str(offset) + str(fsStreamType) + str(fsUrlAppend)

                                else:
                                    m_catchupSource = str(fsHost) + '/' + str(fsChannelId) + '/' + str(fsListType) + '-timeshift_rel-' + str(offset) + '.m3u8' + str(fsUrlAppend)

                            strmUrl = m_catchupSource

                        else:
                            deb('archive_type(0) wrong type')
                            self.cancelProgramDownload(self.program)
                            updateDB = True
                            xbmcgui.Dialog().ok(strings(30998), strings(59979))
                            self.processIsCanceled = True
                            return False

                    # Append
                    if ADDON.getSetting('archive_type') == '1':
                        setting = ADDON.getSetting('archive_string')

                        putc = re.compile('(^\?utc=|^\&utc=)')
                        mutc = putc.match(setting)

                        putv = re.compile('(^.*)(\{Y\}.\{m\}.\{d\}.*\{H\}.\{M\}.\{S\})(?=.*|$)')
                        mutv = putv.match(setting)

                        if mutc:
                            catchup = ADDON.getSetting('archive_string').format(utc=utc, lutc=lutc)

                        elif mutv:
                            catchup = ADDON.getSetting('archive_string').format(Y=year, m=month, d=day, H=hour, M=minute, S=second)

                        putc = re.compile('(^\?utc=|^\&utc=)')
                        mutc = putc.match(catchup)

                        putv = re.compile('(^.*)(\d{4}.\d{2}.\d{2}.*\d{2}.\d{2}.\d{2})(?=.*|$)')
                        mutv = putv.match(catchup)

                        if mutc:
                            m_catchupSource = strmUrl + catchup
                            strmUrl = m_catchupSource + '-' + str(int(duration)*60)
                        elif mutv:
                            m_catchupSource = strmUrl + catchup
                            strmUrl = m_catchupSource + '?duration={duration}'.format(duration=str(int(duration)*60))
                        else:
                            deb('archive_type(1) wrong type')
                            xbmcgui.Dialog().ok(strings(30998), strings(59979))
                            return

                    # Xtream Codes
                    if ADDON.getSetting('archive_type') == '2':
                        matches = re.compile('^(http[s]?://[^/]+)/(?:live/)?([^/]+)/([^/]+)/([^/\\.]+)(\\.m3u[8]?|\\.ts)?$')

                        if matches.match(strmUrl):
                            xcHost = matches.search(strmUrl).group(1)
                            xcUsername = matches.search(strmUrl).group(2)
                            xcPassword = matches.search(strmUrl).group(3)
                            xcChannelId = matches.search(strmUrl).group(4)
                            try:
                                xcExtension = matches.search(strmUrl).group(5)
                            except:
                                xcExtension = ''

                            if xcExtension == '':
                                m_isCatchupTSStream = True
                                xcExtension = ".ts"

                            start = '{y}-{m}-{d}:{h}-{min}'.format(y=year, m=month, d=day, h=hour, min=minute)
                            timeshift = duration + '/' + start + '/' + duration

                            try:
                                m_catchupSource = xcHost + "/timeshift/" + xcUsername + "/" + xcPassword + "/"+timeshift+"/" + xcChannelId + xcExtension
                            except:
                                m_catchupSource = xcHost + "/timeshift/" + xcUsername + "/" + xcPassword + "/"+timeshift+"/" + xcChannelId

                            strmUrl = m_catchupSource

                        else:
                            deb('archive_type(2) wrong type')
                            self.cancelProgramDownload(self.program)
                            updateDB = True
                            xbmcgui.Dialog().ok(strings(30998), strings(59979))
                            self.processIsCanceled = True
                            return False

                    # Shift
                    if ADDON.getSetting('archive_type') == '3':
                        if '?' in strmUrl:
                            m_catchupSource = strmUrl + '&utc={utc}&lutc={lutc}-{duration}'.format(utc=utc, lutc=lutc, duration=duration)
                            strmUrl = m_catchupSource
                        else:
                            m_catchupSource = strmUrl + '?utc={utc}&lutc={lutc}-{duration}'.format(utc=utc, lutc=lutc, duration=duration)
                            strmUrl = m_catchupSource
            
            try:
                channelInfo.strm = strmUrl
            except:
                channelInfo.strm

        if channelInfo is None:
            threadData['nrOfReattempts'] += 1
            deb('DownloadService downloadUrl - locked service {} - trying next, nrOfReattempts: {}, max: {}'.format(service, threadData['nrOfReattempts'], maxNrOfReattempts))
            return #go to next stream - this one seems to be locked

        self.findNextUnusedOutputFilename(threadData)

        if not self.downloading:
            recordCommand = self.generateFFMPEGDownloadCommand(channelInfo, threadData['downloadDuration'], threadData['destinationFile'], threadData['downloadOptions'])

            if recordCommand:
                self.showStartDownloadNotification(threadData)
                output = self.download(recordCommand, threadData)
                self.postDownloadActions(output, threadData)
            else:
                threadData['nrOfReattempts'] += 1


    def download(self, recordCommand, threadData):
        deb('DownloadService download command: {}'.format(str(recordCommand)))
        avgList = list()

        threadData['downloadStartTime'] = datetime.datetime.now()
        output = ''
        si = None
        if os.name == 'nt':
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        recordEnviron = os.environ.copy()
        oldLdPath = recordEnviron.get("LD_LIBRARY_PATH", '')
        recordEnviron["LD_LIBRARY_PATH"] = os.path.join(os.path.dirname(recordCommand[0]), 'lib') + ':/lib:/usr/lib:/usr/local/lib'
        if oldLdPath != '':
            recordEnviron["LD_LIBRARY_PATH"] = recordEnviron["LD_LIBRARY_PATH"] + ":" + oldLdPath

        try:
            threadData['stopDownloadTimer'] = threading.Timer(threadData['downloadDuration'], self.stopDownload, [threadData])
            threadData['stopDownloadTimer'].start()

            self.downloading = True 

            threadData['downloadHandle'] = subprocess.Popen(recordCommand, shell=False, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, startupinfo=si, env=recordEnviron)
            duration = threadData['downloadDuration']

            for line in threadData['downloadHandle'].stdout:
                #mediaprobe_re = re.compile(r"Duration:\s+(?P<dur>(?:(?:\d:?)+[.]?\d*)|N/A)(?:.+start:\s+(?P<start>\d+[.]\d+))?.+bitrate:\s+(?P<bitrate>(?:\d+\s*..[/]s)|N/A)")
                #streamprobe_re = re.compile(r"\s*Stream.+:\s+Video:(.*,\s(?P<depth>.*)).+\s+(?P<res>\d+x\d+)(?:.*,\s*(?P<fps>\d+[.]?\d*)\sfps)?(?:.+\(default\))?")
                #audioprobe_re = re.compile(r"\s*Stream.+:\s+Audio:.*")
                #fftime_re = re.compile(r"(?P<h>\d+):(?P<m>\d+):(?P<s>\d+)\.(?P<fract>\d+)")

                #media = mediaprobe_re.search(line).group(0)
                #deb('media: {}'.format(media))

                #duration  = mediaprobe_re.search(line).group(1)
                #deb('duration: {}'.format(duration))
                
                #start  = mediaprobe_re.search(line).group(2)
                #deb('start: {}'.format(start))
                
                #bitrate  = mediaprobe_re.search(line).group(3)
                #deb('bitrate: {}'.format(bitrate))

                #bitrateNum = re.findall(r'(\d+)\skb/s', bitrate)
                #bitrateCalc = int(bitrateNum[0])

                #video = streamprobe_re.search(line).group(0)
                #deb('video: {}'.format(video))

                #res  = streamprobe_re.search(line).group(3)
                #deb('res: {}'.format(res))

                #split = res.split('x')
                #width = int(split[0])
                #height = int(split[1])

                #deb('width: {}'.format(self.width))
                #deb('height: {}'.format(self.height))

                #fps  = streamprobe_re.search(line).group(4)
                #fps = int(fps)
                #deb('fps: {}'.format(self.fps))

                #depth = streamprobe_re.search(line).group(2)
                #deb('depth: {}'.format(depth))

                #bit8 = ['yuv420p', 'yuvj420p', 'yuv422p', 'yuvj422p', 'yuv444p', 'yuvj444p', 'nv12', 'nv16']
                #bit10 = ['yuv420p10le', 'yuv422p10le', 'yuv444p10le', 'nv20le']

                #if depth in bit8:
                    #depthSize = 8

                #elif depth in bit10:
                    #depthSize = 10

                #else:
                    #depthSize = 8

                #audio  = audioprobe_re.search(line).group(0)
                #deb('audio: {}'.format(audio))

                #h  = fftime_re.search(line).group(1)
                #deb('h: {}'.format(h))
                #m  = fftime_re.search(line).group(2)
                #deb('m: {}'.format(m))
                #s  = fftime_re.search(line).group(3)
                #deb('s: {}'.format(s))
                #f  = fftime_re.search(line).group(4)
                #deb('f: {}'.format(f))


                ### Regex ###

                # Resolution

                #resolution = re.findall('Video:.*\s(\d+x\d+)', video)
                #res = resolution[0]

                #split = res.split('x')
                #width = int(split[0])
                #height = int(split[1])

                # Fps

                #frames = re.findall('Video:.*,\s(\d+)', video)
                #fps = frames[0]
                #fps = int(fps)

                i = 1

                while i < 15:
                    # Bitrate
                    bitrate_re = re.findall(r'.*bitrate=(.*?)kbits.*', line)
                    if bitrate_re:
                        bitrate
                    else:
                        bitrate = 0
                    
                    try:
                        bitrate = float(bitrate_re[0])
                        avgList.append(bitrate)
                        
                    except:
                        bit = 0

                    if bitrate > 1:
                        bit = sum(avgList) / len(avgList)
                        self.downloadSize = self.calcFileSize(threadData, bit, 8)

                    i += 1

            output = threadData['downloadHandle'].communicate()[0]
            returnCode = threadData['downloadHandle'].returncode
            threadData['stopDownloadTimer'].cancel()
            threadData['downloadHandle'] = None

            self.downloading = False #dodane

            deb('DownloadService download finished, \noutput: {}, \nstatus: {}, Command: {}'.format(output, returnCode, str(recordCommand)))

        except Exception as ex:
            deb('DownloadService download exception: {}'.format(getExceptionString()))
                
        return output


    def stopDownload(self, threadData, kill = False):
        if threadData['downloadHandle'] is not None:
            self.downloading = False
            try:
                threadData['downloadHandle'].terminate()
                #if kill == True:
                    #threadData['recordHandle'].kill()
            except:
                pass


    def postDownloadActions(self, recordOutput, threadData):
        self.StopAll()
        self.analyzeDownloadOutput(recordOutput, threadData['downloadOptions'])
        recordedSecs = (threadData['program'].endDate - threadData['downloadStartTime']).seconds

        if(threadData['downloadDuration'] - recordedSecs < 60):
            if sys.version_info[0] > 2:
                deb('DownloadService downloadLoop successfully recored program: {}, started at: {}, ended at: {}, duration {}, now: {}'.format(threadData['program'].title, threadData['program'].startDate, threadData['program'].endDate, threadData['downloadDuration'], datetime.datetime.now()))
            else:
                deb('DownloadService downloadLoop successfully recored program: {}, started at: {}, ended at: {}, duration {}, now: {}'.format(threadData['program'].title.encode('utf-8'), threadData['program'].startDate, threadData['program'].endDate, threadData['downloadDuration'], datetime.datetime.now()))
            threadData['success'] = True
        else:
            if sys.version_info[0] > 2:
                deb('DownloadService downloadLoop ERROR: too short recording, got: {} sec, should be: {}, program: {}, start at: {}, end at: {}, nrOfReattempts: {}, max: {}'.format(recordedSecs, threadData['downloadDuration'], threadData['program'].title, threadData['program'].startDate, threadData['program'].endDate, threadData['nrOfReattempts'], maxNrOfReattempts))
            else:
                deb('DownloadService downloadLoop ERROR: too short recording, got: {} sec, should be: {}, program: {}, start at: {}, end at: {}, nrOfReattempts: {}, max: {}'.format(recordedSecs, threadData['downloadDuration'], threadData['program'].title.encode('utf-8'), threadData['program'].startDate, threadData['program'].endDate, threadData['nrOfReattempts'], maxNrOfReattempts))
            threadData['nrOfReattempts'] += 1
            if os.path.isfile(threadData['destinationFile']) and os.path.getsize(threadData['destinationFile']) < minRecordedFileSize: #Less than minimum, remove downloaded data
                try:
                    deb('DownloadService downloadLoop deleting incomplete download file {}, recorded for {} s, size {} KB'.format(threadData['destinationFile'], recordedSecs, os.path.getsize(threadData['destinationFile'])/1024))
                    os.remove(threadData['destinationFile'])
                except:
                    pass


    def analyzeDownloadOutput(self, output, recordOptions):
        try:
            if 'Unrecognized option' in output:
                if 'copy_unknown' in output:
                    deb('RecordService detected problem with copy_unknown - disabling it!')
                    ADDON.setSetting(id="ffmpeg_dis_cop_un", value=str("true"))
                    if self.ffmpegDisableCopyUnknown == False:
                        recordOptions['settingsChanged'] = True
                        self.ffmpegDisableCopyUnknown = True

            if "Detected librtmp style URL parameters, these aren't supported" in output:
                deb('RecordService detected that stream needs to be recorded by RTMPdump')
                if recordOptions['forceRTMPDump'] == False:
                    recordOptions['settingsChanged'] = True
                    recordOptions['forceRTMPDump'] = True

            if "use -bsf h264_mp4toannexb" in output:
                deb('RecordService detected that stream needs to be encoded using h264_mp4toannexb')
                if recordOptions['force_h264_mp4toannexb'] == False:
                    recordOptions['settingsChanged'] = True
                    recordOptions['force_h264_mp4toannexb'] = True
        except:
            pass


    def calculateDownloadTimeDifference(self, programStartTime, programEndTime, timeOffset = 0):
        timeDiff = programEndTime - programStartTime
        programDuration = ((timeDiff.days * 86400) + timeDiff.seconds) + timeOffset
        return programDuration    


    def checkIfDownloadShouldContinue(self, threadData):
        return (threadData['success'] == False and threadData['nrOfReattempts'] <= maxNrOfReattempts and self.terminating == False and threadData['terminateDownloadThread'] == False and strings2.M_TVGUIDE_CLOSING == False)


    def generateFFMPEGDownloadCommand(self, channelInfo, programDuration, destinationFile, recordOptions):
        recordCommand = list()
        recordCommand.append(self.ffmpegdumpExe)

        duration = datetime.timedelta(seconds=int(programDuration))

        streamSource = channelInfo.strm
        coockieSeparator = streamSource.find('|')
        if coockieSeparator > 0:
            removedCoockie = streamSource[coockieSeparator+1:]
            streamSource = streamSource[:coockieSeparator]
            deb('DownloadService - found cookie separator in download source! Remove this from URL: %s' % removedCoockie)

            headers = removedCoockie.split('&')
            newHeader = ""
            for header in headers:
                deb('Got: {}'.format(header))
                if 'User-Agent' in header:
                    newHeader = newHeader + "User-Agent: {}\r\n".format(serviceLib.HOST)
                else:
                    newHeader = newHeader + "{}\r\n".format(header)

            recordCommand.append("-headers")
            recordCommand.append(newHeader)

        recordCommand.append("-protocol_whitelist")
        recordCommand.append("file,http,https,tcp,tls,crypto")

        recordCommand.append("-probesize")
        recordCommand.append("50M")

        recordCommand.append("-analyzeduration")
        recordCommand.append("20M")

        recordCommand.append("-i")

        recordCommand.append("{}".format(streamSource))

        #recordCommand.append("-vcodec")
        #recordCommand.append("mpeg4")

        #recordCommand.append("-b")
        #recordCommand.append("3M")

        recordCommand.append("-c")
        recordCommand.append("copy")

        recordCommand.append("-map")
        recordCommand.append("0")

        #recordCommand.append("-sn")  #Disable subtitles

        recordCommand.append("-f")
        recordCommand.append("{}".format(self.ffmpegFormat))

        if recordOptions['force_h264_mp4toannexb']:
            recordCommand.append("-bsf")
            recordCommand.append("h264_mp4toannexb")

        recordCommand.append("-t")
        recordCommand.append(str(duration))
        recordCommand.append("-loglevel")
        recordCommand.append("info")
        recordCommand.append("-n")
        recordCommand.append("{}".format(destinationFile))

        return recordCommand


    def showStartDownloadNotification(self, threadData):
        if threadData['notificationDisplayed'] == False:
            if sys.version_info[0] > 2:
                xbmc.executebuiltin('Notification({},{},10000,{})'.format(downloadNotificationName, self.normalizeString(threadData['program'].title), self.dwicon))
            else:
                xbmc.executebuiltin('Notification({},{},10000,{})'.format(downloadNotificationName.encode('utf-8', 'replace'), self.normalizeString(threadData['program'].title), self.dwicon))

            threadData['notificationDisplayed'] = True #show only once

    def showEndDownloadNotification(self, threadData):
        if threadData['notificationDisplayed'] == True:
            if sys.version_info[0] > 2:
                xbmc.executebuiltin('Notification({},{},10000,{})'.format(finishedDownloadNotificationName, self.normalizeString(threadData['program'].title), self.dwicon))
            else:
                xbmc.executebuiltin('Notification({},{},10000,{})'.format(finishedDownloadNotificationName.encode('utf-8', 'replace'), self.normalizeString(threadData['program'].title), self.dwicon))


    def scheduleAllRecordings(self):
        deb('scheduleAllRecordings')
        channels = self.epg.database.getChannelList(True)
        for channel_name, program_title, start_date, end_date, start_offset, end_offset in self.epg.database.getRecordings():
            timeDelta = end_date - datetime.datetime.now()
            timeToProgramEnd = timeDelta.seconds + timeDelta.days * 86400
            if timeToProgramEnd < 0:
                try:
                    debug('scheduleAllRecordings {} has already finished'.format(program_title))
                except:
                    debug('scheduleAllRecordings {} has already finished'.format(program_title.encode('utf-8', 'replace')))
                continue
            for channel in channels:
                if channel.id == channel_name:
                    program = self.epg.database.getProgramStartingAt(channel, start_date)
                    if program is not None and self.isProgramRecordScheduled(program) == False and self.isDownload is False:
                        self.scheduleRecording(program, start_offset, end_offset, 30)
                    if program is not None and self.isProgramDownloadScheduled(program) == False and self.isDownload is True:
                        self.scheduleDownload(program, start_offset, end_offset, 30)
                    break
        debug('scheduleAllRecordings completed!')


    def scheduleRecording(self, program, startOffset, endOffset, delayRecording = 0):

        program = copy.deepcopy(program)
        program.endDate += datetime.timedelta(seconds=endOffset)
        
        secToFinishRecording = self.calculateTimeDifference(program.endDate, timeOffset = -5 )  #stop 5 sec earlier to release stream and allow recording of next program on that channel
        if secToFinishRecording <= 0:
            if sys.version_info[0] > 2:
                deb('RecordService not scheduling record for program {}, starting at {}, ending at {}, since it already finished'.format(program.title, program.startDate, program.endDate))
            else:
                deb('RecordService not scheduling record for program {}, starting at {}, ending at {}, since it already finished'.format(program.title.encode('utf-8'), program.startDate, program.endDate))
            return False
        else:
            if sys.version_info[0] > 2:
                deb('RecordService scheduling record for program {}, starting at {}, startOffset {}'.format(program.title, program.startDate, startOffset))
            else:
                deb('RecordService scheduling record for program {}, starting at {}, startOffset {}'.format(program.title.encode('utf-8'), program.startDate, startOffset))

        if self.rtmpdumpAvailable == False and self.ffmpegdumpAvailable == False:
            deb('DownloadService - no record application installed!')
            self.showThreadedDialog(failedRecordDialogName, "\n" + missingRecordBinaryString + ' RTMPDUMP & FFMPEG.')
            return False

        if not self.checkIfRecordDirExist():
            return False

        secToRecording = self.calculateTimeDifference(program.startDate, timeOffset = startOffset + 5 )
        if secToRecording < 0:
            secToRecording = delayRecording   #start now

        for element in self.getScheduledRecordingsForThisTime(program.startDate):
            if element.startOffset == startOffset:
                programList = element.programList    #Fetch already scheduled list of programs
                for prog in programList:
                    if program.channel == prog.channel and program.startDate == prog.startDate:
                        return False        #already on list
                programList.append(program) #add one more
                return True

        programList = list()
        programList.append(program)
        timer = threading.Timer(secToRecording, self.recordChannel, [program.startDate, startOffset])
        self.timers.append(RecordTimer(program.startDate, startOffset, timer, programList))
        timer.start()
        return True


    def recordChannel(self, startTime, startOffset):
        deb('RecordService recordChannel startTime {}, startOffset {}'.format(startTime, startOffset))
        for element in self.getScheduledRecordingsForThisTime(startTime):
            if element.startOffset == startOffset:
                programList = element.programList
                self.timers.remove(element)
                for program in programList:
                    urlList = self.epg.database.getStreamUrlList(program.channel)
                    threadData = {'urlList' : urlList, 'program' : program, 'recordHandle' : None, 'stopRecordTimer' : None, 'terminateThread' : False}
                    thread = threading.Thread(name='recordLoop', target = self.recordLoop, args=[threadData])
                    self.threadList.append([thread, threadData])
                    thread.start()


    def recordLoop(self, threadData):
        threadData['success']               = False
        threadData['notificationDisplayed'] = False
        threadData['destinationFile']       = os.path.join(self.recordDestinationPath, self.getOutputFilename(threadData['program']))
        threadData['partNumber']            = 1
        threadData['nrOfReattempts']        = 0
        threadData['recordOptions']         = { 'forceRTMPDump' : False, 'settingsChanged' : False, 'force_h264_mp4toannexb' : self.force_h264_mp4toannexb }
        threadData['recordDuration']        = self.calculateTimeDifference(threadData['program'].endDate, timeOffset = -5 )

        while self.checkIfRecordingShouldContinue(threadData):
            for url in threadData['urlList']:
                if not self.checkIfRecordingShouldContinue(threadData):
                    break

                threadData['recordOptions']['forceRTMPDump'] = False

                self.recordUrl(url, threadData)
                if threadData['recordOptions']['settingsChanged'] == True and self.checkIfRecordingShouldContinue(threadData):
                    deb('RecordService - detected settings change for recorded stream - retrying record')
                    self.recordUrl(url, threadData)

            #Go to sleep, maybe after that any service will be free to use
            for sleepTime in range(5):
                if not self.checkIfRecordingShouldContinue(threadData):
                    break
                time.sleep(1) 

        if sys.version_info[0] > 2:
            deb('RecordService - end of recording program: {}'.format(threadData['program'].title))
        else:
            deb('RecordService - end of recording program: {}'.format(threadData['program'].title).encode('utf-8'))

        self.showEndRecordNotification(threadData)

        if self.cleanupTimer is not None:
            self.cleanupTimer.cancel()
        self.cleanupTimer = threading.Timer(0.2, self.cleanupFinishedThreads)
        self.cleanupTimer.start()


    def recordUrl(self, url, threadData):
        threadData['recordOptions']['settingsChanged'] = False
        threadData['recordDuration'] = self.calculateTimeDifference(threadData['program'].endDate, timeOffset = -5 )

        if threadData['recordDuration'] <= 0:
            deb('RecordService - recordUrl ducation is 0, aborting record')
            return

        if self.recordingStopsPlayback and (xbmc.Player().isPlaying() or self.epg.playService.isWorking()):
            deb('RecordService - stopping ongoing playback')
            self.epg.playService.stopPlayback()
            xbmc.sleep(500)

        cid, service = self.parseUrl(url)
        channelInfo = self.getChannel(cid, service)

        if type(channelInfo) is tuple:
            channelInfo, LicenseUrl = channelInfo

            self.license = LicenseUrl

        if channelInfo is None:
            threadData['nrOfReattempts'] += 1
            deb('RecordService recordUrl - locked service {} - trying next, nrOfReattempts: {}, max: {}'.format(service, threadData['nrOfReattempts'], maxNrOfReattempts))
            return #go to next stream - this one seems to be locked

        self.findNextUnusedOutputFilename(threadData)
        
        if self.rtmpdumpAvailable and self.useOnlyFFmpeg == 'false' and (channelInfo.rtmpdumpLink is not None or (threadData['recordOptions']['forceRTMPDump'] == True and 'rtmp:' in channelInfo.strm) ):
            recordCommand = self.generateRTMPDumpCommand(channelInfo, threadData['recordDuration'], threadData['destinationFile'], threadData['recordOptions'])
        elif self.ffmpegdumpAvailable:
            recordCommand = self.generateFFMPEGCommand(channelInfo, threadData['recordDuration'], threadData['destinationFile'], threadData['recordOptions'])
        else:
            recordCommand = None
            deb('RecordService recordUrl ERROR, cant choose record application, self.rtmpdumpAvailable: {}, self.ffmpegdumpAvailable: {}, self.useOnlyFFmpeg: {}, channelInfo.rtmpdumpLink: {}, forceRTMPDump: {}, rtmpInUrl: {}'.format(self.rtmpdumpAvailable, self.ffmpegdumpAvailable, self.useOnlyFFmpeg, channelInfo.rtmpdumpLink, threadData['recordOptions']['forceRTMPDump'], 'rtmp:' in channelInfo.strm) )

        if recordCommand:
            self.showStartRecordNotification(threadData)
            output = self.record(recordCommand, threadData)
            self.postRecordActions(output, threadData)
        else:
            threadData['nrOfReattempts'] += 1

        self.unlockService(service)


    def record(self, recordCommand, threadData):
        deb('RecordService record command: {}'.format(str(recordCommand)))
        threadData['recordStartTime'] = datetime.datetime.now()
        output = ''
        si = None
        if os.name == 'nt':
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        recordEnviron = os.environ.copy()
        oldLdPath = recordEnviron.get("LD_LIBRARY_PATH", '')
        recordEnviron["LD_LIBRARY_PATH"] = os.path.join(os.path.dirname(recordCommand[0]), 'lib') + ':/lib:/usr/lib:/usr/local/lib'
        if oldLdPath != '':
            recordEnviron["LD_LIBRARY_PATH"] = recordEnviron["LD_LIBRARY_PATH"] + ":" + oldLdPath
        try:
            threadData['stopRecordTimer'] = threading.Timer(threadData['recordDuration'] + 5, self.stopRecord, [threadData])
            threadData['stopRecordTimer'].start()
            threadData['recordHandle'] = subprocess.Popen(recordCommand, shell=False, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=si, env=recordEnviron)
            output = threadData['recordHandle'].communicate()[0]
            returnCode = threadData['recordHandle'].returncode
            threadData['stopRecordTimer'].cancel()
            threadData['recordHandle'] = None
            deb('RecordService record finished, \noutput: {}, \nstatus: {}, Command: {}'.format(output, returnCode, str(recordCommand)))
        except Exception as ex:
            deb('RecordService record exception: {}'.format(getExceptionString()))

        return output


    def stopRecord(self, threadData, kill = False):
        if threadData['recordHandle'] is not None:
            try:
                threadData['recordHandle'].terminate()
                #if kill == True:
                    #threadData['recordHandle'].kill()
            except:
                pass


    def postRecordActions(self, recordOutput, threadData):
        self.analyzeRecordOutput(recordOutput, threadData['recordOptions'])
        recordedSecs = (datetime.datetime.now() - threadData['recordStartTime']).seconds
        if(threadData['recordDuration'] - recordedSecs < 60):
            if sys.version_info[0] > 2:
                deb('RecordService recordLoop successfully recored program: {}, started at: {}, ended at: {}, duration {}, now: {}'.format(threadData['program'].title, threadData['program'].startDate, threadData['program'].endDate, threadData['recordDuration'], datetime.datetime.now()))
            else:
                deb('RecordService recordLoop successfully recored program: {}, started at: {}, ended at: {}, duration {}, now: {}'.format(threadData['program'].title.encode('utf-8'), threadData['program'].startDate, threadData['program'].endDate, threadData['recordDuration'], datetime.datetime.now()))
            threadData['success'] = True
        else:
            if sys.version_info[0] > 2:
                deb('RecordService recordLoop ERROR: too short recording, got: {} sec, should be: {}, program: {}, start at: {}, end at: {}, nrOfReattempts: {}, max: {}'.format(recordedSecs, threadData['recordDuration'], threadData['program'].title, threadData['program'].startDate, threadData['program'].endDate, threadData['nrOfReattempts'], maxNrOfReattempts))
            else:
                deb('RecordService recordLoop ERROR: too short recording, got: {} sec, should be: {}, program: {}, start at: {}, end at: {}, nrOfReattempts: {}, max: {}'.format(recordedSecs, threadData['recordDuration'], threadData['program'].title.encode('utf-8'), threadData['program'].startDate, threadData['program'].endDate, threadData['nrOfReattempts'], maxNrOfReattempts))
            threadData['nrOfReattempts'] += 1
            if os.path.isfile(threadData['destinationFile']) and os.path.getsize(threadData['destinationFile']) < minRecordedFileSize: #Less than minimum, remove downloaded data
                try:
                    deb('RecordService recordLoop deleting incomplete record file {}, recorded for {} s, size {} KB'.format(threadData['destinationFile'], recordedSecs, os.path.getsize(threadData['destinationFile'])/1024))
                    os.remove(threadData['destinationFile'])
                except:
                    pass


    def analyzeRecordOutput(self, output, recordOptions):
        try:
            if 'Unrecognized option' in output:
                if 'copy_unknown' in output:
                    deb('RecordService detected problem with copy_unknown - disabling it!')
                    ADDON.setSetting(id="ffmpeg_dis_cop_un", value=str("true"))
                    if self.ffmpegDisableCopyUnknown == False:
                        recordOptions['settingsChanged'] = True
                        self.ffmpegDisableCopyUnknown = True

            if "Detected librtmp style URL parameters, these aren't supported" in output:
                deb('RecordService detected that stream needs to be recorded by RTMPdump')
                if recordOptions['forceRTMPDump'] == False:
                    recordOptions['settingsChanged'] = True
                    recordOptions['forceRTMPDump'] = True

            if "use -bsf h264_mp4toannexb" in output:
                deb('RecordService detected that stream needs to be encoded using h264_mp4toannexb')
                if recordOptions['force_h264_mp4toannexb'] == False:
                    recordOptions['settingsChanged'] = True
                    recordOptions['force_h264_mp4toannexb'] = True
        except:
            pass


    def calculateTimeDifference(self, programTime, timeOffset = 0):
        timeDiff = programTime - datetime.datetime.now()
        programDuration = ((timeDiff.days * 86400) + timeDiff.seconds) + timeOffset
        return programDuration


    def checkIfRecordingShouldContinue(self, threadData):
        return (threadData['success'] == False and threadData['recordDuration'] > 0 and threadData['nrOfReattempts'] <= maxNrOfReattempts and self.terminating == False and threadData['terminateThread'] == False and strings2.M_TVGUIDE_CLOSING == False)


    def generateRTMPDumpCommand(self, channelInfo, programDuration, destinationFile, recordOptions):
        recordCommand = list()
        recordCommand.append(self.rtmpdumpExe)

        if channelInfo.rtmpdumpLink:
            recordCommand.extend(channelInfo.rtmpdumpLink)
        else:
            recordCommand.append("-i")
            recordCommand.append("{}".format(channelInfo.strm))
        if os.name != 'nt':
            recordCommand.append("--realtime")
        recordCommand.append("--timeout")
        recordCommand.append("5")
        recordCommand.append("--hashes")
        recordCommand.append("--live")
        recordCommand.append("-B")
        recordCommand.append("{}".format(programDuration))
        recordCommand.append("-o")
        recordCommand.append(destinationFile)
        return recordCommand


    def generateFFMPEGCommand(self, channelInfo, programDuration, destinationFile, recordOptions):
        recordCommand = list()
        recordCommand.append(self.ffmpegdumpExe)

        if channelInfo.ffmpegdumpLink is not None:
            recordCommand.extend(channelInfo.ffmpegdumpLink)
        else:
            if 'cmore.se' in str(channelInfo.strm):
                streamSource = channelInfo.strm['manifestUrl']
            else:
                streamSource = channelInfo.strm

            coockieSeparator = streamSource.find('|')
            if coockieSeparator > 0:
                removedCoockie = streamSource[coockieSeparator+1:]
                streamSource = streamSource[:coockieSeparator]
                deb('RecordService - found coockie separator in record source! Remove this from URL: %s' % removedCoockie)

                headers = removedCoockie.split('&')
                newHeader = ""
                for header in headers:
                    deb('Got: {}'.format(header))
                    if 'User-Agent' in header:
                        newHeader = newHeader + "User-Agent: {}\r\n".format(serviceLib.HOST)
                    else:
                        newHeader = newHeader + "{}\r\n".format(header)

                recordCommand.append("-headers")
                recordCommand.append(newHeader)

            recordCommand.append("-probesize")
            recordCommand.append("50M")

            recordCommand.append("-analyzeduration")
            recordCommand.append("20M")

            recordCommand.append("-i")
            recordCommand.append("{}".format(streamSource))

        recordCommand.append("-c")
        recordCommand.append("copy")

        #recordCommand.append("-sn")  #Disable subtitles

        recordCommand.append("-map")
        recordCommand.append("0")

        if not self.ffmpegDisableCopyUnknown:
            recordCommand.append("-copy_unknown")

        recordCommand.append("-f")
        recordCommand.append("{}".format(self.ffmpegFormat))

        if recordOptions['force_h264_mp4toannexb']:
            recordCommand.append("-bsf")
            recordCommand.append("h264_mp4toannexb")

        recordCommand.append("-t")
        recordCommand.append("{}".format(programDuration))
        recordCommand.append("-loglevel")
        recordCommand.append("info")
        recordCommand.append("-n")
        recordCommand.append("{}".format(destinationFile))

        return recordCommand


    def showStartRecordNotification(self, threadData):
        if threadData['notificationDisplayed'] == False:
            if sys.version_info[0] > 2:
                xbmc.executebuiltin('Notification({},{},10000,{})'.format(recordNotificationName, self.normalizeString(threadData['program'].title), self.icon))
            else:
                xbmc.executebuiltin('Notification({},{},10000,{})'.format(recordNotificationName.encode('utf-8', 'replace'), self.normalizeString(threadData['program'].title), self.icon))

            threadData['notificationDisplayed'] = True #show only once


    def showEndRecordNotification(self, threadData):
        if threadData['notificationDisplayed'] == True:
            if sys.version_info[0] > 2:
                xbmc.executebuiltin('Notification({},{},10000,{})'.format(finishedRecordNotificationName, self.normalizeString(threadData['program'].title), self.icon))
            else:
                xbmc.executebuiltin('Notification({},{},10000,{})'.format(finishedRecordNotificationName.encode('utf-8', 'replace'), self.normalizeString(threadData['program'].title), self.icon))


    def close(self):
        deb('RecordService close')

        # Record
        self.terminating = True
        for element in self.timers[:]:
            element.timer.cancel()
        self.timers = list()

        for thread in self.threadList[:]:
            if thread[0].is_alive():
                self.stopRecord(thread[1], kill = True) #stop all recordings

        for thread in self.threadList[:]:
            if thread[0].is_alive():
                thread[0].join(30) #wait for threads to clean up
        self.threadList = list()
        if self.cleanupTimer is not None:
            self.cleanupTimer.cancel()

        # Download
        for element in self.timersdw[:]:
            element.timer.cancel()
        self.timersdw = list()

        for thread in self.threadDownloadList[:]:
            if thread[0].is_alive():
                self.stopDownload(thread[1], kill = True) #stop all downloads

        for thread in self.threadDownloadList[:]:
            if thread[0].is_alive():
                thread[0].join(30) #wait for threads to clean up
        self.threadDownloadList = list()
        if self.cleanupDownloadTimer is not None:
            self.cleanupDownloadTimer.cancel()


    def getScheduledRecordingsForThisTime(self, startDate):
        recordings = list()
        for element in self.timers:
            if element.startDate == startDate:
                debug('RecordService getScheduledRecordingsForThisTime found programs starting at %s, startOffset %s' % (startDate, element.startOffset))
                recordings.append(element)

        if len(recordings) == 0:
            debug('RecordService getScheduledRecordingsForThisTime no programs starting at %s' % startDate)
        return recordings

    def getScheduledDownloadingsForThisTime(self, startDate):
        recordings = list()
        for element in self.timersdw:
            if element.startDate == startDate:
                debug('DownloadService getScheduledDownloadingsForThisTime found programs starting at %s, startOffset %s' % (startDate, element.startOffset))
                recordings.append(element)

        if len(recordings) == 0:
            debug('DownloadService getScheduledDownloadingsForThisTime no programs starting at %s' % startDate)
        return recordings


    def normalizeString(self, text):
        import sys
        if sys.version_info[0] > 2:
            nkfd_form = unicodedata.normalize('NFKD', str(text))
            text = ("".join([c for c in nkfd_form if not unicodedata.combining(c)]))
        else:
            nkfd_form = unicodedata.normalize('NFKD', unicode(text))
            text = ("".join([c for c in nkfd_form if not unicodedata.combining(c)]))
        
        return re.compile('[^A-Za-z0-9_]+', re.IGNORECASE).sub('_', text)
        
    def getOutputFilename(self, program, partNumber = 0):
        filename = self.normalizeString(program.title) + "_" + str(program.startDate.strftime("%Y-%m-%d_%H-%M"))
        if partNumber > 1:
            filename = filename + "_part_%d" % partNumber
        return filename + ".mpeg"


    def findNextUnusedOutputFilename(self, threadData):
        while os.path.isfile(threadData['destinationFile']): #Generate output filename which is not used
            threadData['partNumber'] += 1
            outputFileName = self.getOutputFilename(threadData['program'], threadData['partNumber'])
            threadData['destinationFile'] = os.path.join(self.recordDestinationPath, outputFileName)

    def getListOfFilenamesForProgram(self, program):
        #debug('getListOfFilenamesForProgram')
        filenameList = list()
        filename = self.getOutputFilename(program)
        filePath = os.path.join(self.recordDestinationPath, filename)
        partNumber = 1
        while os.path.isfile(filePath):
            filenameList.append(filePath)
            partNumber = partNumber + 1
            filename = self.getOutputFilename(program, partNumber)
            filePath = os.path.join(self.recordDestinationPath, filename)
        return filenameList


    def isProgramRecorded(self, program):
        #if sys.version_info[0] > 2:
            #debug('RecordService isProgramRecorded program: %s' % program.title)
        #else:
            #debug('RecordService isProgramRecorded program: %s' % program.title.encode('utf-8'))
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        filenameList = self.getListOfFilenamesForProgram(program)
        for filename in filenameList:
            playlist.add(url=filename)
        if playlist.size() > 0:
            return playlist
        return None


    def isProgramRecordScheduled(self, program):
        if program is None:
            return False
        for element in self.getScheduledRecordingsForThisTime(program.startDate):
            programList = element.programList
            for prog in programList:
                if program.channel == prog.channel:
                    return True

        for thread in self.threadList:
            if not thread[0].is_alive():
                continue
            threadData = thread[1]
            prog = threadData['program'] #program recorded by this thread
            if program.channel == prog.channel and program.startDate == prog.startDate:
                return True
        return False


    def isProgramDownloadScheduled(self, program):
        if program is None:
            return False
        for element in self.getScheduledDownloadingsForThisTime(program.startDate):
            programList = element.programList
            for prog in programList:
                if program.channel == prog.channel:
                    return True

        for thread in self.threadDownloadList:
            if not thread[0].is_alive():
                continue
            threadData = thread[1]
            prog = threadData['program'] #program recorded by this thread
            if program.channel == prog.channel and program.startDate == prog.startDate:
                return True
        return False


    def cancelProgramRecord(self, program): #wylaczyc akturalnie nagrywany program?
        for element in self.getScheduledRecordingsForThisTime(program.startDate):
            programList = element.programList
            try:
                for prog in programList:
                    if program.channel == prog.channel:
                        programList.remove(prog)
                        if len(programList) == 0:
                            element.timer.cancel()
                            self.timers.remove(element)
                        if sys.version_info[0] > 2:
                            deb('RecordService canceled scheduled recording of: {}'.format(program.title))
                        else:
                            deb('RecordService canceled scheduled recording of: {}'.format(program.title.encode('utf-8')))
                        return
            except:
                pass

        for thread in self.threadList:
            if not thread[0].is_alive():
                continue
            threadData = thread[1]
            prog = threadData['program']
            if program.channel == prog.channel and program.startDate == prog.startDate:
                threadData['terminateThread'] = True
                self.stopRecord(threadData)
                if sys.version_info[0] > 2:
                    deb('RecordService canceled ongoing recording of: {}'.format(program.title))
                else:
                    deb('RecordService canceled ongoing recording of: {}'.format(program.title.encode('utf-8')))
                return

    def cancelProgramDownload(self, program): #wylaczyc akturalnie nagrywany program?
        for element in self.getScheduledDownloadingsForThisTime(program.startDate):
            programList = element.programList
            try:
                for prog in programList:
                    if program.channel == prog.channel:
                        programList.remove(prog)
                        if len(programList) == 0:
                            element.timer.cancel()
                            self.timersdw.remove(element)
                        if sys.version_info[0] > 2:
                            deb('DownloadService canceled scheduled downloading of: {}'.format(program.title))
                        else:
                            deb('DownloadService canceled scheduled downloading of: {}'.format(program.title.encode('utf-8')))
                        return
            except:
                pass

        for thread in self.threadDownloadList:
            if not thread[0].is_alive():
                continue
            threadData = thread[1]
            prog = threadData['program']
            if program.channel == prog.channel and program.startDate == prog.startDate:
                threadData['terminateDownloadThread'] = True
                self.stopDownload(threadData)
                if sys.version_info[0] > 2:
                    deb('DownloadService canceled ongoing downloading of: {}'.format(program.title))
                else:
                    deb('DownloadService canceled ongoing downloading of: {}'.format(program.title.encode('utf-8')))
                return


    def cleanupFinishedThreads(self):
        for thread in self.threadList[:]:
            try:
                if not thread[0].is_alive():
                    self.threadList.remove(thread)
            except:
                pass


    def cleanupFinishedDownloadThreads(self):
        for thread in self.threadDownloadList[:]:
            try:
                if not self.downloading:
                    self.threadDownloadList.remove(thread)
            except:
                pass


    def isRecordOngoing(self):
        for thread in self.threadList:
            if thread[0].is_alive():
                return True
        return False


    def isDownloadOngoing(self):
        if self.downloading:
            return True
        return False


    def isRecordScheduled(self):
        if len(self.timers) > 0:
            return True
        return False


    def removeRecordedProgram(self, program):
        debug('removeRecordedProgram')
        if program is None:
            deb('removeRecordedProgram got faulty program!!!!')

        filenameList = self.getListOfFilenamesForProgram(program)

        for filename in filenameList:
            try:
                os.remove(filename)
                debug('removeRecordedProgram removing %s' % filename)
            except Exception as ex:
                deb('removeRecordedProgram exception: %s' % getExceptionString())

    def checkIfRecordDirExist(self):
        if self.recordDestinationPath == '':
            deb('checkIfRecordDirExist record destination not configured!')
            self.showThreadedDialog(failedRecordDialogName, "\n" + nonExistingRecordDirName)
            return False
        elif os.path.isdir(self.recordDestinationPath) == False:
            try:
                os.makedirs(self.recordDestinationPath)
                #make sure dir was created
                if os.path.isdir(self.recordDestinationPath) == False:
                    deb('checkIfRecordDirExist record destination does not exist after attmept to create! path: {}'.format(self.recordDestinationPath))
                    self.showThreadedDialog(failedRecordDialogName, "\n" + nonExistingRecordDirName + "\n" + self.recordDestinationPath)
                    return False
            except:
                deb('checkIfRecordDirExist record destination does not exist and cannot be created! path: {}'.format(self.recordDestinationPath))
                self.showThreadedDialog(failedRecordDialogName, "\n" + nonExistingRecordDirName + "\n" + self.recordDestinationPath)
                return False
        else:
            return True

    def checkIfDownloadDirExist(self):
        if self.recordDestinationPath == '':
            deb('checkIfDownloadDirExist download destination not configured!')
            self.showThreadedDialog(failedDownloadDialogName, "\n" + nonExistingRecordDirName)
            return False
        elif os.path.isdir(self.recordDestinationPath) == False:
            try:
                os.makedirs(self.recordDestinationPath)
                #make sure dir was created
                if os.path.isdir(self.recordDestinationPath) == False:
                    deb('checkIfDownloadDirExist download destination does not exist after attmept to create! path: {}'.format(self.recordDestinationPath))
                    self.showThreadedDialog(failedRecordDialogName, "\n" + nonExistingRecordDirName + "\n" + self.recordDestinationPath)
                    return False
            except:
                deb('checkIfDownloadDirExist download destination does not exist and cannot be created! path: {}'.format(self.recordDestinationPath))
                self.showThreadedDialog(failedRecordDialogName, "\n" + nonExistingRecordDirName + "\n" + self.recordDestinationPath)
                return False
        else:
            return True

    def showThreadedDialog(self, dialogName, dialogMessage):
        try:
            threading.Timer(0, self.showDialog, [dialogName, dialogMessage]).start()
        except:
            pass

    def showDialog(self, dialogName, dialogMessage):
        xbmcgui.Dialog().ok(dialogName, dialogMessage)


class DownloadMenu(xbmcgui.WindowXMLDialog):
    def __new__(cls, program):
        return super(DownloadMenu, cls).__new__(cls, 'script-tvguide-download.xml', Skin.getSkinBasePath(), Skin.getSkinName(), skin_resolution)

    def __init__(self, program):
        self.startDateId = 401
        self.endDateId = 402

        self.startTimeId = 403
        self.endTimeId = 404

        self.saveControlId = 301
        self.cancelControlId = 302
        self.resetControlId = 303

        self.programTitleId = 201
        self.channelId = 202

        self.downloadDurationId = 204

        self.dwnl = False
        self.chkdate = True
        self.program = program

        self.calculatedStartDate = self.program.startDate
        self.calculatedEndDate = self.program.endDate
        super(DownloadMenu, self).__init__()

    def onInit(self): 
        self.downloadDuration = self.getControl(self.downloadDurationId)

        if sys.version_info[0] > 2:
            channel = self.program.channel.title
            title = self.program.title
        else:
            channel = self.program.channel.title.encode('utf-8')
            title = self.program.title.encode('utf-8')

        self.getControl(self.programTitleId).setLabel(channel)

        self.channelId = self.getControl(self.channelId)
        self.channelId.setLabel(strings(70000))
        self.channelId.setText(title)

        startDate = str(self.program.startDate).split(' ')[0]
        endDate = str(self.program.endDate).split(' ')[0]

        startTime = str(self.program.startDate).split(' ')[1]
        endTime = str(self.program.endDate).split(' ')[1]

        self.startDate = self.getControl(self.startDateId)
        self.startDate.setType(xbmcgui.INPUT_TYPE_DATE, strings(70024))
        self.startDate.setLabel(strings(70024))
        self.startDate.setText(str(startDate))

        self.endDate = self.getControl(self.endDateId)
        self.endDate.setType(xbmcgui.INPUT_TYPE_DATE, strings(70025))
        self.endDate.setLabel(strings(70025))
        self.endDate.setText(str(endDate))

        self.startTime = self.getControl(self.startTimeId)
        self.startTime.setType(xbmcgui.INPUT_TYPE_SECONDS, strings(70002))
        self.startTime.setLabel(strings(70002))
        self.startTime.setText(str(startTime))

        self.endTime = self.getControl(self.endTimeId)
        self.endTime.setType(xbmcgui.INPUT_TYPE_SECONDS, strings(70023))
        self.endTime.setLabel(strings(70023))
        self.endTime.setText(str(endTime))

        self.updateLabels()

    def updateLabels(self):
        self.calculatedStartDate = self.program.startDate + datetime.timedelta(minutes=0)
        self.calculatedEndDate = self.program.endDate + datetime.timedelta(minutes=0)

        try:
            if self.calculatedEndDate > self.calculatedStartDate:
                self.downloadDuration.setLabel('{}'.format(self.calculatedEndDate - self.calculatedStartDate))
            else:
                self.downloadDuration.setLabel('{}'.format(0))
        except:
            pass

    def getOffsets(self):
        if self.calculatedStartDate > self.calculatedEndDate:
            self.dwnl = False
        elif self.calculatedEndDate > datetime.datetime.now():
            self.dwnl = False
            self.chkdate = False
        return [self.dwnl, self.chkdate, 0, 0]

    def getStartDate(self, date, time):
        startDate = str(self.program.startDate).split(' ')[0]
        startTime = str(self.program.startDate).split(' ')[1]

        try:
            try:
                strdate = '{} {}'.format(startDate, time)
                self.program.startDate = proxydt.strptime(str(strdate), '%Y-%m-%d %H:%M:%S')
            except:
                strdate = '{} {}'.format(date, startTime)
                self.program.startDate = proxydt.strptime(str(strdate), '%Y-%m-%d %H:%M:%S')
        except:
            self.program.startDate

    def getEndDate(self, date, time):
        endDate = str(self.program.endDate).split(' ')[0]
        endTime = str(self.program.endDate).split(' ')[1]

        try:
            try:
                strdate = '{} {}'.format(endDate, time)
                self.program.endDate = proxydt.strptime(str(strdate), '%Y-%m-%d %H:%M:%S')
            except:
                strdate = '{} {}'.format(date, endTime)
                self.program.endDate = proxydt.strptime(str(strdate), '%Y-%m-%d %H:%M:%S')
        except:
            self.program.endDate


    def onAction(self, action):
        if action.getId() in [ACTION_PREVIOUS_MENU, KEY_NAV_BACK, ACTION_PARENT_DIR, 101]:
            deb('DownloadMenu got action close!')
            self.close()
        else:
            self.updateLabels()

    def onClick(self, controlId):
        if controlId == self.channelId.getId():
            self.program.title = self.channelId.getText()
            self.updateLabels()

        elif controlId == self.startDateId :
            startDate = self.startDate.getText()
            self.getStartDate(startDate, None)
            self.updateLabels()

        elif controlId == self.startTimeId:
            startTime = self.startTime.getText()
            self.getStartDate(None, startTime)
            self.updateLabels()

        elif controlId == self.endDateId:
            endDate = self.endDate.getText()
            self.getEndDate(endDate, None)
            self.updateLabels()

        elif controlId == self.endTimeId:
            endTime = self.endTime.getText()
            self.getEndDate(None, endTime)
            self.updateLabels()

        elif controlId == self.cancelControlId:
            self.close()

        elif controlId == self.saveControlId:
            self.dwnl = True
            self.chkdate = True
            self.close()

        else:
            self.updateLabels()

class RecordMenu(xbmcgui.WindowXMLDialog):
    def __new__(cls, program):
        return super(RecordMenu, cls).__new__(cls, 'script-tvguide-record.xml', Skin.getSkinBasePath(), Skin.getSkinName(), skin_resolution)

    def __init__(self, program):
        self.startOffsetLabelId = 501
        self.endOffsetLabelId = 502

        self.startOffsetSliderId = 401
        self.endOffsetSliderId = 402

        self.saveControlId = 301
        self.cancelControlId = 302
        self.resetControlId = 303

        self.startOffsetValue = 0
        self.endOffsetValue = 0

        self.programTitleId = 201
        self.channelId = 202
        self.startHourId = 203
        self.recordDurationId = 204

        self.record = False
        self.program = program

        self.calculatedStartDate = self.program.startDate
        self.calculatedEndDate = self.program.endDate
        super(RecordMenu, self).__init__()

    def onInit(self): 
        self.startOffsetLabel = self.getControl(self.startOffsetLabelId)
        self.endOffsetLabel = self.getControl(self.endOffsetLabelId)

        self.startOffsetSlider = self.getControl(self.startOffsetSliderId)
        self.endOffsetSlider = self.getControl(self.endOffsetSliderId)

        self.startHour = self.getControl(self.startHourId)
        self.recordDuration = self.getControl(self.recordDurationId)

        if sys.version_info[0] > 2:
            self.getControl(self.programTitleId).setLabel('{}'.format(self.program.title))
            self.getControl(self.channelId).setLabel('{}'.format(self.program.channel.title))
        else:
            self.getControl(self.programTitleId).setLabel('{}'.format(self.program.title.encode('utf-8')))
            self.getControl(self.channelId).setLabel('{}'.format(self.program.channel.title.encode('utf-8')))

        self.resetSliders()

    def resetSliders(self):
        self.startOffsetSlider.setPercent(50)
        self.endOffsetSlider.setPercent(50)
        self.updateLabels()

    def updateLabels(self):
        self.startOffsetValue = int(self.startOffsetSlider.getPercent() - 50)
        self.endOffsetValue = int(self.endOffsetSlider.getPercent() - 50)

        self.startOffsetLabel.setLabel('{}'.format(self.startOffsetValue))
        self.endOffsetLabel.setLabel('{}'.format(self.endOffsetValue))

        self.calculatedStartDate = self.program.startDate + datetime.timedelta(minutes=self.startOffsetValue)
        self.calculatedEndDate = self.program.endDate + datetime.timedelta(minutes=self.endOffsetValue)

        self.startHour.setLabel('{}'.format(self.calculatedStartDate))

        if self.calculatedEndDate > self.calculatedStartDate:
            self.recordDuration.setLabel('{}'.format(self.calculatedEndDate - self.calculatedStartDate))
        else:
            self.recordDuration.setLabel('{}'.format(0))

    def getOffsets(self):
        if self.calculatedStartDate > self.calculatedEndDate:
            self.record = False
        return [self.record, self.startOffsetValue, self.endOffsetValue]

    def onAction(self, action):
        if action.getId() in [ACTION_PREVIOUS_MENU, KEY_NAV_BACK, ACTION_PARENT_DIR, 101]:
            deb('RecordMenu got action close!')
            self.close()
        else:
            self.updateLabels()

    def onClick(self, controlId):
        if controlId == self.cancelControlId:
            self.close()
        elif controlId == self.resetControlId:
            self.resetSliders()
        elif controlId == self.saveControlId:
            self.record = True
            self.close()
        

        
        
            