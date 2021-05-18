#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2020 Mariusz89B
#   Copyright (C) 2020 mbebe
#   Copyright (C) 2019 Andrzej Mleczko

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
#   This add-on is unoffical and is not endorsed or supported by WIRTUALNA POLSKA MEDIA S.A. in any way. Any trademarks used belong to their owning companies and organisations.

from __future__ import unicode_literals

import sys

import os, copy, re
import xbmc, xbmcvfs
from strings import *
from serviceLib import *
from random import randrange
import requests
import base64
import json

serviceName         = 'WP Pilot'
wpUrl               = 'https://pilot.wp.pl/api/'
wpVideoUrl          = 'https://pilot.wp.pl/api/v1/channel/'
wpCloseUrl          = 'https://pilot.wp.pl/api/v1/channels/close'

headers = {
    'user-agent': 'ExoMedia 4.3.0 (43000) / Android 8.0.0 / foster_e',
    'accept': 'application/json',
    'x-version': 'pl.videostar|3.25.0|Android|26|foster_e',
    'content-type': 'application/json; charset=UTF-8'
}

wpLoginUrl = 'https://pilot.wp.pl/api/v1/user_auth/login'

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

cacheFile = os.path.join(profilePath, 'cache.db')

sess = requests.Session()

class WpPilotUpdater(baseServiceUpdater):
    def __init__(self):
        self.serviceName        = serviceName
        self.localMapFile       = 'basemap.xml'
        baseServiceUpdater.__init__(self)
        self.serviceEnabled     = ADDON.getSetting('videostar_enabled')
        self.login              = ADDON.getSetting('videostar_username').strip()
        self.password           = ADDON.getSetting('videostar_password').strip()
        self.servicePriority    = int(ADDON.getSetting('priority_videostar'))
        self.url                = wpUrl
        self.videoUrl           = wpVideoUrl
        self.closeUrl           = wpCloseUrl
        self.addDuplicatesToList = True
        self.acc                = None

    def saveToDB(self, table_name, value):
        import sqlite3
        import os
        if os.path.exists(cacheFile):
            os.remove(cacheFile)
        else:
            print('File does not exists')
        conn = sqlite3.connect(cacheFile, detect_types=sqlite3.PARSE_DECLTYPES,
                               cached_statements=20000)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS Cache(%s TEXT)' % table_name)
        c.execute("INSERT INTO Cache('%s') VALUES ('%s')" % (table_name, value))
        conn.commit()
        c.close()

    def readFromDB(self):
        import sqlite3
        conn = sqlite3.connect(cacheFile, detect_types=sqlite3.PARSE_DECLTYPES,
                               cached_statements=20000)
        c = conn.cursor()
        c.execute("SELECT * FROM Cache")
        for row in c:
            if row:
                c.close()
                return row[0]

    def cookiesToString(self, cookies):
        try:
            return "; ".join([str(x) + "=" + str(y) for x, y in cookies.get_dict().items()])
        except Exception as e:
            print (e)
            return ''

    def loginService(self, checked=''):
        try:
            if len(self.password) > 0 and len(self.login) > 0:
                try:
                    cookies = self.readFromDB()
                except:
                    cookies = None
                headers.update({'Cookie': cookies})

                account = requests.get('https://pilot.wp.pl/api/v1/user', verify=False, headers=headers).json()

                try:
                    if not self.login == account['data']['login']:
                        os.remove(cacheFile)
                        self.loginService(checked=True)
                        if checked:
                            self.loginErrorMessage()
                            return False
                except:
                    None
                
                try:
                    accountType = account['data']['type']

                    if 'free' in accountType:
                        self.acc = True
                    else:
                        self.acc = False
                except:
                    None

                response = requests.get('https://pilot.wp.pl/api/v1/user/sessions', verify=False, headers=headers).json()

                device_id = ''

                try:
                    for item in response['data']:
                        device_id = item['device_info']
                except:
                    device_id = ''

                if 'TV Android foster_e' in device_id:
                    return True
                else:
                    data = {'device': 'android_tv', 'login': self.login, 'password': self.password}

                    response = requests.post(
                        wpLoginUrl,
                        json=data,
                        verify=False,
                        headers=headers
                    )

                    account = response.json()
                    accountType = account['data']['type']

                    if 'free' in accountType:
                        self.acc = True
                    else:
                        self.acc = False

                    meta = response.json().get('_meta', None)
                    if meta is not None:
                        if meta.get('error', {}).get('name', None) is not None:
                            self.log('Exception while trying to log in: {}'.format(getExceptionString()))
                            self.loginErrorMessage()
                            return False
                    
                    self.saveToDB('wppilot_cache', self.cookiesToString(response.cookies))
                    return True

        except:
            self.log('Exception while trying to log in: {}'.format(getExceptionString()))
            self.connErrorMessage()
        return False

    def getChannelList(self, silent):
        result = list()
        if not self.loginService():
            return result

        self.log('\n\n')
        self.log('[UPD] Downloading list of available {} channels from {}'.format(self.serviceName, self.url))
        self.log('[UPD] -------------------------------------------------------------------------------------')
        self.log('[UPD] %-10s %-35s %-15s %-20s %-35s' % ( '-CID-', '-NAME-', '-GEOBLOCK-', '-ACCESS STATUS-', '-IMG-'))

        try:
            cookies = self.readFromDB()
            headers.update({'Cookie': cookies})
            httpdata = requests.get(self.url + '/v1/channels/list?device=androidtv', verify=False, headers=headers).json()

            if httpdata is None:
                self.log('Error while trying to get channel list, result: {}'.format(str(httpdata)))
                self.noPremiumMessage()
                return result

            data = httpdata.get('data', [])

            for channel in data:
                if channel.get('access_status', '') != 'unsubscribed':
                    name = channel['name'] + ' PL'
                    cid  = channel['id']
                    img  = channel['thumbnail_mobile']
                    geoblocked = channel['geoblocked']
                    access = channel['access_status']
                    self.log('[UPD] %-10s %-35s %-15s %-20s %-35s' % (cid, name, geoblocked, access, img))
                    if geoblocked != True and access != 'unsubscribed':
                        program = TvCid(cid, access, name, img=img)
                        result.append(program)

            if len(result) <= 0:
                self.log('Error while parsing service {}, returned data is: {}'.format(self.serviceName, str(httpdata)))
                self.loginErrorMessage()

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

    def getChannelStream(self, chann, retry=False):
        data = None

        cid = self.channCid(chann.cid)
        
        free = self.acc

        try:
            cookies = self.readFromDB()
            url = self.videoUrl + cid
            data = {'format_id': '2', 'device_type': 'android'}

            headers.update({'Cookie': cookies})
            response = requests.get(url, params=data, verify=False, headers=headers).json()

            meta = response.get('_meta', None)
            if meta is not None:
                token = meta.get('error', {}).get('info', {}).get('stream_token', None)
                if token is not None:
                    json = {'channelId': cid, 't': token}
                    response = requests.post(
                        self.closeUrl,
                        json=json,
                        verify=False,
                        headers=headers).json()

                    if response.get('data', {}).get('status', '') == 'ok' and not retry:
                        data = self.getChannelStream(cid, True)
                    else:
                        return

            if 'user_channel_other_stream_playing' in str(response):
                self.maxDeviceIdMessage()

            if 'user_not_verified_eu' in str(response):
                self.geoBlockErrorMessage()

            if 'hls@live:abr' in response['data']['stream_channel']['streams'][0]['type']:
                data = response['data']['stream_channel']['streams'][0]['url'][0] + '|user-agent=' + headers['user-agent'] + '&cookie=' + cookies
            else:
                data = response['data']['stream_channel']['streams'][1]['url'][0] + '|user-agent=' + headers['user-agent'] + '&cookie=' + cookies

            # Advertisement
            #adList = list()

            #if free:
                #import xml.etree.ElementTree as ET

                #html = requests.get('https://pilot.wp.pl/dGdpeTBqSyYFEhNnbQpGM0ZKRyYpU0hlEVJfdm0HBSNKCAg4fQMSelVWFjp_AQ0rCwQSJB0VHSkFHQw3ZAESLgBNXG0jSV12UUNSNnZIXXdXQ1I2cklCNQEbDDB_Q1dyXElTciEDACYGTVdyMhkQKghNFT0uHhBpEwBLJC5UVgEQBkBmBFcCNQsdIjstFggiWUBDMjAeCRQjTVVyEiYlNQEWWCQrHQszSgcVejIdQXUiBBNxcDdCFzMxFiN_QlBzVFY1AwMCDHpVRFFkZBYLNANNVHIkHRczBQQMMH8XQiQQCRUxfwIQNQERCHISJiUYBRQHMH9BQi8FAzM9JhQLelVWFTwjAgx6EAYVeXNcDCNCGAQ6Jh0BNVlAQzA3AwUzDR8LaXFBQioNHgQzJ0xUYQACBCc2GAd6VFYHNzRMVmEJFQE9IxQJJQEUWDEmGBAoFhkEOGQfCzUSEwQkf0BCMQYUECYjBQ0oCk1UbHJXCTcBTQAwKwULNQ0RCXIvGAp6VVYIOTdMVGEJGRFpc1MZ', verify=False).content
                #root = ET.ElementTree(ET.fromstring(html)) 
                #find = root.findall(".//MediaFile/.")

                #for item in find:
                    #ad = item.text.replace('//', 'https://')
                    #ad = re.sub('.webm', '.mp4', str(ad))
                    #adList.append(ad)

                #adList = list(dict.fromkeys(adList))

                #for ad in adList:
                    #try:
                        #ad = requests.get(ad, allow_redirects=False, verify=False, timeout=2).url
                    #except:
                        #adList.remove(ad)

                #adsUrl = adList

            if data is not None and data != "":
                chann.strm = data
                #chann.lic = adsUrl

                self.log('getChannelStream found matching channel: cid: {}, name: {}, rtmp:{}'.format(chann.cid, chann.name, chann.strm))
                return chann
            else:
                self.log('getChannelStream error getting channel stream2, result: {}'.format(str(data)))
                return None

        except Exception as e:
            self.log('getChannelStream exception while looping: {}\n Data: {}'.format(getExceptionString(), str(data)))
        return None
