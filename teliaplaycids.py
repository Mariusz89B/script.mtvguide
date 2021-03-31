#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2020 mbebe
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
else:
    import urllib
    import cookielib

import os, copy, re

from strings import *
from serviceLib import *
import requests
import json
import iso8601
from datetime import datetime, timedelta
import time
import pytz
import threading
import time
import textwrap
import uuid
import six

serviceName = 'Telia Play'

base = ['https://teliatv.dk', 'https://www.teliaplay.se']
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

class Threading(object):
    """ Threading example class
    The run() method will be started and it will run in the background
    until the application exits.
    """

    def __init__(self, interval=60):
        """ Constructor
        :type interval: int
        :param interval: Check interval, in seconds
        """
        self.interval = interval
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

    def run(self):
        """ Method that runs forever """
        while True:
            ab = TeliaPlayUpdater().checkRefresh()
            if ab:
                result = TeliaPlayUpdater().checkLogin()
                if result is not None:
                    validTo, beartoken, refrtoken, cookies = result
                    
                    ADDON.setSetting('teliaplay_validTo', str(validTo))
                    ADDON.setSetting('teliaplay_beartoken', str(beartoken))
                    ADDON.setSetting('teliaplay_refrtoken', str(refrtoken))
                    ADDON.setSetting('teliaplay_cookies', str(cookies))

            time.sleep(self.interval)


class TeliaPlayUpdater(baseServiceUpdater):
    def __init__(self):
        self.serviceName        = serviceName
        if ADDON.getSetting('teliaplay_locale') == '0':
            self.localMapFile = 'basemap_danish.xml'

        elif ADDON.getSetting('teliaplay_locale') == '1':
            self.localMapFile = 'basemap_swedish.xml'

        baseServiceUpdater.__init__(self)
        self.serviceEnabled     = ADDON.getSetting('teliaplay_enabled')
        self.servicePriority    = int(ADDON.getSetting('priority_teliaplay'))
        self.login              = ADDON.getSetting('teliaplay_username').strip()
        self.password           = ADDON.getSetting('teliaplay_password').strip()
        self.sess_id            = ADDON.getSetting('teliaplay_sess_id')
        self.dashjs             = ADDON.getSetting('teliaplay_devush')
        self.beartoken          = ADDON.getSetting('teliaplay_beartoken')
        self.refrtoken          = ADDON.getSetting('teliaplay_refrtoken')
        self.validTo            = ADDON.getSetting('teliaplay_validTo')
        self.cookies            = ADDON.getSetting('teliaplay_cookies')
        self.usern              = ADDON.getSetting('teliaplay_usern')
        self.country            = int(ADDON.getSetting('teliaplay_locale'))
        self.tv_client_boot_id  = ADDON.getSetting('teliaplay_tv_client_boot_id')


    def createDATAS(self):
        #import random
        
        #def gen_hex_code(myrange=6, start=0):
            #if not start:
                #a = ''.join([random.choice('0123456789abcdef') for x in range(myrange)])
            #else:
                #a = str(start)+''.join([random.choice('0123456789abcdef') for x in range(myrange-1)])
            #return a

        #def uid():
            #a = gen_hex_code(8,0) + '-' + gen_hex_code(4,0) + '-' + gen_hex_code(4,4) + '-' + gen_hex_code(4,9) + '-' + gen_hex_code(12,0)
            #return a

        self.dashjs = 'WEB-' + str(uuid.uuid4())
        self.tv_client_boot_id = str(uuid.uuid4())

        ADDON.setSetting('teliaplay_devush', self.dashjs)
        ADDON.setSetting('teliaplay_tv_client_boot_id', self.tv_client_boot_id)

        return self.dashjs

        
    def loginService(self):
        try:
            self.sess_id = ADDON.getSetting('teliaplay_sess_id')
            self.dashjs = ADDON.getSetting('teliaplay_devush')

            import uuid
            if self.dashjs == '':
                try: 
                    from BeautifulSoup import BeautifulSoup
                except ImportError:
                    from bs4 import BeautifulSoup

                html = sess.get('https://www.telia.se/privat/support/info/registrerade-enheter-telia-play', verify=False).text

                soup = BeautifulSoup(html, "html.parser")

                msg = soup.body.find('div', attrs={'class' : 'stepbystep__wrapper'}).text
                msg = re.sub('   ', '[CR]', msg)

                msg = msg[75:]
                if sys.version_info[0] > 2:
                    xbmcgui.Dialog().ok(strings(30904), str(msg))
                else:
                    xbmcgui.Dialog().ok(strings(30904), str(msg.encode('utf-8')))
            
                self.dashjs = self.createDATAS()

            url = 'https://ottapi.prod.telia.net/web/{cc}/logingateway/rest/v1/login'.format(cc=cc[self.country])

            headers = {
                  'Pragma':'no-cache',
                  'Cache-Control':'no-cache',
                  'DNT':'1',
                  'User-Agent': UA,
                  'Accept':'*/*',
                  'Origin': base[self.country],
                  'Accept-Encoding':'gzip, deflate, br',
                  'Accept-Language':'sv',
                  'Content-Type':'application/json',
                    }

            payload = {
                "deviceId": self.dashjs,
                "username": self.login,
                "password": self.password,
                "deviceType": "WEB"
                }


            jsonresponse = sess.post(url, headers=headers, data=json.dumps(payload), verify=False).json()

            try:
                if 'Username/password was incorrect' in jsonresponse['errorMessage']:
                    self.loginErrorMessage()
                    return False 
            except:
                pass
        
            try:
                if 'Could not entitle customer because of the maximum number of devices have been reached' in jsonresponse['message']:
                    self.maxDeviceIdMessage()
                    ADDON.setSetting('teliaplay_sess_id', '')
                    ADDON.setSetting('teliaplay_devush', '')
                    return False
            except:
                pass

            try:
                if 'Could not get devices' in jsonresponse['message']:
                    self.loginService()
            except:
                pass


            url = 'https://ottapi.prod.telia.net/web/{cc}/tvclientgateway/rest/secure/v1/provision'.format(cc=cc[self.country])

            headers = {
                    'Authorization': 'Bearer '+ jsonresponse['accessToken']
            }

            params = (
                ('coreVersion',  '7.0.4'),
                ('deviceId', self.dashjs),
                ('model', 'desktop_windows'),
                ('nativeVersion', 'N/A'),
                ('networkType', 'unknown'),
                ('platformName', 'windows'),
                ('platformVersion', 'NT 10.0'),
                ('productName', 'Microsoft Edge 89.0.774.63'),
                ('uiName', 'telia-web'),
                ('networkType', '6.24.0(578)'),
                ('uiVersion', '2007ed0'),
            )

            response = sess.post(url, headers=headers, params=params, verify=False)
            
            cookies = {}

            self.sess_id = sess.cookies['JSESSIONID']
            ADDON.setSetting('teliaplay_sess_id', self.sess_id)

            self.cookies = sess.cookies

            self.validTo = jsonresponse["validTo"]
            ADDON.setSetting('teliaplay_validTo', str(self.validTo))

            self.beartoken = jsonresponse["accessToken"]
            ADDON.setSetting('teliaplay_beartoken', str(self.beartoken))
            
            self.refrtoken = jsonresponse["refreshToken"]
            ADDON.setSetting('teliaplay_refrtoken', str(self.refrtoken))     

            self.cookies = sess.cookies['JSESSIONID']
            ADDON.setSetting('teliaplay_cookies', str(self.cookies))

            run = Threading()
            
            headers = { 
                "User-Agent": UA,
                "Accept": "*/*",
                "Accept-Language": "sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6",
                "Authorization": "Bearer " + self.beartoken,
            }

            response = sess.get('https://ottapi.prod.telia.net/web/{cc}/tvclientgateway/rest/secure/v1/pubsub'.format(cc=cc[self.country]), headers=headers, cookies=sess.cookies, allow_redirects=False).json()
            
            self.usern = response['channels']['engagement']
            ADDON.setSetting('teliaplay_usern', self.usern)
            
            return True

        except:
            self.log('getChannelList exception: {}'.format(getExceptionString()))
        return False


    def checkLogin(self):
        result = None

        refreshTimeDelta = self.refreshTimeDelta()

        if not self.validTo:
            self.validTo = datetime.datetime.now() - timedelta(days=1)

        if not self.beartoken or refreshTimeDelta < timedelta(minutes=1):
            url = 'https://ottapi.prod.telia.net/web/{cc}/logingateway/rest/v1/login'.format(cc=cc[self.country])

            headers = {
                  'Pragma': 'no-cache',
                  'Cache-Control': 'no-cache',
                  'DNT': '1',
                  'User-Agent': UA,
                  'Accept': '*/*',
                  'Origin': base[self.country],
                  'Accept-Encoding': 'gzip, deflate, br',
                  'Accept-Language': 'sv',
                  'Content-Type': 'application/json',
                    }

            payload = {
                "deviceId": self.dashjs,
                "username": self.login,
                "password": self.password,
                "deviceType": "WEB"
                }

            jsonresponse = sess.post(url, headers=headers, data=json.dumps(payload), verify=False).json()

            self.validTo = jsonresponse["validTo"]
            ADDON.setSetting('teliaplay_validTo', str(self.validTo))

            self.beartoken = jsonresponse["accessToken"]
            ADDON.setSetting('teliaplay_beartoken', str(self.beartoken))

            self.refrtoken = jsonresponse["refreshToken"]
            ADDON.setSetting('teliaplay_refrtoken', str(self.refrtoken))

            self.cookies = sess.cookies['JSESSIONID']
            ADDON.setSetting('teliaplay_cookies', str(self.cookies))

            result = self.validTo, self.beartoken, self.refrtoken, self.cookies

        return result


    def utc_to_local(self, utc_dt):
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
                result = self.utc_to_local(validTo)
        else:
            try:
                try:
                    date_time_format = '%Y-%m-%dT%H:%M:%S.%f+' + self.validTo.split('+')[1]
                    validTo = datetime(*(time.strptime(self.validTo, date_time_format)[0:6]))
                except:
                    date_time_format = '%Y-%m-%dT%H:%M:%S+' + self.validTo.split('+')[1]
                    validTo = datetime(*(time.strptime(self.validTo, date_time_format)[0:6]))
            except:
                try:
                    date_time_format = '%Y-%m-%dT%H:%M:%S.%f+' + self.validTo.split('+')[0]
                    validTo = datetime(*(time.strptime(self.validTo, date_time_format)[0:6]))
                except:
                    date_time_format = '%Y-%m-%dT%H:%M:%S+' + self.validTo.split('+')[0]
                    validTo = datetime(*(time.strptime(self.validTo, date_time_format)[0:6]))


            
            timestamp = int(time.mktime(validTo.timetuple()))
            tokenValidTo = datetime.fromtimestamp(int(timestamp))
            result = tokenValidTo - datetime.now()

        return result
        
        
    def checkRefresh(self):
        refreshTimeDelta = self.refreshTimeDelta()

        if not self.validTo:
            self.validTo = datetime.datetime.now() - timedelta(days=1)

        refr = True if not self.beartoken or refreshTimeDelta < timedelta(minutes=1) else False

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
            
            engagementjson = sess.get(url, headers=headers).json()

            try:
                self.engagementLiveChannels = engagementjson['channelIds']
            except KeyError as k:
                self.engagementLiveChannels = []
                deb('errorMessage: {k}'.format(k=str(k)))

            headers = {
                'Host': host[self.country],
                'User-Agent': UA,
                'Accept': '*/*',
                'Accept-Language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6,da;q=0.5,no;q=0.4',
                'Origin': base[self.country],

            }

            channels = sess.get('https://ottapi.prod.telia.net/web/{cc}/contentsourcegateway/rest/v1/channels'.format(cc=cc[self.country]), headers=headers, verify=False).json() 
            for channel in channels:
                if channel['id'] in self.engagementLiveChannels:
                    cid = channel["id"]
                    name = channel ["name"] + ' ' + ca[self.country]
                    img = channel["id"]
                
                    program = TvCid(cid, name, name, img=img) 
                    result.append(program)

            if len(result) <= 0:
                self.log('Error while parsing service {}'.format(self.serviceName))
                self.loginErrorMessage()
        
        except:
            self.log('getChannelList exception: {}'.format(getExceptionString()))
        
        return result

    
    def getChannelStream(self, chann):
        self.checkLogin()
        data = None
        try:
            try:
                from urllib.parse import urlencode, quote_plus, quote, unquote
            except ImportError:
                from urllib import urlencode, quote_plus, quote, unquote

            cid = chann.cid
            self.beartoken = ADDON.getSetting('teliaplay_beartoken')
            self.dashjs = ADDON.getSetting('teliaplay_devush')

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
                ('sessionId', six.text_type(uuid.uuid4())),#self.sess_id),
            )

            response = sess.post('https://ottapi.prod.telia.net/web/{cc}/streaminggateway/rest/secure/v1/streamingticket/CHANNEL/{cid}/DASH'.format(cc=cc[self.country], cid=(str(cid))), headers=headers, params=params, cookies=sess.cookies, verify=False)#.json()
            response = response.json()

            try:
                if 'Content not authorized' in response['errorMessage']:
                    self.noPremiumMessage()
                    return
            except:
                deb('Content available')

            streamingUrl = response["streamingUrl"]
            token = response["token"]
            currentTime = response["currentTime"]
            expires = response["expires"]
            mpdurl = streamingUrl+'?ssl=true&time='+str(currentTime)+'&token='+str(token)+'&expires='+str(expires)+'&c='+str(self.usern)+'&d='+str(self.dashjs)
            
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

            mpdurl2 = sess.get(mpdurl, headers=xheaders, verify=False).json()
            mpdurl = mpdurl2["location"]
            
            if sys.version_info[0] > 2:
                headok = urllib.parse.urlencode(headers)
            else:
                headok = urllib.urlencode(headers)

            licurl = 'https://wvls.webtv.telia.com:8063/'
            licenseUrl = licurl+'|'+headok+'|R{SSM}|'

            data = mpdurl

            if data is not None and data != "":
                chann.strm = data
                try:
                    self.log('getChannelStream found matching channel: cid: {}, name: {}, rtmp:{}'.format(chann.cid, chann.name, chann.strm))
                except:
                    self.log('getChannelStream found matching channel: cid: {}, name: {}, rtmp:{}'.format(str(chann.cid), str(chann.name), str(chann.strm)))
                return chann, licenseUrl
            else:
                self.log('getChannelStream error getting channel stream2, result: {}'.format(str(data)))
                return None

        except Exception as e:
            self.log('getChannelStream exception while looping: {}\n Data: {}'.format(getExceptionString(), str(data)))
        return None