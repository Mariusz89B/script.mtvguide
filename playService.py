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

from __future__ import unicode_literals

import sys

if sys.version_info[0] > 2:
    import urllib.request, urllib.parse, urllib.error
    import urllib.request as Request
    from urllib.error import HTTPError, URLError
else:
    import urllib
    import urllib2 as Request
    from urllib2 import HTTPError, URLError 

try:
    from urllib.parse import urlencode, quote_plus, quote, unquote
except ImportError:
    from urllib import urlencode, quote_plus, quote, unquote

if sys.version_info[0] > 2:
    from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
else:
    from requests import HTTPError, ConnectionError, Timeout, RequestException

import six
import uuid
import json

import ssl
import socket

import datetime, threading, sys, os, re
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, xbmcvfs
from strings import *
import strings as strings2
import serviceLib
import requests
import time
import threading
import cloudscraper 

from contextlib import contextmanager

import playlistcids
import cmorecids
#import francetvcids
import iplacids
import ncplusgocids
import playerplcids
import polsatgocids
import polsatgoboxcids
import teliaplaycids
import tvpcids
import wppilotcids

sess = cloudscraper.create_scraper()
scraper = cloudscraper.CloudScraper()

SERVICES = {
    playlistcids.serviceName + '_1' : playlistcids.PlaylistUpdater(instance_number=1),
    playlistcids.serviceName + '_2' : playlistcids.PlaylistUpdater(instance_number=2),
    playlistcids.serviceName + '_3' : playlistcids.PlaylistUpdater(instance_number=3),
    playlistcids.serviceName + '_4' : playlistcids.PlaylistUpdater(instance_number=4),
    playlistcids.serviceName + '_5' : playlistcids.PlaylistUpdater(instance_number=5),
    cmorecids.serviceName           : cmorecids.CmoreUpdater(),
    #francetvcids.serviceName        : francetvcids.FranceTVUpdater(),
    iplacids.serviceName            : iplacids.IplaUpdater(),
    ncplusgocids.serviceName        : ncplusgocids.NcPlusGoUpdater(),
    playerplcids.serviceName        : playerplcids.PlayerPLUpdater(),
    polsatgocids.serviceName        : polsatgocids.PolsatGoUpdater(),
    polsatgoboxcids.serviceName     : polsatgoboxcids.PolsatGoBoxUpdater(),
    teliaplaycids.serviceName       : teliaplaycids.TeliaPlayUpdater(),
    tvpcids.serviceName             : tvpcids.TvpUpdater(),
    wppilotcids.serviceName         : wppilotcids.WpPilotUpdater()
}

for serviceName in list(SERVICES.keys()):
    if SERVICES[serviceName].serviceEnabled != 'true':
        SERVICES[serviceName].close()
        del SERVICES[serviceName]

class BasePlayService:
    lockMap = {}
    maxAllowedStreams = {}
    lock = threading.Lock()
    for service in SERVICES:
        lockMap[service] = 0
        maxAllowedStreams[service] = SERVICES[service].maxAllowedStreams

    def __init__(self):
        self.thread = None
        self.terminating = False
        self.starting = False

    def parseUrl(self, url):
        cid = 0
        service = None
        try:
            params = url[8:].split('&')
            service = params[0]
            cid = params[1].split('=')[1]
            deb(self.__class__.__name__ + ' parseUrl: cid {}, service {}'.format(cid, service))
        except:
            pass
        return [cid, service]

    def isWorking(self):
        if self.thread is not None:
            return self.thread.is_alive() or self.starting
        return False

    def getChannel(self, cid, service, currentlyPlayedService = { 'service' : None }):
        BasePlayService.lock.acquire() # make this function thread safe
        channelInfo = None
        if self.isServiceLocked(service) == True and service != currentlyPlayedService['service']: #if issued by PlayService and it's the same as played then allow using the same service - it will be release anyway
            deb(self.__class__.__name__ + ' getChannel service {} is locked - aborting'.format(service))
            BasePlayService.lock.release()
            return None
        try:
            serviceHandler = SERVICES[service]
        except KeyError:
            serviceHandler = None

        if serviceHandler is not None:
            channelInfo = serviceHandler.getChannel(cid)

        if channelInfo is not None and service != currentlyPlayedService['service']:
            self.lockService(service)
        BasePlayService.lock.release()
        return channelInfo

    def getChannelDownload(self, cid, service, currentlyPlayedService = { 'service' : None }):
        channelInfo = None

        try:
            serviceHandler = SERVICES[service]
        except KeyError:
            serviceHandler = None

        if serviceHandler is not None:
            channelInfo = serviceHandler.getChannel(cid)

        return channelInfo

    def lockService(self, service):
        try:
            BasePlayService.lockMap[service] = BasePlayService.lockMap[service] + 1
            deb(self.__class__.__name__ + ' lockService: {} streams handled by service: {}, max is: {}'.format(BasePlayService.lockMap[service], service, BasePlayService.maxAllowedStreams[service]))
        except:
            pass

    def unlockService(self, service):
        try:
            if service:
                BasePlayService.lockMap[service] = BasePlayService.lockMap[service] - 1
                SERVICES[service].unlockService()
                deb(self.__class__.__name__ + ' unlockService: still {} streams handled by service: {}, max is: {}'.format(BasePlayService.lockMap[service], service, BasePlayService.maxAllowedStreams[service]))
                if BasePlayService.lockMap[service] < 0:
                    deb(self.__class__.__name__ + ' error while unlocking service, nr less than 0, something went wrong!')
                    raise
        except:
            pass

    def isServiceLocked(self, service):
        try:
            if BasePlayService.lockMap[service] >= BasePlayService.maxAllowedStreams[service]:
                return True
        except:
            pass
        return False

class PlayService(xbmc.Player, BasePlayService):
    def __init__(self, *args, **kwargs):
        BasePlayService.__init__(self)
        self.playbackStopped        = False
        self.playbackStarted        = False
        self.currentlyPlayedService = { 'service' : None }
        self.urlList                = None
        self.playbackStartTime      = None
        self.sleepSupervisor        = serviceLib.SleepSupervisor(self.stopPlayback)
        self.streamQuality          = ''
        self.userStoppedPlayback    = True
        self.nrOfResumeAttempts     = 0
        self.threadData             = { 'terminate' : False }
        self.maxNrOfResumeAttempts  = int(ADDON.getSetting('max_reconnect_attempts'))
        self.reconnectDelay         = int(ADDON.getSetting('reconnect_delay'))
        self.reconnectFailedStreams = ADDON.getSetting('reconnect_stream')
        self.maxStreamStartupTime   = int(ADDON.getSetting('max_wait_for_playback')) * 10
        self.strmUrl                = None
        self.service                = None
        

    def playUrlList(self, urlList, archiveService, archivePlaylist, resetReconnectCounter=False):
        self.archiveService = archiveService
        self.archivePlaylist = archivePlaylist
        if urlList is None or len(urlList) == 0:
            deb('playUrlList got empty list to play - aborting!')
            self.starting = False
            return
        self.starting = True
        self.threadData['terminate'] = True
        currentThreadData = self.threadData = { 'terminate' : False }
        if resetReconnectCounter:
            self.nrOfResumeAttempts = 0

        if self.thread is not None and self.thread.is_alive():
            deb('PlayService playUrlList waiting for thread to terminate')
            self.terminating = True
            while self.thread is not None and self.thread.is_alive() and currentThreadData['terminate'] == False:
                xbmc.sleep(100)

        if currentThreadData['terminate'] == True:
            deb('playUrlList decided to terminate thread starting playback')
            return

        self.thread = threading.Thread(name='playUrlList Loop', target = self._playUrlList, args=[urlList])
        self.thread.start()
        self.starting = False

    def _playUrlList(self, urlList):
        self.terminating = False
        self.urlList = list(urlList)
        self.userStoppedPlayback = False

        for url in self.urlList[:]:

            if self.userStoppedPlayback or self.terminating or strings2.M_TVGUIDE_CLOSING:
                deb('_playUrlList aborting loop, self.userStoppedPlayback: {}, self.terminating: {}'.format(self.userStoppedPlayback, self.terminating))
                return

            playStarted, customPlugin = self.playUrl(url)

            if playStarted is None:
                return

            if not playStarted:
                deb('_playUrlList playback not started - checking next stream')

            else:
                time.sleep(1)
                
                if customPlugin:
                    waitTime = self.maxStreamStartupTime + 30
                else:
                    waitTime = self.maxStreamStartupTime

                start_date = datetime.datetime.now()
                for i in range(waitTime):
                    if self.terminating == True or strings2.M_TVGUIDE_CLOSING == True or self.userStoppedPlayback:
                        if strings2.M_TVGUIDE_CLOSING == True:
                            self.userStoppedPlayback = True
                            xbmc.Player().stop()
                        self.unlockCurrentlyPlayedService()
                        deb('PlayService _playUrlList abort requested - terminating')
                        return

                    if self.playbackStarted == True:
                        deb('PlayService _playUrlList detected stream start!')
                        self.playbackStartTime = datetime.datetime.now()
                        return

                    if self.playbackStopped == True or playStarted == False:
                        break

                    if i == (waitTime - 1):
                        deb('PlayService _playUrlList maximum wait time ({}) for stream start exceeded! Time since starting stream: {}'.format(waitTime, (datetime.datetime.now() - start_date).seconds))
                    xbmc.sleep(100)

                deb('PlayService _playUrlList detected faulty stream! playbackStopped: {}, playStarted: {}'.format(self.playbackStopped, playStarted) )
                self.unlockCurrentlyPlayedService()
                xbmc.Player().stop()

            try:
                #move stream to the end of list
                if url is not None:
                    self.urlList.remove(url)
                    self.urlList.append(url)
            except Exception as ex:
                deb('_playUrlList exception: {}'.format(getExceptionString()))

        deb('PlayService _playUrlList non of streams started - stopping playback!')
        
        self.userStoppedPlayback = True
        xbmc.Player().stop()

    def playUrl(self, url):
        self.playbackStopped = False
        self.playbackStarted = False
        self.streamQuality = ''
        success = True
        customPlugin = False

        if url[-5:] == '.strm':
            try:
                f = open(url)
                content = f.read()
                f.close()
                if content[0:9] == 'plugin://':
                    url = content.strip()
            except:
                pass

        if url[0:9] == 'plugin://':
            self.unlockCurrentlyPlayedService()
            if ADDON.getSetting('start_video_minimalized') == 'true':
                xbmc.executebuiltin('PlayMedia({}, false, 1)'.format(url))
            else:
                xbmc.executebuiltin('PlayMedia({})'.format(url))
            customPlugin = True
        elif url[0:7] == 'service':
            cid, service = self.parseUrl(url)
            success = self.LoadVideoLink(cid, service, url)
            if success:
                self.getStreamQualityFromCid(cid)
        else:
            self.unlockCurrentlyPlayedService()
            xbmc.Player().play(url)

        return [success, customPlugin]

    def playNextStream(self):
        if self.urlList and len(self.urlList) > 1:
            tmpUrl = self.urlList.pop(0)
            self.urlList.append(tmpUrl)
            debug('PlayService playNextStream skipping: {}, next: {}'.format(tmpUrl, self.urlList[0]))
            self.playUrlList(self.urlList, self.archiveService, self.archivePlaylist)

    def archiveService(self):
        archiveStr = self.archiveService
        return archiveStr

    def playlistArchive(self):
        archiveStr = self.archivePlaylist
        return archiveStr

    def deleteSession(self, url, headers):
        # Wait for player to start playing. This is not exactly bulletproof...
        xbmc.sleep(2000)
        # we need to send a delete request to close the session after playback stops
        while xbmc.Player().isPlaying():
            xbmc.sleep(300)
            #deb('looping while playing')

        response = sess.delete(url, headers=headers)

    def getUrl(self, strmUrl, cid, service, retry=False):
        mimeType = ''

        status = 200

        UA = ADDON.getSetting('{}_user_agent'.format(service))

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }

        if UA:
            headers.update({'User-Agent': UA})
        
            conn_timeout = int(ADDON.getSetting('max_wait_for_playback'))
            read_timeout = int(ADDON.getSetting('max_wait_for_playback'))
            timeouts = (conn_timeout, read_timeout)

            try:
                response = scraper.get(strmUrl, headers=headers, allow_redirects=False, stream=True, timeout=timeouts)
                if 'Location' in response.headers and '_TS' not in cid:
                    strmUrl = response.headers.get('Location', None) 

                else:
                    strmUrl = response.url

                status = response.status_code

            except HTTPError as e:
                status = 400
                deb('HTTPError: {}'.format(str(e)))

            except ConnectionError as e:
                status = 400
                deb('ConnectionError: {}'.format(str(e)))

            except Timeout as e:
                status = 400
                deb('Timeout: {}'.format(str(e))) 

            except RequestException as e:
                status = 400
                deb('RequestException: {}'.format(str(e))) 

        if status >= 400 and not retry:
            retry = True
            self.getUrl(strmUrl, cid, service, retry)

        if retry:
            return None

        return strmUrl


    def channCid(self, cid):
        try:
            r = re.compile('^(.*?)_TS_.*$', re.IGNORECASE)
            cid = r.findall(cid)[0]
        except:
            cid 

        return cid


    def catchupTeliaPlay(self, channelInfo, utc, lutc):
        base = ['https://teliatv.dk', 'https://www.teliaplay.se']
        classic = ['https://teliatv.dk', 'https://classic.teliaplay.se']

        host = ['www.teliatv.dk', 'www.teliaplay.se']
        hclassic = ['www.teliatv.dk', 'classic.teliaplay.se']

        cc = ['dk', 'se']

        country            = int(ADDON.getSetting('teliaplay_locale'))
        
        dashjs             = ADDON.getSetting('teliaplay_devush')
        beartoken          = ADDON.getSetting('teliaplay_beartoken')
        tv_client_boot_id  = ADDON.getSetting('teliaplay_tv_client_boot_id')
        usern              = ADDON.getSetting('teliaplay_usern')
        sessionid          = ADDON.getSetting('teliaplay_sess_id')

        UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36 Edg/89.0.774.63'

        utc = str(int(utc) * 1000 + 1000)
        lutc = str(int(lutc) * 1000)

        n = datetime.datetime.now()

        if sys.version_info[0] > 2:
            now = int(time.mktime(n.timetuple())) * 1000
            tday = str(((int(time.time() // 86400)) * 86400) * 1000)
            yday = str(((int(time.time() // 86400)) * 86400 - 86400 ) * 1000)
        else:
            now = int(time.mktime(n.timetuple())) * 1000
            tday = str(((int(time.mktime(n.timetuple()) // 86400)) * 86400) * 1000)
            yday = str(((int(time.mktime(n.timetuple()) // 86400)) * 86400 - 86400 ) * 1000)

        if int(utc) < int(tday):
            timestamp = yday
        else:
            timestamp = tday

        headers = {
            'Authority': 'graphql-telia.t6a.net',
            'tv-client-name': 'web',
            'tv-client-boot-id': tv_client_boot_id,
            'DNT': '1',
            'sec-ch-ua-mobile': '?0',
            'Authorization': 'Bearer '+ beartoken,
            'Content-Type': 'application/json',
            'X-Country': cc[country],
            'User-Agent': UA,
            'tv-client-version': '1.2.0',
            'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Microsoft Edge";v="92"',
            'Accept': '*/*',
            'Origin': base[country],
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': base[country]+'/',
            'Accept-Language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6',
        }

        params = (
            ('operationName', 'getTvChannel'),
            ('variables', '{"timestamp":'+timestamp+',"offset":0,"id":"'+str(self.channCid(channelInfo.cid))+'"}'),
            ('extensions', '{"persistedQuery":{"version":1,"sha256Hash":"6760f09a1fde5f410dc80906db28789631cc8c8b4887ff0c24ed76ff25eca71a"}}'),
        )

        response = requests.get('https://graphql-telia.t6a.net/graphql', headers=headers, params=params, cookies=sess.cookies, verify=False).json()

        media_id = ''
        watch_mode = ''

        programItems = response['data']['channel']['programs']['programItems']
        for item in programItems:
            start_time = item['startTime']['timestamp']
            end_time = item['endTime']['timestamp']
            if int(utc) >= int(start_time) and int(utc) <= int(end_time):
                media_id = item['media']['id']
                title = item['media']['title']

                if sys.version_info[0] > 2:
                    p = re.compile('\WwatchMode\W:\s*\W(.*?)\W,', re.M)
                else:
                    p = re.compile('\WwatchMode\W:\s*\W(.*?)\W},', re.M)

                watch_modes = p.findall(json.dumps(item['media']['playback']['play']))

                if ('ONDEMAND' in watch_modes or 'STARTOVER' in watch_modes) and media_id != '':
                    streamType = 'MEDIA'

                else:
                    res = xbmcgui.Dialog().yesno(strings(30998), strings(59980))
                    if res:
                        media_id = self.channCid(channelInfo.cid)
                        streamType = 'CHANNEL'
                    else:
                        return None, None

        catchupType = 'ONDEMAND'
        if int(end_time) > int(now):
            catchupType = 'STARTOVER'

        url = 'https://streaminggateway-telia.clientapi-prod.live.tv.telia.net/streaminggateway/rest/secure/v2/streamingticket/{type}/{cid}?country={cc}'.format(type=streamType, cid=(str(media_id)), cc=cc[country].upper())

        headers = {
            'Connection': 'keep-alive',
            'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Microsoft Edge";v="92"',
            'tv-client-boot-id': tv_client_boot_id,
            'DNT': '1',
            'sec-ch-ua-mobile': '?0',
            'Authorization': 'Bearer '+ beartoken,
            'Content-Type': 'application/json',
            'X-Country': cc[country],
            'User-Agent': UA,
            'Accept': '*/*',
            'Origin': base[country],
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': base[country]+'/',
            'Accept-Language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6',
        }

        params = (
            ('country', cc[country].upper()),
        )

        data = {
            "sessionId": six.text_type(uuid.uuid4()),
            "whiteLabelBrand":"TELIA",
            "watchMode": catchupType,
            "accessControl":"SUBSCRIPTION",
            "device": {
                "deviceId": tv_client_boot_id,
                "category":"unknown",
                "packagings":["DASH_MP4_CTR"],
                "drmType":"WIDEVINE",
                "capabilities":[],
                "screen": {
                    "height":1080,
                    "width":1920
                    },
                "model":"windows_desktop"
                },
                "preferences": {
                    "audioLanguage":["undefined"],
                    "accessibility":[]}
                    }

        response = requests.post(url, headers=headers, json=data, params=params, cookies=sess.cookies, verify=False).json()

        hea = ''

        LICENSE_URL = response.get('streams', '')[0].get('drm', '').get('licenseUrl', '')
        stream_url = response.get('streams', '')[0].get('url', '')
        headr = response.get('streams', '')[0].get('drm', '').get('headers', '')

        if 'X-AxDRM-Message' in headr:
            hea = 'Content-Type=&X-AxDRM-Message=' + dashjs

        elif 'x-dt-auth-token' in headr:
            hea = 'Content-Type=&x-dt-auth-token=' + dashjs

        else:
            if sys.version_info[0] > 2:
                hea = urllib.parse.urlencode(headr)
            else:
                hea = urllib.urlencode(headr)

            if 'Content-Type=&' not in hea:
                hea = 'Content-Type=&' + hea

        license_url = LICENSE_URL + '|' + hea + '|R{SSM}|'

        deleteUrl = 'https://streaminggateway-telia.clientapi-prod.live.tv.telia.net/streaminggateway/rest/secure/v2/streamingticket/{type}/{cid}?country={cc}'.format(type=streamType, cid=(str(media_id)), cc=cc[country].upper())

        headers = {
            'Connection': 'keep-alive',
            'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Microsoft Edge";v="92"',
            'tv-client-boot-id': tv_client_boot_id,
            'DNT': '1',
            'sec-ch-ua-mobile': '?0',
            'Authorization': 'Bearer '+ beartoken,
            'Content-Type': 'application/json',
            'X-Country': cc[country],
            'User-Agent': UA,
            'Accept': '*/*',
            'Origin': base[country],
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': base[country]+'/',
            'Accept-Language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6',
        }

        thread = threading.Thread(name='deleteSession', target=self.deleteSession, args=[deleteUrl, headers])
        thread = threading.Timer(3.0, self.deleteSession, args=[deleteUrl, headers])
        thread.start()

        return stream_url, license_url


    @contextmanager
    def busyDialog(self):
        xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
        try:
            yield
        finally:
            xbmc.executebuiltin('Dialog.Close(busydialognocancel)')


    def LoadVideoLink(self, channel, service, url):
        deb('LoadVideoLink {} service'.format(service))

        self.service = service

        res = False
        startWindowed = False

        inputstream = self.CheckInputstreamInstalledAndEnabled()
        ffmpegdirect = self.CheckFFmpegDirectInstalledAndEnabled()

        pl = re.compile('playlist_\d')

        if ADDON.getSetting('start_video_minimalized') == 'true':
            startWindowed = True

        channelInfo = self.getChannel(channel, service, self.currentlyPlayedService)

        if channelInfo is not None:
            with self.busyDialog():

                if self.currentlyPlayedService['service'] != service:
                    self.unlockCurrentlyPlayedService()
                self.currentlyPlayedService['service'] = service

                if self.terminating or self.userStoppedPlayback:
                    deb('LoadVideoLink aborting playback: self.terminating {}, self.userStoppedPlayback: {}'.format(self.terminating, self.userStoppedPlayback))
                    self.unlockCurrentlyPlayedService()
                    return res

                if service == 'C More':
                    if self.archiveService == '' or self.archivePlaylist == '':
                        try:
                            self.playbackStopped = False

                            try:
                                from urllib.parse import urlencode, quote_plus, quote, unquote
                            except ImportError:
                                from urllib import urlencode, quote_plus, quote, unquote

                            licenseUrl = channelInfo.lic
                            strmUrl = channelInfo.strm

                            if lic['type'] == 'hls':
                                PROTOCOL = 'hls'
                            else:
                                PROTOCOL = 'mpd'

                            DRM = 'com.widevine.alpha'

                            import inputstreamhelper
                            is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)
                            if is_helper.check_inputstream():
                                ListItem = xbmcgui.ListItem(path=strmUrl)
                                ListItem.setInfo( type="Video", infoLabels={ "Title": channelInfo.title, } )
                                ListItem.setContentLookup(False)
                                if sys.version_info[0] > 2:
                                    ListItem.setProperty('inputstream', is_helper.inputstream_addon)
                                else:
                                    ListItem.setProperty('inputstreamaddon', is_helper.inputstream_addon)
                                ListItem.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
                                if DRM:
                                    ListItem.setProperty('inputstream.adaptive.license_type', DRM)
                                    ListItem.setProperty('inputstream.adaptive.license_key', licenseUrl['license']['castlabsServer'] + '|Content-Type=&x-dt-auth-token=%s|R{SSM}|' % licenseUrl['license']['castlabsToken'])
                                    ListItem.setProperty('IsPlayable', 'true')

                            self.strmUrl = strmUrl
                            xbmc.Player().play(item=str(self.strmUrl), listitem=ListItem, windowed=startWindowed)
                            res = True

                        except Exception as ex:
                            deb('Exception while trying to play video: {}'.format(getExceptionString()))
                            self.unlockCurrentlyPlayedService()
                            xbmcgui.Dialog().ok(strings(57018), strings(57021) + '\n' + strings(57028) + '\n' + str(ex))

                if service == 'Ipla':
                    if self.archiveService == '' or self.archivePlaylist == '':
                        try:
                            self.playbackStopped = False

                            try:
                                from urllib.parse import urlencode, quote_plus, quote, unquote
                            except ImportError:
                                from urllib import urlencode, quote_plus, quote, unquote

                            licenseUrl, licenseData = channelInfo.lic
                            strmUrl = channelInfo.strm
                                
                            UA = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0'
                            
                            PROTOCOL = 'mpd'
                            DRM = 'com.widevine.alpha'

                            import inputstreamhelper
                            import ssl
                            try:
                                _create_unverified_https_context = ssl._create_unverified_context
                            except AttributeError:
                                pass
                            else:
                                ssl._create_default_https_context = _create_unverified_https_context
                            certificate_data = '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'
                            

                            is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)
                            if is_helper.check_inputstream():
                                ListItem = xbmcgui.ListItem(path=strmUrl)
                                ListItem.setInfo( type="Video", infoLabels={ "Title": channelInfo.title, } )
                                ListItem.setContentLookup(False)
                                if sys.version_info[0] > 2:
                                    ListItem.setProperty('inputstream', is_helper.inputstream_addon)
                                else:
                                    ListItem.setProperty('inputstreamaddon', is_helper.inputstream_addon)
                                ListItem.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
                                ListItem.setMimeType('application/xml+dash')
                                ListItem.setProperty('inputstream.adaptive.stream_headers', 'Referer: https://www.ipla.tv&User-Agent=' + quote(UA))
                                ListItem.setProperty('inputstream.adaptive.license_type', DRM)
                                #ListItem.setProperty('inputstream.adaptive.server_certificate', certificate_data)
                                ListItem.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
                                ListItem.setProperty('inputstream.adaptive.license_key', licenseUrl+'|Content-Type=application%2Fjson&Referer=https://www.ipla.tv/&User-Agent='+quote(UA)+'|'+licenseData+'|JBlicense')
                                ListItem.setProperty('inputstream.adaptive.license_flags', "persistent_storage")
                                ListItem.setProperty("IsPlayable", "true")

                            self.strmUrl = strmUrl
                            xbmc.Player().play(item=self.strmUrl, listitem=ListItem, windowed=startWindowed)
                            res = True

                        except Exception as ex:
                            deb('Exception while trying to play video: {}'.format(getExceptionString()))
                            self.unlockCurrentlyPlayedService()
                            xbmcgui.Dialog().ok(strings(57018), strings(57021) + '\n' + strings(57028) + '\n' + str(ex))

                if service == 'nc+ GO':
                    try:
                        self.playbackStopped = False

                        try:
                            from urllib.parse import urlencode, quote_plus, quote, unquote
                        except ImportError:
                            from urllib import urlencode, quote_plus, quote, unquote

                        licenseUrl = channelInfo.lic
                        strmUrl = channelInfo.strm

                        if sys.version_info[0] > 2:
                            from urllib.parse import parse_qsl, quote, unquote, urlencode, quote_plus

                        else:
                            from urllib import unquote, quote, urlencode, quote_plus
                            from urlparse import parse_qsl

                        licServ = 'https://wv.drm.insyscd.net/AcquireLicense.ashx'
                        licenseUrl = 'DrmChallengeCustomData='+quote(licenseUrl)
                        
                        UA = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0'
                        
                        PROTOCOL = 'mpd'
                        DRM = 'com.widevine.alpha'
                        
                        import inputstreamhelper
                        is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)
                        if is_helper.check_inputstream():      
                            ListItem = xbmcgui.ListItem(path=strmUrl)
                            ListItem.setInfo( type="Video", infoLabels={ "Title": channelInfo.title, } )
                            ListItem.setContentLookup(False)
                            if sys.version_info[0] > 2:
                                ListItem.setProperty('inputstream', is_helper.inputstream_addon)
                            else:
                                ListItem.setProperty('inputstreamaddon', is_helper.inputstream_addon)
                            ListItem.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
                            ListItem.setMimeType('application/xml+dash')
                            ListItem.setProperty('inputstream.adaptive.stream_headers', 'User-Agent='+quote(UA)+'&auth=SSL/TLS&verifypeer=false')
                            ListItem.setProperty('inputstream.adaptive.license_type', DRM)
                            #ListItem.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
                            ListItem.setProperty('inputstream.adaptive.license_key', licServ+'|'+licenseUrl+'&auth=SSL/TLS&verifypeer=false|R{SSM}|')
                            #ListItem.setProperty('inputstream.adaptive.license_flags', "persistent_storage")
                            ListItem.setProperty('IsPlayable', 'true')

                            catchup = self.archiveService

                            if catchup == '':
                                sec = 90.0 
                            else:
                                sec = catchup.total_seconds()

                            # 3H stream
                            playTime = 11160 - sec 

                            ListItem.setProperty('StartOffset', str(playTime))
                            ListItem.setProperty('inputstream.adaptive.play_timeshift_buffer', 'true')

                        self.strmUrl = strmUrl
                        xbmc.Player().play(item=self.strmUrl, listitem=ListItem, windowed=startWindowed)
                        res = True

                    except Exception as ex:
                        deb('Exception while trying to play video: {}'.format(getExceptionString()))
                        self.unlockCurrentlyPlayedService()
                        xbmcgui.Dialog().ok(strings(57018), strings(57021) + '\n' + strings(57028) + '\n' + str(ex))

                if service == 'PlayerPL':
                    try:
                        self.playbackStopped = False

                        try:
                            from urllib.parse import urlencode, quote_plus, quote, unquote
                        except ImportError:
                            from urllib import urlencode, quote_plus, quote, unquote

                        licenseUrl = channelInfo.lic
                        strmUrl = channelInfo.strm

                        PROTOCOL = 'mpd'
                        DRM = 'com.widevine.alpha'
                        
                        import inputstreamhelper
                        is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)
                        if is_helper.check_inputstream():
                            ListItem = xbmcgui.ListItem(path=strmUrl)
                            ListItem.setInfo( type="Video", infoLabels={ "Title": channelInfo.title, } )
                            ListItem.setContentLookup(False)
                            if sys.version_info[0] > 2:
                                ListItem.setProperty('inputstream', is_helper.inputstream_addon)
                            else:
                                ListItem.setProperty('inputstreamaddon', is_helper.inputstream_addon)
                            ListItem.setMimeType('application/xml+dash')
                            ListItem.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
                            ListItem.setProperty('inputstream.adaptive.license_type', DRM)
                            ListItem.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
                            ListItem.setProperty('inputstream.adaptive.license_key', licenseUrl+'|Content-Type=|R{SSM}|')
                            ListItem.setProperty('inputstream.adaptive.license_flags', "persistent_storage")
                            ListItem.setProperty('IsPlayable', 'true')

                        self.strmUrl = strmUrl
                        xbmc.Player().play(item=self.strmUrl, listitem=ListItem, windowed=startWindowed)
                        res = True

                    except Exception as ex:
                        deb('Exception while trying to play video: {}'.format(getExceptionString()))
                        self.unlockCurrentlyPlayedService()
                        xbmcgui.Dialog().ok(strings(57018), strings(57021) + '\n' + strings(57028) + '\n' + str(ex))

                if service == 'Polsat GO':
                    if self.archiveService == '' or self.archivePlaylist == '':
                        try:
                            self.playbackStopped = False

                            try:
                                from urllib.parse import urlencode, quote_plus, quote, unquote
                            except ImportError:
                                from urllib import urlencode, quote_plus, quote, unquote

                            licenseUrl = channelInfo.lic
                            strmUrl = channelInfo.strm

                            licServ = 'https://b2c-www.redefine.pl/rpc/drm/'

                            UA = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36'

                            PROTOCOL = 'mpd'
                            DRM = 'com.widevine.alpha'

                            if licenseUrl is not None:
                                import inputstreamhelper
                                is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)
                                if is_helper.check_inputstream():
                                    ListItem = xbmcgui.ListItem(path=strmUrl)
                                    ListItem.setInfo( type="Video", infoLabels={ "Title": channelInfo.title, } )
                                    ListItem.setContentLookup(False)
                                    if sys.version_info[0] > 2:
                                        ListItem.setProperty('inputstream', is_helper.inputstream_addon)
                                    else:
                                        ListItem.setProperty('inputstreamaddon', is_helper.inputstream_addon)
                                    ListItem.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
                                    ListItem.setMimeType('application/xml+dash')
                                    ListItem.setProperty('inputstream.adaptive.stream_headers', 'Referer: https://polsatgo.pl')
                                    ListItem.setProperty('inputstream.adaptive.license_type', DRM)
                                    ListItem.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
                                    ListItem.setProperty('inputstream.adaptive.license_key', licServ+'|Content-Type=application%2Fjson&Referer=https://polsatgo.pl/&User-Agent='+quote(UA)+'|'+licenseUrl+'|JBlicense')                      
                                    ListItem.setProperty('inputstream.adaptive.license_flags', "persistent_storage")
                                    ListItem.setProperty('IsPlayable', 'true')
                            else:
                                ListItem = xbmcgui.ListItem(path=strmUrl)
                                ListItem.setInfo( type="Video", infoLabels={ "Title": channelInfo.title, } )
                                ListItem.setContentLookup(False)
                                ListItem.setProperty('IsPlayable', 'true')
                            
                            self.strmUrl = strmUrl
                            xbmc.Player().play(item=self.strmUrl, listitem=ListItem, windowed=startWindowed)
                            res = True

                        except Exception as ex:
                            deb('Exception while trying to play video: {}'.format(getExceptionString()))
                            self.unlockCurrentlyPlayedService()
                            xbmcgui.Dialog().ok(strings(57018), strings(57021) + '\n' + strings(57028) + '\n' + str(ex))

                if service == 'Polsat GO Box':
                    if self.archiveService == '' or self.archivePlaylist == '':
                        try:
                            self.playbackStopped = False

                            try:
                                from urllib.parse import urlencode, quote_plus, quote, unquote
                            except ImportError:
                                from urllib import urlencode, quote_plus, quote, unquote

                            licenseUrl, licenseData = channelInfo.lic
                            strmUrl = channelInfo.strm
                                
                            UA = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'
                            
                            PROTOCOL = 'mpd'
                            DRM = 'com.widevine.alpha'

                            import inputstreamhelper
                            import ssl
                            try:
                                _create_unverified_https_context = ssl._create_unverified_context
                            except AttributeError:
                                pass
                            else:
                                ssl._create_default_https_context = _create_unverified_https_context
                            certificate_data = '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'

                            if licenseUrl is not None:
                                is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)
                                if is_helper.check_inputstream():
                                    ListItem = xbmcgui.ListItem(path=strmUrl)
                                    ListItem.setInfo( type="Video", infoLabels={ "Title": channelInfo.title, } )
                                    ListItem.setContentLookup(False)
                                    if sys.version_info[0] > 2:
                                        ListItem.setProperty('inputstream', is_helper.inputstream_addon)
                                    else:
                                        ListItem.setProperty('inputstreamaddon', is_helper.inputstream_addon)
                                    ListItem.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
                                    ListItem.setMimeType('application/xml+dash')
                                    ListItem.setProperty('inputstream.adaptive.stream_headers', 'Referer: https://polsatboxgo.pl&User-Agent=' + quote(UA))
                                    ListItem.setProperty('inputstream.adaptive.license_type', DRM)
                                    ListItem.setProperty('inputstream.adaptive.server_certificate', certificate_data)
                                    ListItem.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
                                    ListItem.setProperty('inputstream.adaptive.license_key', licenseUrl+'|Content-Type=application%2Fjson&Referer=https://polsatboxgo.pl/&User-Agent='+quote(UA)+'|'+licenseData+'|JBlicense')
                                    ListItem.setProperty('inputstream.adaptive.license_flags', "persistent_storage")
                                    ListItem.setProperty("IsPlayable", "true")

                            else:
                                ListItem = xbmcgui.ListItem(path=strmUrl)
                                ListItem.setInfo( type="Video", infoLabels={ "Title": channelInfo.title, } )
                                ListItem.setContentLookup(False)
                                ListItem.setProperty('IsPlayable', 'true')

                            self.strmUrl = strmUrl
                            xbmc.Player().play(item=self.strmUrl, listitem=ListItem, windowed=startWindowed)
                            res = True

                        except Exception as ex:
                            deb('Exception while trying to play video: {}'.format(getExceptionString()))
                            self.unlockCurrentlyPlayedService()
                            xbmcgui.Dialog().ok(strings(57018), strings(57021) + '\n' + strings(57028) + '\n' + str(ex))

                if service == 'Telia Play':
                    try:
                        self.playbackStopped = False

                        try:
                            from urllib.parse import urlencode, quote_plus, quote, unquote
                        except ImportError:
                            from urllib import urlencode, quote_plus, quote, unquote

                        strmUrl = channelInfo.strm
                        licenseUrl = channelInfo.lic

                        catchup = False

                        if ADDON.getSetting('archive_support') == 'true':
                            if str(self.playlistArchive()) != '':
                                archivePlaylist = str(self.playlistArchive())
                                catchupList = archivePlaylist.split(', ')

                                catchup = True

                                # Catchup strings
                                utc = catchupList[2]
                                lutc = catchupList[3]

                                strmUrl, licenseUrl = self.catchupTeliaPlay(channelInfo, utc, lutc)
                                if not strmUrl:
                                    return None

                        UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36 Edg/89.0.774.63'

                        PROTOCOL = 'mpd'
                        DRM = 'com.widevine.alpha'

                        import inputstreamhelper
                        is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)
                        if is_helper.check_inputstream():  
                            ListItem = xbmcgui.ListItem(path=strmUrl)
                            ListItem.setInfo( type="Video", infoLabels={ "Title": channelInfo.title, } )
                            ListItem.setContentLookup(False)
                            if sys.version_info[0] > 2:
                                ListItem.setProperty('inputstream', is_helper.inputstream_addon)
                            else:
                                ListItem.setProperty('inputstreamaddon', is_helper.inputstream_addon)
                            ListItem.setMimeType('application/dash+xml')
                            ListItem.setProperty('inputstream.adaptive.license_type', DRM)
                            ListItem.setProperty('inputstream.adaptive.license_key', licenseUrl)
                            ListItem.setProperty('inputstream.adaptive.stream_headers', 'Referer: https://www.teliaplay.se/&User-Agent='+quote(UA))
                            ListItem.setProperty('inputstream.adaptive.manifest_type', 'mpd')
                            ListItem.setProperty('IsPlayable', 'true')
                            if catchup:
                                ListItem.setProperty('inputstream.adaptive.play_timeshift_buffer', 'true')       

                        self.strmUrl = strmUrl
                        xbmc.Player().play(item=self.strmUrl, listitem=ListItem, windowed=startWindowed)

                        res = True

                    except Exception as ex:
                        deb('Exception while trying to play video: {}'.format(getExceptionString()))
                        self.unlockCurrentlyPlayedService()
                        xbmcgui.Dialog().ok(strings(57018), strings(57021) + '\n' + strings(57028) + '\n' + str(ex))

                if service == 'Telewizja Polska':
                    if self.archiveService == '' or self.archivePlaylist == '':
                        try:
                            self.playbackStopped = False

                            try:
                                from urllib.parse import urlencode, quote_plus, quote, unquote
                            except ImportError:
                                from urllib import urlencode, quote_plus, quote, unquote

                            strmUrl = channelInfo.strm
                                
                            UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.902.55'

                            PROTOCOL = ''
                            DRM = 'com.widevine.alpha'

                            if '.m3u8' in strmUrl:
                                mimeType = 'application/x-mpegURL'
                                #mimeType = 'application/vnd.apple.mpegstream_url'
                                PROTOCOL = 'hls'

                            import inputstreamhelper
                            is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)
                            if is_helper.check_inputstream():  
                                ListItem = xbmcgui.ListItem(path=strmUrl)
                                ListItem.setInfo( type="Video", infoLabels={ "Title": channelInfo.title, } )
                                ListItem.setContentLookup(False)
                                if sys.version_info[0] > 2:
                                    ListItem.setProperty('inputstream', is_helper.inputstream_addon)
                                else:
                                    ListItem.setProperty('inputstreamaddon', is_helper.inputstream_addon)
                                ListItem.setMimeType(mimeType)
                                ListItem.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
                                ListItem.setProperty('inputstream.adaptive.stream_headers', 'Referer: https://tvpstream.vod.tvp.pl/&User-Agent='+quote(UA))
                                #ListItem.setProperty('inputstream.adaptive.license_type', DRM)
                                #ListItem.setProperty('inputstream.adaptive.license_key','')
                                #ListItem.setProperty('inputstream.adaptive.license_flags', "persistent_storage")
                                ListItem.setProperty('IsPlayable', 'true')
                            
                            self.strmUrl = strmUrl
                            xbmc.Player().play(item=self.strmUrl, listitem=ListItem, windowed=startWindowed)

                            res = True

                        except Exception as ex:
                            deb('Exception while trying to play video: {}'.format(getExceptionString()))
                            self.unlockCurrentlyPlayedService()
                            xbmcgui.Dialog().ok(strings(57018), strings(57021) + '\n' + strings(57028) + '\n' + str(ex))

                if service == 'WP Pilot':
                    if self.archiveService == '' or self.archivePlaylist == '':
                        try:
                            self.playbackStopped = False

                            try:
                                from urllib.parse import urlencode, quote_plus, quote, unquote
                            except ImportError:
                                from urllib import urlencode, quote_plus, quote, unquote

                            strmUrl = channelInfo.strm
                            #adsUrl = channelInfo.lic

                            PROTOCOL = ''

                            if '.m3u8' in strmUrl:
                                mimeType = 'application/x-mpegURL'
                                #mimeType = 'application/vnd.apple.mpegstream_url'
                                PROTOCOL = 'hls'

                            elif '.mpd' in strmUrl or 'format=mpd' in strmUrl:
                                mimeType = 'application/xml+dash'
                                PROTOCOL = 'mpd'

                            import inputstreamhelper
                            is_helper = inputstreamhelper.Helper(PROTOCOL)
                            if is_helper.check_inputstream():  
                                ListItem = xbmcgui.ListItem(path=strmUrl)
                                ListItem.setInfo( type="Video", infoLabels={ "Title": channelInfo.title, } )
                                ListItem.setContentLookup(False)
                                if sys.version_info[0] > 2:
                                    ListItem.setProperty('inputstream', is_helper.inputstream_addon)
                                else:
                                    ListItem.setProperty('inputstreamaddon', is_helper.inputstream_addon)
                                ListItem.setMimeType(mimeType)
                                ListItem.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
                                ListItem.setProperty('IsPlayable', 'true')
                            
                            self.strmUrl = strmUrl
                            xbmc.Player().play(item=self.strmUrl, listitem=ListItem, windowed=startWindowed)
                            xbmcgui.Dialog().notification('WP Pilot', strings(30965))

                            res = True

                        except Exception as ex:
                            deb('Exception while trying to play video: {}'.format(getExceptionString()))
                            self.unlockCurrentlyPlayedService()
                            xbmcgui.Dialog().ok(strings(57018), strings(57021) + '\n' + strings(57028) + '\n' + str(ex))

                if pl.match(service):
                    playbackServices = ['C More', 'Polsat GO', 'Polsat GO Box', 'Ipla', 'nc+ GO', 'PlayerPL', 'Telia Play', 'Telewizja Polska', 'WP Pilot']
                    if self.currentlyPlayedService['service'] not in playbackServices:
                        catchup = False

                        strmUrl = ''

                        redirected_strm = self.getUrl(channelInfo.strm, channelInfo.cid, service)
                        if redirected_strm is not None:
                            strmUrl = redirected_strm
                        else:
                            strmUrl = channelInfo.strm
                            
                        strmUrl_catchup = channelInfo.catchup

                        p = re.compile('service=playlist_\d&cid=\d+_AR.*')

                        duration = ''

                        try:
                            self.playbackStopped = False
                            if ADDON.getSetting('archive_support') == 'true':
                                if str(self.playlistArchive()) != '':
                                    archivePlaylist = str(self.playlistArchive())
                                    catchupList = archivePlaylist.split(', ')

                                    if not p.match(url):
                                        return res

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
                                            if p.match(url):
                                                deb('archive_type(4) wrong type')
                                                xbmcgui.Dialog().ok(strings(30998), strings(59979))
                                            return res
                                    else:

                                        # Default
                                        if ADDON.getSetting('archive_type') == '0':
                                            matches = re.compile('^(http[s]?://[^/]+)/([^/]+)/([^/]*)(mpegts|\\.m3u8)(\\?.+=.+)?$')

                                            catchupList = ['hls-custom', 'mono']

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
                                                    
                                                    elif any(x in fsListType for x in catchupList):
                                                        new_url = strmUrl + '?utc={utc}&lutc={lutc}'.format(utc=utc, lutc=lutc)
                                                        response = requests.get(new_url, allow_redirects=False, timeout=2)
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
                                                        catchup = True
                                                    else:
                                                        m_catchupSource = str(fsHost) + '/' + str(fsChannelId) + '/' + str(fsListType.replace('mono', 'video')) + '-timeshift_rel-' + str(offset) + '.m3u8' + str(fsUrlAppend)
                                                        catchup = True

                                                strmUrl = m_catchupSource

                                            else:
                                                if p.match(url):
                                                    deb('archive_type(0) wrong type')
                                                    xbmcgui.Dialog().ok(strings(30998), strings(59979))
                                                return res

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
                                                catchup = True
                                            elif mutv:
                                                m_catchupSource = strmUrl + catchup
                                                strmUrl = m_catchupSource + '?duration={duration}'.format(duration=str(int(duration)*60))
                                                catchup = True
                                            else:
                                                if p.match(url):
                                                    deb('archive_type(1) wrong type')
                                                    xbmcgui.Dialog().ok(strings(30998), strings(59979))
                                                return res

                                        # Xtream Codes
                                        if ADDON.getSetting('archive_type') == '2':
                                            matches = re.compile('^(http[s]?://[^/]+)/(?:live/)?([^/]+)/([^/]+)/([^/\\.]+)(\\.m3u[8]?|\\.ts)?$')

                                            if matches.match(strmUrl):
                                                xcHost = matches.search(strmUrl).group(1)
                                                xcUsername = matches.search(strmUrl).group(2)
                                                xcPassword = matches.search(strmUrl).group(3)
                                                xcChannelId = matches.search(strmUrl).group(4)
                                                xcExtension = matches.search(strmUrl).group(5)

                                                if xcExtension is None:
                                                    m_isCatchupTSStream = True
                                                    xcExtension = ".ts"

                                                start = '{y}-{m}-{d}:{h}-{min}'.format(y=year, m=month, d=day, h=hour, min=minute)
                                                timeshift = duration + '/' + start

                                                try:
                                                    m_catchupSource = xcHost + "/timeshift/" + xcUsername + "/" + xcPassword + "/"+timeshift+"/" + xcChannelId + xcExtension
                                                except:
                                                    m_catchupSource = xcHost + "/timeshift/" + xcUsername + "/" + xcPassword + "/"+timeshift+"/" + xcChannelId + '.m3u8'

                                                strmUrl = m_catchupSource
                                                catchup = True

                                            else:
                                                if p.match(url):
                                                    deb('archive_type(2) wrong type')
                                                    xbmcgui.Dialog().ok(strings(30998), strings(59979))
                                                return res

                                        # Shift
                                        if ADDON.getSetting('archive_type') == '3':
                                            if '?' in strmUrl:
                                                m_catchupSource = strmUrl + '&utc={utc}&lutc={lutc}-{duration}'.format(utc=utc, lutc=lutc, duration=duration)
                                                strmUrl = m_catchupSource
                                                catchup = True
                                            else:
                                                m_catchupSource = strmUrl + '?utc={utc}&lutc={lutc}-{duration}'.format(utc=utc, lutc=lutc, duration=duration)
                                                strmUrl = m_catchupSource
                                                catchup = True

                            ListItem = xbmcgui.ListItem(path=strmUrl)

                            if inputstream:
                                PROTOCOL = ''
                                DRM = 'com.widevine.alpha'

                                if '$$lic' in strmUrl:
                                    strmUrl, licenseUrl = strmUrl.split('$$lic=')
                                    licenseUrl = unquote_plus(licenseUrl)
                                    if '{SSM}' not in licenseUrl:
                                        licenseUrl += '||R{SSM}|'
                                    ListItem.setProperty('inputstream.adaptive.license_type', DRM)
                                    ListItem.setProperty('inputstream.adaptive.license_key', licenseUrl)

                                elif ('m3u8' in strmUrl or 'hls' in strmUrl) and ffmpegdirect:
                                    mimeType = 'application/x-mpegURL'
                                    #mimeType = 'application/vnd.apple.mpegstream_url'
                                    PROTOCOL = 'hls'

                                elif ('.ts' or ':8080' in strmUrl) and ffmpegdirect:
                                    mimeType = 'video/mp2t'
                                    PROTOCOL = 'hls'

                                elif '.mpd' in strmUrl or 'format=mpd' in strmUrl:
                                    mimeType = 'application/xml+dash'
                                    PROTOCOL = 'mpd'

                                elif '.ism' in strmUrl:
                                    mimeType = 'application/vnd.ms-sstr+xml'
                                    PROTOCOL = 'ism'

                                import inputstreamhelper

                                if PROTOCOL != '':
                                    is_helper = inputstreamhelper.Helper(PROTOCOL)
                                    if is_helper.check_inputstream():
                                        ListItem.setContentLookup(False)

                                        if sys.version_info[0] > 2:
                                            ListItem.setProperty('inputstream', is_helper.inputstream_addon)
                                        else:
                                            ListItem.setProperty('inputstreamaddon', is_helper.inputstream_addon)

                                        ListItem.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)

                                        if mimeType != '':
                                            ListItem.setMimeType(mimeType)

                                        if '|' in strmUrl:
                                            strmUrl, strhdr = strmUrl.split('|')
                                            ListItem.setProperty('inputstream.adaptive.stream_headers', strhdr)

                                        if PROTOCOL == 'dash':                            
                                            ListItem.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')

                                        if ffmpegdirect:
                                            ListItem.setProperty('inputstream', 'inputstream.ffmpegdirect')
                                            ListItem.setProperty('inputstream.ffmpegdirect.stream_mode', 'timeshift')
                                            #ListItem.setProperty('inputstream.ffmpegdirect.open_mode', 'ffmpeg')
                                            ListItem.setProperty('inputstream.ffmpegdirect.is_realtime_stream', 'true')
                                            ListItem.setProperty('inputstream.ffmpegdirect.manifest_type', PROTOCOL)
                                            if duration != '':
                                                ListItem.setProperty('inputstream.ffmpegarchive.default_programme_duration', duration)

                                        if catchup:
                                            ListItem.setProperty('inputstream.adaptive.play_timeshift_buffer', 'true')

                                        ListItem.setProperty("IsPlayable", "true")

                            ListItem.setInfo( type="Video", infoLabels={ "Title": channelInfo.title, } )

                            self.strmUrl = strmUrl

                            xbmc.Player().play(self.strmUrl, ListItem, windowed=startWindowed)
                            res = True

                        except Exception as ex:
                            deb('Exception while trying to play video: {}'.format(getExceptionString()))
                            self.unlockCurrentlyPlayedService()
                            xbmcgui.Dialog().ok(strings(57018), strings(57021) + '\n' + strings(57028) + '\n' + str(ex))
        else:
            deb('LoadVideoLink ERROR channelInfo is None! service: {}'.format(service))
        self.service = service

        return res

    def onPlayBackError(self):
        self.playbackStopped = True
        self.unlockCurrentlyPlayedService()
        self.sleepSupervisor.Stop()
        self.closeVideoOsd()

        if not self.userStoppedPlayback:
            self.checkConnection(self.strmUrl)
        
    def onPlayBackStopped(self):
        self.playbackStopped = True
        self.unlockCurrentlyPlayedService()
        self.sleepSupervisor.Stop()
        self.tryResummingPlayback()
        self.closeVideoOsd()

        if not self.userStoppedPlayback:
            self.checkConnection(self.strmUrl)
        
    def onPlayBackEnded(self):
        self.playbackStopped = True
        self.unlockCurrentlyPlayedService()
        self.sleepSupervisor.Stop()
        self.tryResummingPlayback()
        self.closeVideoOsd()

        if not self.userStoppedPlayback:
            self.checkConnection(self.strmUrl)

    def onPlayBackStarted(self):
        self.playbackStarted = True
        self.sleepSupervisor.Start()
        self.closeDialog()

    def pausePlayback(self):
        debug('PlayService stopPlayback')
        self.urlList = None
        self.userStoppedPlayback = True
        self.nrOfResumeAttempts = 0
        self.terminating = True
        self.unlockCurrentlyPlayedService()
        try:
            xbmc.Player().pause()
        except:
            xbmc.executebuiltin('PlayerControl(Play)')

    def stopPlayback(self):
        debug('PlayService stopPlayback')
        self.urlList = None
        self.userStoppedPlayback = True
        self.nrOfResumeAttempts = 0
        self.terminating = True
        self.unlockCurrentlyPlayedService()

        try:
            xbmc.Player().stop()
        except:
            xbmc.executebuiltin('PlayerControl(Stop)')

        if not self.userStoppedPlayback:
            self.checkConnection(self.strmUrl)

    def unlockCurrentlyPlayedService(self):
        if self.currentlyPlayedService['service'] is not None:
            self.unlockService(self.currentlyPlayedService['service'])
            self.currentlyPlayedService['service'] = None

    def getStreamQualityFromCid(self, cid):
        #debug('getStreamQualityFromCid cid: {}'.format(cid))
        self.streamQuality = ''
        try:
            parts = cid.split("_")
            try:
                parts = re.findall('(?i)(sd|hd|fhd|uhd)', str(parts))
                self.streamQuality = parts[0]
            except:
                self.streamQuality = ''
        except:
            pass

    def tryResummingPlayback(self):
        deb('PlayService tryResummingPlayback self.userStoppedPlayback: {}, self.isWorking(): {}, self.nrOfResumeAttempts: {}, self.maxNrOfResumeAttempts: {}'.format(self.userStoppedPlayback, self.isWorking(), self.nrOfResumeAttempts, self.maxNrOfResumeAttempts))   
        self.closeDialog()

        if self.isWorking() == False and self.urlList is not None and self.userStoppedPlayback == False and self.reconnectFailedStreams == 'true':
            if self.nrOfResumeAttempts < self.maxNrOfResumeAttempts:
                self.nrOfResumeAttempts += 1
                self.starting = True
                deb('PlayService reconnecting, nr of reattempts: {}'.format(self.nrOfResumeAttempts))
                if self.playbackStartTime is not None and (datetime.datetime.now() - self.playbackStartTime).seconds < 10:
                    try:
                        #Playback didn't last for 10s - remove stream from list
                        deb('Playback last for only %s seconds - moving to next one' % (datetime.datetime.now() - self.playbackStartTime).seconds)
                        self.urlList.pop(0)
                    except Exception as ex:
                        deb('tryResummingPlayback exception: {}'.format(getExceptionString()))
                if self.urlList is not None and len(self.urlList) > 0:
                    if self.reconnectDelay > 0:
                        xbmc.sleep(self.reconnectDelay)
                    self.playUrlList(self.urlList, self.archiveService, self.archivePlaylist)
                else:
                    deb('tryResummingPlayback empty playback list, cant resume!')
                    self.closeDialog()

                    self.starting = False

            else:
                deb('PlayService reached reconnection limit - aborting!')
                self.closeDialog()
                self.stopPlayback()


    def checkConnection(self, strmUrl):
        if strmUrl is not None:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            status = 0
            timeout = 2.0

            try:
                req = Request.Request(strmUrl)
                req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0')
                req.add_header('Accept', 'application/json, text/javascript, */*; q=0.01')
                req.add_header('Accept-Language', 'pl,en-US;q=0.7,en;q=0.3')
                req.add_header('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
                response = Request.urlopen(req, context=ctx, timeout=timeout)
                status = response.code

                if status == 200:
                    UA = ADDON.getSetting('{}_user_agent'.format(self.currentlyPlayedService['service']))

                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0',
                        'Accept': 'application/json, text/javascript, */*; q=0.01',
                        'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
                    }

                    if UA:
                        headers.update({'User-Agent': UA})

                    conn_timeout = int(ADDON.getSetting('max_wait_for_playback'))
                    read_timeout = int(ADDON.getSetting('max_wait_for_playback'))
                    timeouts = (conn_timeout, read_timeout)
                    
                    response = scraper.get(strmUrl, headers=headers, allow_redirects=False, stream=True, timeout=timeouts)
                    status = response.status_code

                    base = response.content
                    if b'<BaseURL>http://hls.redefine.pl</BaseURL>' in base and xbmc.getCondVisibility('!Player.HasMedia'):
                        xbmcgui.Dialog().notification(self.service, strings(SERVICE_MAX_DEVICE_ID), xbmcgui.NOTIFICATION_WARNING, time=15000, sound=True)
                        return status

            except HTTPError as e:
                deb('chkConn HTTPError: {}'.format(e.reason))
                status = e.code

            except URLError as e:
                deb('chkConn URLError: {}'.format(e.reason))
                status = 404

            except socket.timeout as e:
                deb('chkConn Timeout: {}, open stream in xbmc.Player'.format('408'))
                status = 408

            except:
                deb('chkConn RequestException')
                status = 400
            
            time.sleep(1)

            if status >= 400 and xbmc.getCondVisibility('!Player.HasMedia'):
                xbmcgui.Dialog().notification(strings(57018) + ' Error: ' + str(status), strings(31019), xbmcgui.NOTIFICATION_ERROR)

            elif status >= 300 and status < 400:
                xbmcgui.Dialog().notification(strings(57058) + ' Status: ' + str(status), strings(31019), xbmcgui.NOTIFICATION_WARNING)

            return status

    def CheckInputstreamInstalledAndEnabled(self):
        if sys.version_info[0] > 2:
            return xbmc.getCondVisibility('System.AddonIsEnabled({id})'.format(id='inputstream.adaptive'))
        else:
            return xbmc.getCondVisibility('System.HasAddon({id})'.format(id='inputstream.adaptive'))

    def CheckFFmpegDirectInstalledAndEnabled(self):
        if sys.version_info[0] > 2:
            return xbmc.getCondVisibility('System.AddonIsEnabled({id})'.format(id='inputstream.ffmpegdirect'))
        else:
            return xbmc.getCondVisibility('System.HasAddon({id})'.format(id='inputstream.ffmpegdirect'))

    def getCurrentServiceString(self):
        service = ''
        if self.currentlyPlayedService['service'] is not None:
            service = self.currentlyPlayedService['service']
            try:
                serviceHandler = SERVICES[service]
                service = serviceHandler.getDisplayName()
            except:
                pass
            if self.streamQuality != '':
                service = service + ' ' + self.streamQuality.upper()
        else:
            service = strings(68016)
        return service

    def closeDialog(self):
        try:
            if xbmc.getCondVisibility('Window.IsVisible(okdialog)'):
                xbmc.executebuiltin('Dialog.Close(okdialog, true)')
        except:
            pass

    def closeVideoOsd(self):
        try:
            if xbmc.getCondVisibility('Window.IsVisible(videoosd)'):
                xbmc.executebuiltin('Dialog.Close(videoosd, true)')
        except:
            pass

    def close(self):
        self.terminating = True
        self.stopPlayback()
        if self.thread is not None and self.thread.is_alive():
            self.thread.join(10)
        for serviceName in SERVICES:
            SERVICES[serviceName].close()