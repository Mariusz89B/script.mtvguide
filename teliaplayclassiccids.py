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


serviceName = 'Telia Play'

base = ['https://teliatv.dk', 'https://classic.teliaplay.se']
host = ['www.teliatv.dk', 'classic.teliaplay.se']
cc = ['dk', 'se']
ca = ['DK', 'SE']

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

    def __init__(self):
        """ Constructor
        :type interval: int
        :param interval: Check interval, in seconds
        """
        self.thread = threading.Thread(target=self.run, args=())
        self.thread.daemon = True                            # Daemonize thread
        self.thread.start()                                  # Start the execution

    def run(self):
        """ Method that runs forever """
        while not xbmc.Monitor().abortRequested():
            ab = TeliaPlayUpdater().checkRefresh()
            if ab:
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


    def createDATAS(self):
        import random
        def gen_hex_code(myrange=6, start=0):
            if not start:
                a = ''.join([random.choice('0123456789abcdef') for x in range(myrange)])
            else:
                a = str(start)+''.join([random.choice('0123456789abcdef') for x in range(myrange-1)])
            return a

        def uid():
            a = gen_hex_code(8,0) + '-' + gen_hex_code(4,0) + '-' + gen_hex_code(4,4) + '-' + gen_hex_code(4,9) + '-' + gen_hex_code(12,0)
            return a

        dashjs = 'DASHJS_' + uid()

        ADDON.setSetting('teliaplay_devush', dashjs)

        
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
            
                self.createDATAS()
        
            headers = {
                'Host': host[self.country],
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36 Edg/86.0.622.51',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6,da;q=0.5,no;q=0.4',
                'DNT': '1',
                'Referer': 'https://teliaplay.se/live',
            }
            
            params = (
                ('deviceId', self.dashjs),
                ('coreVersion', '3.35.1'),
                ('model', 'desktop_windows'),
                ('nativeVersion', 'unknown_nativeVersion'),
                ('uiVersion', '6.24.0(578)'),
            )

            response = sess.get('{base}/rest/secure/users/authentication'.format(base=base[self.country]), headers=headers, params=params, verify=False)

            cookies = {}

            sess_id = sess.cookies['TisapSESSIONID']
            self.cookies = sess.cookies#{ "Cookie": "TisapSESSIONID=" + sess_id + "; path=/; secure; HttpOnly" }
            ADDON.setSetting('teliaplay_sess_id', sess_id)
            
            headers = {
                'Host': host[self.country],
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36 Edg/86.0.622.51',
                'Accept': '*/*',
                'Accept-Language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6,da;q=0.5,no;q=0.4',
                'Origin': base[self.country],

            
            }
            
            params = (
                ('deviceType', 'WEB'),
            )
            
            data = {
            'j_username': self.login,
            'j_password': self.password,
            'deviceType': 'WEB'
            }
            
            response = sess.post('{base}/rest/secure/users/authentication/j_security_check'.format(base=base[self.country]), headers=headers, params=params, data=data, cookies=self.cookies, allow_redirects=False, verify=False)
            deb('TEST: {}'.format(response.text))
            try:
                url = response.headers['Location']
            except:
                deb('Username/password was incorrect')
                self.loginErrorMessage()
                return False 

            response = sess.get(url, headers=headers, params=params, cookies=sess.cookies, verify=False)#.url
            jsonresponse = response.json()
            
            try:
                if 'Username/password was incorrect' in jsonresponse['errorMessage']:
                    self.loginErrorMessage()
                    return False 
            except:
                None
        
            try:
                if 'Could not entitle customer because of the maximum number of devices have been reached' in jsonresponse['message']:
                    self.maxDeviceIdMessage()
                    ADDON.setSetting('teliaplay_sess_id', '')
                    ADDON.setSetting('teliaplay_devush', '')
                    return False
            except:
                None

            try:
                if 'Could not get devices' in jsonresponse['message']:
                    self.loginService()
            except:
                None

            run = Threading()    
            validTo = jsonresponse["token"]["validTo"]
            ADDON.setSetting('teliaplay_validTo', str(validTo))

            beartoken = jsonresponse["token"]["accessToken"]
            ADDON.setSetting('teliaplay_beartoken', str(beartoken))
            
            refrtoken = jsonresponse["token"]["refreshToken"]
            ADDON.setSetting('teliaplay_refrtoken', str(refrtoken))     

            cookies = sess.cookies['TisapSESSIONID']
            ADDON.setSetting('teliaplay_cookies', str(cookies))
  
            headers = {
                'Host': host[self.country],
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36 Edg/86.0.622.51',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6,da;q=0.5,no;q=0.4',
            
            }
            
            params = (
                ('deviceType', 'WEB'),
            )

            data = {
            'j_username': self.login,
            'j_password': self.password,
            'deviceType': 'WEB'
            }
            
            headers = { "Authorization": "Bearer " + beartoken }
            response = sess.get('https://ottapi.prod.telia.net/web/{cc}/tvclientgateway/rest/secure/v1/pubsub'.format(cc=cc[self.country]), headers=headers, params=params, data=data, cookies=sess.cookies, allow_redirects=False).json()
            
            self.usern = response['channels']['engagement']
            ADDON.setSetting('teliaplay_usern', self.usern)
            
            return True

        except:
            self.log('getChannelList exception: {}'.format(getExceptionString()))
        return False


    def checkLogin(self):
        refreshTimeDelta = self.refreshTimeDelta()

        if not self.validTo:
            self.validTo = datetime.datetime.now() - timedelta(days=1)

        if not self.beartoken or refreshTimeDelta < timedelta(minutes=1):
            url = '{base}/rest/secure/users/authentication?deviceId={dash}&coreVersion=3.35.1&model=desktop_windows&nativeVersion=unknown_nativeVersion&uiVersion=6.24.0%28578%29'.format(base=base[self.country], dash=self.dashjs)
            
            headers = {
                'Host': host[self.country],
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36 Edg/86.0.622.51',
                'Accept': '*/*',
                'Accept-Language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6,da;q=0.5,no;q=0.4',
                'Origin': base[self.country],            
            }

            params = (
                ('deviceType', 'WEB'),
            )

            data = {
            'j_username': self.login,
            'j_password': self.password,
            'deviceType': 'WEB'
            }

            try:
                response = sess.get(url, headers=headers, params=params, verify=False)#.url
                jsonresponse = response.json()

                if jsonresponse['message'] == 'Login required':
                    response = sess.post('{base}/rest/secure/users/authentication/j_security_check'.format(base=base[self.country]), headers=headers, params=params, data=data, cookies=self.cookies, allow_redirects=False, verify=False)
                    try:
                        url_new = response.headers['Location']
                        response = sess.get(url_new, headers=headers, params=params, cookies=sess.cookies, verify=False)#.url
                        jsonresponse = response.json()
                    except:
                        pass

                validTo = jsonresponse["token"]["validTo"]
                ADDON.setSetting('teliaplay_validTo', str(validTo))

                beartoken = jsonresponse["token"]["accessToken"]
                ADDON.setSetting('teliaplay_beartoken', str(beartoken))

                refrtoken = jsonresponse["token"]["refreshToken"]
                ADDON.setSetting('teliaplay_refrtoken', str(refrtoken))

                cookies = sess.cookies['TisapSESSIONID']
                ADDON.setSetting('teliaplay_cookies', str(cookies))

                result = validTo, beartoken, refrtoken, cookies

            except:
                result = None

            return result


    def utc_to_local(self, utc_dt):
        # get integer timestamp to avoid precision lost
        timestamp = calendar.timegm(utc_dt.timetuple())
        local_dt = datetime.datetime.fromtimestamp(timestamp)
        assert utc_dt.resolution >= timedelta(microseconds=1)
        return local_dt.replace(microsecond=utc_dt.microsecond)


    def refreshTimeDelta(self):
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
            url = '{base}/rest/v3/secure/engagements/customerengagement'.format(base=base[self.country])
            engagementjson = sess.get(url).json()

            try:
                self.engagementLiveChannels = engagementjson['liveChannels']
            except KeyError as k:
                self.engagementLiveChannels = []
                deb('errorMessage: {k}'.format(k=str(k)))

            self.engagementPlayChannels = []

            try:
               for channel in engagementjson['playChannels']:
                   self.engagementPlayChannels.append(channel['id'])
            except KeyError as k:
                deb('errorMessage: {k}'.format(k=str(k)))

            headers = {
                'Host': host[self.country],
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36 Edg/86.0.622.51',
                'Accept': '*/*',
                'Accept-Language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6,da;q=0.5,no;q=0.4',
                'Origin': base[self.country],

            }
            
            params = (
                ('deviceTypes', 'WEB'),
            )

            channels = sess.get('https://ottapi.prod.telia.net/web/{cc}/contentsourcegateway/rest/v1/channels'.format(cc=cc[self.country]), headers=headers, params=params, cookies=sess.cookies,verify=False).json()       
            for channel in channels:
                if int(channel['id']) in self.engagementLiveChannels:
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
                'Host': 'ottapi.prod.telia.net',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36 Edg/86.0.622.51',
                'Accept': '*/*',
                'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
                'cache-control': 'no-cache',
                'if-modified-since': '0',
                'Authorization': 'Bearer '+ self.beartoken,
                'Content-Type': 'text/plain;charset=UTF-8',
                'Origin': base[self.country],
                'Referer': base[self.country] + '/live',
            }
            
            params = (
                ('playerProfile', 'DEFAULT'),
                ('sessionId', self.sess_id),
            )

            response = sess.post('https://ottapi.prod.telia.net/web/{cc}/streaminggateway/rest/secure/v1/streamingticket/CHANNEL/{cid}/DASH'.format(cc=cc[self.country], cid=(str(cid))), headers=headers, params=params, cookies=sess.cookies, verify=False).json()

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
            mpdurl = streamingUrl+'?ssl=true&time='+str(currentTime)+'&token='+str(token)+'&expires='+str(expires)+'&c='+str(self.usern).replace("e_{}_".format(ca[self.country]), "")+'&d='+str(self.dashjs)

            
            headers = {
                'Host': 'wvls.webtv.telia.com:8063',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36 Edg/86.0.622.51',
                'Accept': '*/*',
                'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
                'X-AxDRM-Message': self.dashjs,
                'Origin': base[self.country],
                'Referer': base[self.country] + '/live',
            }
            xheaders = {

                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36 Edg/86.0.622.51',
                'Accept': '*/*',
                'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
                'Origin': base[self.country],
                'Referer': base[self.country] + '/live',
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