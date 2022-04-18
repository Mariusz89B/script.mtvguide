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

if sys.version_info[0] > 2:
    PY3 = True
else:
    PY3 = False

import xbmc, xbmcvfs
import requests

from strings import *
from serviceLib import *
import re

serviceName         = 'TVP GO'

url = 'https://tvpstream.vod.tvp.pl/'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36 Edg/98.0.1108.50'
}

if PY3:
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
        self.localMapFile       = 'basemap_pl.xml'
        baseServiceUpdater.__init__(self)
        self.serviceEnabled     = ADDON.getSetting('tvpgo_enabled')
        self.servicePriority    = int(ADDON.getSetting('priority_tvpgo'))
        self.url = url

    def loginService(self):
        response = requests.get(url, headers=headers).status_code
        if response == 200:
            return True
        else:
            self.connErrorMessage() 
            return False

    def getChannelList(self, silent):
        result = list()
        if not self.loginService():
            return result

        self.log('\n\n')
        self.log('[UPD] Downloading list of available {} channels from {}'.format(self.serviceName, self.url))
        self.log('[UPD] -------------------------------------------------------------------------------------')
        self.log('[UPD] %-12s %-35s %-35s' % ( '-CID-', '-NAME-', '-TITLE-'))

        try:
            url = 'https://tvpstream.tvp.pl/api/tvp-stream/program-tv/stations'

            response = requests.get(url).json()

            ch_data = response.get('data')

            if ch_data:
                for c in ch_data:
                    cid = c['code'] + '_TS_3'
                    name = c['name'].replace('EPG - ', '').replace('TVP3', 'TVP 3').replace('Historia2', 'Historia 2').replace('Kultura2', 'Kultura 2').replace('UA1', 'UA 1')

                    p = re.compile(r'(\sPL$)')

                    r = p.search(name)
                    match = r.group(1) if r else None

                    if match:
                        title = name
                    else:
                        title = name + ' PL'

                    img = c['image_square']['url'].replace('{width}','140').replace('{height}','140')

                    program = TvCid(cid=cid, name=name, title=title, img=img)
                    result.append(program)

                    self.log('[UPD] %-12s %-35s %-35s' % (cid, name, title))

            if len(result) <= 0:
                self.log('Error while parsing service {}, returned data is: {}'.format(self.serviceName, str(response)))

            self.log('-------------------------------------------------------------------------------------')

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

        code = self.channCid(chann.cid)

        streams = []

        url = 'https://tvpstream.tvp.pl/api/tvp-stream/stream/data?station_code={0}'.format(code)

        response = requests.get(url).json()
        live = response.get('data')
        if live:
            urls = live['stream_url']
            response = requests.get(urls).json()
            data = response

        else:
            data = None

        try:
            if data is not None and data != "":
                chann.strm = data
                try:
                    self.log('getChannelStream found matching channel: cid: {}, name: {}, rtmp:{}'.format(chann.cid, chann.name, chann.strm))
                except:
                    self.log('getChannelStream found matching channel: cid: {}, name: {}, rtmp:{}'.format(str(chann.cid), str(chann.name.encode('utf-8')), str(chann.strm)))
                return chann
            else:
                self.log('getChannelStream error getting channel stream2, result: {}'.format(str(chann.strm)))
                return None

        except Exception as e:
            self.log('getChannelStream exception while looping: {}\n Data: {}'.format(getExceptionString(), str(chann.strm)))
        return None