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

if sys.version_info[0] > 2:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

serviceName         = 'WP Pilot'
login_url = 'https://pilot.wp.pl/api/v1/user_auth/login?device_type=android_tv'
main_url = 'https://pilot.wp.pl/api/v1/channels/list?device_type=android_tv'
video_url = 'https://pilot.wp.pl/api/v1/channel/'
close_stream_url = 'https://pilot.wp.pl/api/v1/channels/close?device_type=android_tv'

headers = {
    'user-agent': 'ExoMedia 4.3.0 (43000) / Android 8.0.0 / foster_e',
    'accept': 'application/json',
    'x-version': 'pl.videostar|3.53.0-gms|Android|26|foster_e',
    'content-type': 'application/json; charset=UTF-8'
}

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
        self.netviapisessid     = ADDON.getSetting('videostar_netviapisessid')
        self.netviapisessval    = ADDON.getSetting('videostar_netviapisessval')
        self.remote_cookies     = ADDON.getSetting('videostar_remote_cookies')
        
    def saveToDB(self, table_name, value):
        import sqlite3
        import os
        if os.path.exists(cacheFile):
            os.remove(cacheFile)
        else:
            print('File does not exists')
        conn = sqlite3.connect(cacheFile, detect_types=sqlite3.PARSE_DECLTYPES, cached_statements=20000)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS Cache(%s TEXT)' % table_name)
        c.execute("INSERT INTO Cache('%s') VALUES ('%s')" % (table_name, value))
        conn.commit()
        c.close()

    def readFromDB(self):
        import sqlite3
        conn = sqlite3.connect(cacheFile, detect_types=sqlite3.PARSE_DECLTYPES, cached_statements=20000)
        c = conn.cursor()
        c.execute("SELECT * FROM Cache")
        for row in c:
            if row:
                c.close()
                return row[0]

    def cookiesToString(self, cookies):
        try:
            return "; ".join([str(x) + "=" + str(y) for x, y in cookies.items()])
        except Exception as e:
            print('exception: ' + e)
            return ''

    def loginService(self):
        if self.netviapisessval == '' and self.netviapisessid == '':
            if len(self.password) > 0 and len(self.login) > 0:
                data = {'device': 'android_tv',
                        'login': self.login,
                        'password': self.password}

                response = requests.post(
                    login_url,
                    json=data,
                    verify=False,
                    headers=headers
                )

                meta = response.json().get('_meta', None)
                if meta is not None:
                    if meta.get('error', {}).get('name', None) is not None:
                        self.loginErrorMessage()
                        return False

                self.saveToDB('wppilot_cache', self.cookiesToString(response.cookies))
                return True

            else:
                self.loginErrorMessage()
                return False
        else:
            if len(self.netviapisessval) > 0 and len(self.netviapisessid) > 0:
                cookies = {'netviapisessid': self.netviapisessid, 'netviapisessval': self.netviapisessval}
                self.saveToDB('wppilot_cache', self.cookiesToString(cookies))
                return True

            elif len(self.remote_cookies) > 0:
                cookies_from_url = requests.get(self.remote_cookies, verify=False, timeout=10).text
                cookies = json.loads(cookies_from_url)
                self.saveToDB('wppilot_cache', self.cookiesToString(cookies))
                return True
            else:
                self.loginErrorMessage()
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
            response = requests.get(main_url, verify=False, headers=headers).json()

            data = response.get('data', [])

            for channel in data:
                if channel.get('access_status', '') != 'unsubscribed':
                    name = channel['name'] + ' PL'
                    cid  = channel['id']
                    img  = channel['thumbnail_mobile']
                    geoblocked = channel['geoblocked']
                    access = channel['access_status']
                    self.log('[UPD] %-10s %-35s %-15s %-20s %-35s' % (cid, name, geoblocked, access, img))
                    if geoblocked != True and access != 'unsubscribed':
                        program = TvCid(cid=cid, name=name, title=name, img=img, lic=access)
                        result.append(program)

            if len(result) <= 0:
                self.log('Error while parsing service {}, returned data is: {}'.format(self.serviceName, str(response)))

        except:
            self.log('getChannelList exception: {}'.format(getExceptionString()))
        return result

    def getChannelStream(self, chann, retry=False):
        video_id = chann.cid

        try:
            cookies = self.readFromDB()
            if len(video_id) == 0:
                return

            url = video_url + video_id + '?format_id=2&device_type=android_tv'
            data = {'format_id': '2', 'device_type': 'android'}

            headers.update({'Cookie': cookies})
            response = requests.get(
                url,
                params=data,
                verify=False,
                headers=headers,
            ).json()

            try:
                if response['_meta']['error']['name'] == 'user_not_verified_eu':
                    self.geoBlockErrorMessage()
            except:
                pass

            meta = response.get('_meta', None)
            if meta is not None:
                token = meta.get('error', {}).get('info', {}).get('stream_token', None)
                if token is not None:
                    json = {'channelId': video_id, 't': token}
                    response = requests.post(
                        close_stream_url,
                        json=json,
                        verify=False,
                        headers=headers
                    ).json()
                    if response.get('data', {}).get('status', '') == 'ok' and not retry:
                        return self.getChannelStream(video_id, True)
                    else:
                        return

            if 'hls@live:abr' in response[u'data'][u'stream_channel'][u'streams'][0][u'type']:
                manifest = response[u'data'][u'stream_channel'][u'streams'][0][u'url'][0]
            else:
                manifest = response[u'data'][u'stream_channel'][u'streams'][1][u'url'][0]

            data = manifest + '|user-agent=' + headers['user-agent']

            if data is not None and data != "":
                chann.strm = data

                self.log('getChannelStream found matching channel: cid: {}, name: {}, rtmp:{}'.format(chann.cid, chann.name, chann.strm))
                return chann
            else:
                self.log('getChannelStream error getting channel stream2, result: {}'.format(str(data)))
                return None

        except Exception as e:
            self.log('getChannelStream exception while looping: {}\n Data: {}'.format(getExceptionString(), str(data)))
        return None
