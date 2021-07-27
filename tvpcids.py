#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
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
#   This add-on is unoffical and is not endorsed or supported by Telewizja Polska S.A. in any way. Any trademarks used belong to their owning companies and organisations.

import sys

import os
import xbmc, xbmcvfs
import requests

if sys.version_info[0] > 2:
    from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
else:
    from requests import HTTPError, ConnectionError, Timeout, RequestException

from strings import *
from serviceLib import *
import json, re, random
import time

serviceName         = 'Telewizja Polska'

url = 'https://tvpstream.vod.tvp.pl/'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.67'
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

sess = requests.Session()
timeouts = (15, 30)

class TvpUpdater(baseServiceUpdater):
    def __init__(self):
        self.serviceName        = serviceName
        self.localMapFile       = 'basemap.xml'
        baseServiceUpdater.__init__(self)
        self.serviceEnabled     = ADDON.getSetting('tvp_enabled')
        self.servicePriority    = int(ADDON.getSetting('priority_tvp'))
        self.url = url

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

    def loginService(self):
        response = self.sendRequest(url, headers=headers).status_code
        if response == 200:
            return True
        else:
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
            response = self.sendRequest(url, headers=headers)

            channels  = re.findall('data-channel-id="(\d+)".*data-video-id="(\d+)".*data-stationname="(.*?)"', response.text)
            for item in channels:
                if item[2] != '':
                    cid = item[1]
                    img = item[1]
                    name = item[2]     
                    
                else:
                    if item[0] == '52451253':
                        name = 'TVP Historia 2 PL'
                        cid = item[1]
                        img = item[1]   

                    elif item[0] == '51121199':
                        name = 'TVP Kultura 2 PL'
                        cid = item[1]
                        img = item[1]  

                    elif item[0] == '51656487':
                        name = 'Poland In PL'
                        cid = item[1]
                        img = item[1] 

                program = TvCid(cid, name, name, img=img)
                result.append(program)

            if len(result) <= 0:
                self.log('Error while parsing service {}, returned data is: {}'.format(self.serviceName, str(response)))

        except:
            self.log('getChannelList exception: {}'.format(getExceptionString()))
        return result

    def getChannelStream(self, chann):
        data = None

        timestamp = int(time.time() * 1000)

        callback = random.randint(1000, 9999)
        response = self.sendRequest('https://tvpstream.vod.tvp.pl/sess/TVPlayer2/api.php?id={cid}&@method=getTvpConfig&@callback=__tp2JSONP{callback}T{time}'.format(cid=chann.cid, callback=callback, time=timestamp), headers=headers)

        response_json = response.text

        txt = re.sub('\"use strict\";', '', response_json)
        txt = re.sub('_.*\({', '{', txt)
        txt = re.sub('}\);', '}', txt)

        jstring = json.loads(txt)

        l = jstring['content']['files']

        for i in range(len(l)):
            stream = jstring['content']['files'][i]['url']
            if '.m3u8' in stream: 
                data = stream

        if data is None or data == '' or 'material_niedostepny' in data:
            xbmcgui.Dialog().notification(serviceName, xbmc.getLocalizedString(15012), xbmcgui.NOTIFICATION_WARNING)
            data = None

        try:
            if data is not None and data != "":
                chann.strm = data
                try:
                    self.log('getChannelStream found matching channel: cid: {}, name: {}, rtmp:{}'.format(chann.cid, chann.name, chann.strm))
                except:
                    self.log('getChannelStream found matching channel: cid: {}, name: {}, rtmp:{}'.format(str(chann.cid), str(chann.name), str(chann.strm)))
                return chann
            else:
                self.log('getChannelStream error getting channel stream2, result: {}'.format(str(chann.strm)))
                return None

        except Exception as e:
            self.log('getChannelStream exception while looping: {}\n Data: {}'.format(getExceptionString(), str(chann.strm)))
        return None