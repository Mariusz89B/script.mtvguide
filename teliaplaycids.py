#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2021 mbebe
#   Copyright (C) 2021 Mariusz89B

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

#   Disclaimer
#   This add-on is unoffical and is not endorsed or supported by Telia Company AB in any way. Any trademarks used belong to their owning companies and organisations.

import sys
import xbmc

if sys.version_info[0] > 2:
    import urllib.request, urllib.parse, urllib.error
    import http.cookiejar as cookielib
    from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
else:
    import urllib
    import cookielib
    from requests import HTTPError, ConnectionError, Timeout, RequestException

import os, copy, re

from strings import *
from serviceLib import *
import requests
import json
import iso8601
from datetime import timedelta
import time
import pytz
import threading
import textwrap
import uuid
import six

serviceName = 'Telia Play'

base = ['https://teliatv.dk', 'https://www.teliaplay.se']
referer = ['https://teliatv.dk/', 'https://www.teliaplay.se/']
host = ['www.teliatv.dk', 'www.teliaplay.se']
cc = ['dk', 'se']
ca = ['DK', 'SE']

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36 Edg/89.0.774.63'

if sys.version_info[0] > 2:
    try:
        profilePath  = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
    except:
        profilePath  = xbmcvfs.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')
else:
    try:
        profilePath  = xbmc.translatePath(ADDON.getAddonInfo('profile'))
    except:
        profilePath  = xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')

sess = requests.Session()
timeouts = (15, 30)

class Threading(object):
    def __init__(self):
        self.thread = threading.Thread(target=self.run, args=())
        self.thread.daemon = True
        self.thread.start()

    def run(self):
        while not xbmc.Monitor().abortRequested():
            ab = TeliaPlayUpdater().checkRefresh()
            if not ab:
                result = TeliaPlayUpdater().checkLogin()
                if result is not None:
                    validTo, beartoken, refrtoken, cookies = result
                    
                    ADDON.setSetting('teliaplay_validTo', str(validTo))
                    ADDON.setSetting('teliaplay_beartoken', str(beartoken))
                    ADDON.setSetting('teliaplay_refrtoken', str(refrtoken))
                    ADDON.setSetting('teliaplay_cookies', str(cookies))

            if xbmc.Monitor().waitForAbort(1):
                break


class TeliaPlayUpdater(baseServiceUpdater):
    def __init__(self):
        self.serviceName        = serviceName
        self.localMapFile       = 'basemap.xml'
        if ADDON.getSetting('teliaplay_locale') == '0':
            self.localMapFile = 'basemap_danish.xml'
        elif ADDON.getSetting('teliaplay_locale') == '1':
            self.localMapFile = 'basemap_swedish.xml'

        baseServiceUpdater.__init__(self)
        self.serviceEnabled     = ADDON.getSetting('teliaplay_enabled') 
        self.login              = ADDON.getSetting('teliaplay_username').strip()
        self.password           = ADDON.getSetting('teliaplay_password').strip()
        try:
            self.servicePriority    = int(ADDON.getSetting('priority_teliaplay'))
            self.country            = int(ADDON.getSetting('teliaplay_locale'))
        except:
            pass
        self.dashjs             = ADDON.getSetting('teliaplay_devush')
        self.tv_client_boot_id  = ADDON.getSetting('teliaplay_tv_client_boot_id')
        self.timestamp          = ADDON.getSetting('teliaplay_timestamp')
        self.validTo            = ADDON.getSetting('teliaplay_validTo')
        self.beartoken          = ADDON.getSetting('teliaplay_beartoken')
        self.refrtoken          = ADDON.getSetting('teliaplay_refrtoken')
        self.cookies            = ADDON.getSetting('teliaplay_cookies')
        self.usern              = ADDON.getSetting('teliaplay_usern')
        self.subtoken           = ADDON.getSetting('teliaplay_subtoken')


    def sendRequest(self, url, post=False, json=False, headers=None, data=None, params=None, cookies=None, verify=False, allow_redirects=False, timeout=None):
        try:
            if post:
                response = sess.post(url, headers=headers, data=data, params=params, cookies=cookies, verify=verify, allow_redirects=allow_redirects, timeout=timeout)
            else:
                response = sess.get(url, headers=headers, data=data, params=params, cookies=cookies, verify=verify, allow_redirects=allow_redirects, timeout=timeout)

        except HTTPError as e:
            deb('HTTPError: {}'.format(str(e)))
            self.connErrorMessage()
            response = False

        except ConnectionError as e:
            deb('ConnectionError: {}'.format(str(e)))
            self.connErrorMessage()
            response = False

        except Timeout as e:
            deb('Timeout: {}'.format(str(e))) 
            self.connErrorMessage()
            response = False

        except RequestException as e:
            deb('RequestException: {}'.format(str(e))) 
            self.connErrorMessage()
            response = False

        except:
            self.connErrorMessage()
            response = False

        if json:
            return response.json()
        else:
            return response


    def createData(self):
        self.dashjs = 'WEB-' + str(uuid.uuid4())
        ADDON.setSetting('teliaplay_devush', str(self.dashjs))

        self.tv_client_boot_id = str(uuid.uuid4())
        ADDON.setSetting('teliaplay_tv_client_boot_id', str(self.tv_client_boot_id))

        self.timestamp = int(time.time())*1000
        ADDON.setSetting('teliaplay_timestamp', str(self.timestamp))


    def loginData(self):
        try:
            url = 'https://log.tvoip.telia.com:6003/logstash'
                
            data = {
                "bootId": self.tv_client_boot_id,
                "networkType": "unknown",
                "service": "ott",
                "deviceIdType": "vmxId",
                "deviceId": self.dashjs,
                "deviceType": "WEB",
                "model": "windows_desktop",
                "productName": "Chrome 89.0.4389.114",
                "platformName": "windows",
                "platformVersion": "NT 6.1",
                "nativeVersion": "N/A",
                "uiName": "telia-web",
                "uiVersion": "7d5c207",
                "environment": "unknown",
                "country": "unknown",
                "logType": "LOG",
                "payloads": [{
                    "sequence": 1,
                    "timestamp": self.timestamp,
                    "level": "ERROR",
                    "loggerId": "telia-data-backend/System",
                    "message": "Failed to get service status due to timeout after 1000 ms"
                }]
            }
            
            headers = {
                'Host': 'log.tvoip.telia.com:6003',
                'User-Agent': UA,
                'Content-Type': 'text/plain;charset=UTF-8',
                'Accept': '*/*',
                'Sec-GPC': '1',
                'Origin': base[self.country],
                'Sec-Fetch-Site': 'cross-site',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty',
                'Referer': referer[self.country],
                'Accept-Language': 'en-US,en;q=0.9',
            }

            response = self.sendRequest(url, post=True, headers=headers, data=json.dumps(data), verify=False, timeout=timeouts)
            if not response:
                return False

            url = 'https://ottapi.prod.telia.net/web/{cc}/logingateway/rest/v1/login'.format(cc=cc[self.country])

            headers = {
                'Host': 'ottapi.prod.telia.net',
                'tv-client-boot-id': self.tv_client_boot_id,
                'User-Agent': UA,
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Sec-GPC': '1',
                'Origin':  base[self.country],
                'Sec-Fetch-Site': 'cross-site',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty',
                'Referer': referer[self.country],
                'Accept-Language': 'en-US,en;q=0.9',
            }

            data = {
                "deviceId": self.dashjs,
                "username": self.login,
                "password": self.password,
                "deviceType": "WEB",
            }
            
            response = self.sendRequest(url, post=True, json=True, headers=headers, data=json.dumps(data), verify=False, timeout=timeouts)
            if not response:
                return False

            try:
                if 'Username/password was incorrect' in response['errorMessage']:
                    self.loginErrorMessage()
                    return False
            except:
                pass

            self.validTo = response.get('validTo', '')
            ADDON.setSetting('teliaplay_validTo', str(self.validTo))

            self.beartoken = response.get('accessToken', '')
            ADDON.setSetting('teliaplay_beartoken', str(self.beartoken))

            self.refrtoken = response.get('refreshToken', '')
            ADDON.setSetting('teliaplay_refrtoken', str(self.refrtoken))

            url = 'https://ottapi.prod.telia.net/web/{cc}/tvclientgateway/rest/secure/v1/provision'.format(cc=cc[self.country])

            headers = {
                'Host': 'ottapi.prod.telia.net',
                'Cache-Control': 'no-cache',
                'Authorization': 'Bearer ' + self.beartoken,
                'If-Modified-Since': '0',
                'User-Agent': UA,
                'tv-client-boot-id': self.tv_client_boot_id,
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Sec-GPC': '1',
                'Origin': 'https://www.teliaplay.se',
                'Sec-Fetch-Site': 'cross-site',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty',
                'Referer': 'https://www.teliaplay.se/',
                'Accept-Language': 'en-US,en;q=0.9',
            }

            data = {
                "deviceId": self.dashjs,
                "uiVersion": "7d5c207",
                "nativeVersion": "N/A",
                "coreVersion": "7.0.4",
                "model": "windows_desktop",
                "networkType": "unknown",
                "productName": "Chrome 89.0.4389.114",
                "uiName": "telia-web",
                "platformName": "windows",
                "platformVersion": "NT 6.1"
            }

            response = self.sendRequest(url, post=True, json=False, headers=headers, data=json.dumps(data), verify=False, timeout=timeouts)

            try:
                response = response.json()
                if response['errorCode'] == 61004:
                    self.maxDeviceIdMessage()
                    ADDON.setSetting('teliaplay_sess_id', '')
                    ADDON.setSetting('teliaplay_devush', '')
                    return False
                elif response['errorCode'] == 9030:
                    self.connErrorMessage() 
                    ADDON.setSetting('teliaplay_sess_id', '')
                    ADDON.setSetting('teliaplay_devush', '')
                    return False
            except:
                pass

            cookies = {}

            self.cookies = sess.cookies
            ADDON.setSetting('teliaplay_cookies', str(self.cookies))

            url = 'https://ottapi.prod.telia.net/web/{cc}/tvclientgateway/rest/secure/v1/pubsub'.format(cc=cc[self.country])

            headers = { 
                    "User-Agent": UA,
                    "Accept": "*/*",
                    "Accept-Language": "sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6",
                    "Authorization": "Bearer " + self.beartoken,
                    'tv-client-boot-id': self.tv_client_boot_id,
                }

            response = self.sendRequest(url, json=True, headers=headers, cookies=sess.cookies, allow_redirects=False, timeout=timeouts)

            self.usern = response['channels']['engagement']
            ADDON.setSetting('teliaplay_usern', str(self.usern))

            self.subtoken = response['config']['subscriberToken']
            ADDON.setSetting('teliaplay_subtoken', str(self.subtoken))

            return True
        except:
            self.log('getChannelList exception: {}'.format(getExceptionString()))
            self.connErrorMessage()  
        return False

    def loginService(self):
        try:
            if self.dashjs == '':
                try: 
                    from BeautifulSoup import BeautifulSoup
                except ImportError:
                    from bs4 import BeautifulSoup

                try:
                    html = sess.get('https://www.telia.se/privat/support/info/registrerade-enheter-telia-play', verify=False, timeout=timeouts).text

                    soup = BeautifulSoup(html, "html.parser")

                    msg = soup.body.find('div', attrs={'class' : 'stepbystep__wrapper'}).text
                    msg = re.sub('   ', '[CR]', msg)

                    msg = msg[75:]
                    if sys.version_info[0] > 2:
                        xbmcgui.Dialog().ok(strings(30904), str(msg))
                    else:
                        xbmcgui.Dialog().ok(strings(30904), str(msg.encode('utf-8')))
                except:
                    pass
            
                self.createData()

            login = self.loginData()

            if login:
                run = Threading()

            return login

        except:
            self.log('getChannelList exception: {}'.format(getExceptionString()))
            self.connErrorMessage()
        return False


    def checkLogin(self):
        result = None

        refreshTimeDelta = self.refreshTimeDelta()

        if not self.validTo:
            self.validTo = datetime.datetime.now() - timedelta(days=1)

        if not self.beartoken or refreshTimeDelta < timedelta(minutes=1):
            login = self.loginData()

            result = self.validTo, self.beartoken, self.refrtoken, self.cookies

        return result


    def utcToLocal(self, utc_dt):
        # get integer timestamp to avoid precision lost
        timestamp = calendar.timegm(utc_dt.timetuple())
        local_dt = datetime.datetime.fromtimestamp(timestamp)
        assert utc_dt.resolution >= timedelta(microseconds=1)
        return local_dt.replace(microsecond=utc_dt.microsecond)


    def refreshTimeDelta(self):
        result = None

        if 'Z' in self.validTo:
            validTo = iso8601.parse_date(self.validTo)
            if localize:
                result = self.utcToLocal(validTo)
        elif self.validTo != '':
            if not self.validTo:
                try:
                    date_time_format = '%Y-%m-%dT%H:%M:%S.%f+' + self.validTo.split('+')[1]
                except:
                    date_time_format = '%Y-%m-%dT%H:%M:%S.%f+' + self.validTo.split('+')[0]

                validTo = datetime.datetime(*(time.strptime(self.validTo, date_time_format)[0:6]))
                timestamp = int(time.mktime(validTo.timetuple()))
                tokenValidTo = datetime.datetime.fromtimestamp(int(timestamp))
            else:
                tokenValidTo = datetime.datetime.now()
        else:
            tokenValidTo = datetime.datetime.now()

        result = tokenValidTo - datetime.datetime.now()

        return result
        
        
    def checkRefresh(self):
        refreshTimeDelta = self.refreshTimeDelta()

        if not self.validTo:
            self.validTo = datetime.datetime.now() - timedelta(days=1)

        if refreshTimeDelta is not None:
            refr = True if not self.beartoken or refreshTimeDelta < timedelta(minutes=1) else False
        else:
            refr = False

        return refr


    def getChannelList(self, silent):
        result = list()

        if not self.loginService():
            return result

        self.checkLogin()
        
        self.log('\n\n')
        self.log('[UPD] Downloading list of available {} channels from {}'.format(self.serviceName, self.country))
        self.log('[UPD] -------------------------------------------------------------------------------------')
        self.log('[UPD] %-15s %-35s %-30s' % ('-CID-', '-NAME-', '-TITLE-'))
        
        try:
            url = 'https://ottapi.prod.telia.net/web/{cc}/engagementgateway/rest/secure/v2/engagementinfo'.format(cc=cc[self.country])
            
            headers = { 
                "User-Agent": UA,
                "Accept": "*/*",
                "Accept-Language": "sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6",
                "Authorization": "Bearer " + self.beartoken,
            }
            
            engagementjson = self.sendRequest(url, json=True, headers=headers, verify=False)
            if not engagementjson:
                return result

            try:
                self.engagementLiveChannels = engagementjson['channelIds']
            except KeyError as k:
                self.engagementLiveChannels = []
                deb('errorMessage: {k}'.format(k=str(k)))

            self.engagementPlayChannels = []

            try:
               for channel in engagementjson['stores']:
                   self.engagementPlayChannels.append(channel['id'])
            except KeyError as k:
                deb('errorMessage: {k}'.format(k=str(k)))

            url = 'https://ottapi.prod.telia.net/web/{cc}/contentsourcegateway/rest/v1/channels'.format(cc=cc[self.country])

            headers = {
                'Host': host[self.country],
                'User-Agent': UA,
                'Accept': '*/*',
                'Accept-Language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6,da;q=0.5,no;q=0.4',
                'Origin': base[self.country],

            }

            channels = self.sendRequest(url, json=True, headers=headers, verify=False) 
            if not channels:
                return result

            for channel in channels:
                if channel['id'] in self.engagementLiveChannels:
                    cid = channel["id"] + '_TS_1'
                    name = channel ["name"] + ' ' + ca[self.country]
                    img = channel["id"]
                
                    program = TvCid(cid, name, name, img=img) 
                    result.append(program)

            if len(result) <= 0:
                self.log('Error while parsing service {}'.format(self.serviceName))
        
        except:
            self.log('getChannelList exception: {}'.format(getExceptionString()))
        
        return result

    def channCid(self, cid):
        try:
            r = re.compile('^(.*?)_TS_.*$', re.IGNORECASE)
            cid = r.findall(cid)[0]
        except:
            cid 

        return cid

    def getChannelStream(self, chann):
        data = None

        self.checkLogin()

        try:
            try:
                from urllib.parse import urlencode, quote_plus, quote, unquote
            except ImportError:
                from urllib import urlencode, quote_plus, quote, unquote

            cid = self.channCid(chann.cid)

            streamType = 'CHANNEL'

            url = 'https://ottapi.prod.telia.net/web/{cc}/streaminggateway/rest/secure/v1/streamingticket/{type}/{cid}/DASH'.format(cc=cc[self.country], cid=(str(cid)), type=streamType)

            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6',
                'Authorization': 'Bearer '+ self.beartoken,
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Content-Type': 'text/plain;charset=UTF-8',
                'DNT': '1',
                'Host': 'ottapi.prod.telia.net',
                'Origin': base[self.country],
                'Pragma': 'no-cache',
                'Referer': base[self.country]+'/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
                'User-Agent': UA,
                'tv-client-boot-id': self.tv_client_boot_id,
            }
            
            params = (
                ('playerProfile', 'DEFAULT'),
                ('sessionId', six.text_type(uuid.uuid4())),
            )

            response = self.sendRequest(url, post=True, json=True, headers=headers, params=params, cookies=sess.cookies, verify=False, timeout=timeouts)
            if not response:
                data = None
                return data 

            streamingUrl = response["streamingUrl"]
            token = response["token"]
            currentTime = response["currentTime"]
            expires = response["expires"]

            mpdurl = '{base}?ssl=true&time={time}&token={token}&expires={expires}&c={user_id}&d={dev_id}'.format(base=streamingUrl, time=currentTime, token=token, expires=expires, user_id=self.usern, dev_id=self.dashjs)

            try:
                if 'Content not authorized' in response['errorMessage']:
                    self.noPremiumMessage()
                    return
            except:
                deb('Content available')
            
            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'DNT': '1',
                'Host': 'wvls.webtv.telia.com:8063',
                'Origin': base[self.country],
                'Pragma': 'no-cache',
                'Referer': base[self.country]+'/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
                'User-Agent': UA,
                'x-axdrm-message': self.dashjs,
            }

            xheaders = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'DNT': '1',
                'Origin': base[self.country],
                'Pragma': 'no-cache',
                'Referer': base[self.country]+'/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
                'User-Agent': UA,
            }

            mpdurl_re = self.sendRequest(mpdurl, json=True, headers=xheaders, verify=False)
            if not mpdurl_re:
                data = None
                return data 

            mpdurl = mpdurl_re["location"]
            
            if sys.version_info[0] > 2:
                headok = urllib.parse.urlencode(headers)
            else:
                headok = urllib.urlencode(headers)

            licurl = 'https://wvls.webtv.telia.com:8063/'
            licenseUrl = licurl+'|'+headok+'|R{SSM}|'

            data = mpdurl

            if data is not None and data != "":
                chann.strm = data
                chann.lic = licenseUrl
                try:
                    self.log('getChannelStream found matching channel: cid: {}, name: {}, rtmp:{}'.format(chann.cid, chann.name, chann.strm))
                except:
                    self.log('getChannelStream found matching channel: cid: {}, name: {}, rtmp:{}'.format(str(chann.cid), str(chann.name), str(chann.strm)))
                return chann
            else:
                self.log('getChannelStream error getting channel stream2, result: {}'.format(str(data)))
                return None

        except Exception as e:
            self.log('getChannelStream exception while looping: {}\n Data: {}'.format(getExceptionString(), str(data)))
        return None
