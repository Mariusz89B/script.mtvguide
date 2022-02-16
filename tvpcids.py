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

import os
import xbmc, xbmcvfs
import requests

if PY3:
    from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
else:
    from requests import HTTPError, ConnectionError, Timeout, RequestException

from strings import *
from serviceLib import *
import json, re, random
import time

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
        self.serviceEnabled     = ADDON.getSetting('tvp_enabled')
        self.servicePriority    = int(ADDON.getSetting('priority_tvp'))
        self.url = url

    def loginService(self):
        response = requests.get(url, headers=headers).status_code
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
            jsdata = '{"operationName":null,"variables":{"categoryId":null},"extensions":{"persistedQuery":{"version":1,"sha256Hash":"5c29325c442c94a4004432d70f94e336b8c258801fe16946875a873e818c8aca"}},"query":"query ($categoryId: String) {\\n  getLandingPageVideos(categoryId: $categoryId) {\\n    type\\n    title\\n    elements {\\n      id\\n      title\\n      subtitle\\n      type\\n      img {\\n        hbbtv\\n        image\\n        website_holder_16x9\\n        video_holder_16x9\\n        __typename\\n      }\\n      broadcast_start_ts\\n      broadcast_end_ts\\n      sportType\\n      label {\\n        type\\n        text\\n        __typename\\n      }\\n      stats {\\n        video_count\\n        __typename\\n      }\\n      __typename\\n    }\\n    __typename\\n  }\\n  getStationsForMainpage {\\n    items {\\n      id\\n      name\\n      code\\n      image_square {\\n        url\\n        __typename\\n      }\\n      background_color\\n      isNativeChanel\\n      __typename\\n    }\\n    __typename\\n  }\\n}"}'
            data = json.loads(jsdata)
            url = 'https://hbb-prod.tvp.pl/apps/manager/api/hub/graphql'
            
            response = requests.post('https://hbb-prod.tvp.pl/apps/manager/api/hub/graphql', json=data)
            if response:
                channels = json.loads(response.text)['data']['getStationsForMainpage']['items']
                for c in channels:
                    cid = c['id'] + '|' + c['code']
                    name = c['name']
                    title = c['name'] + ' PL'
                    img = c['image_square']['url'].replace('{width}','140').replace('{height}','140')

                    program = TvCid(cid=cid, name=name, title=title, img=img)
                    result.append(program)

            if len(result) <= 0:
                self.log('Error while parsing service {}, returned data is: {}'.format(self.serviceName, str(response)))

        except:
            self.log('getChannelList exception: {}'.format(getExceptionString()))
        return result

    def getChannelStream(self, chann):
        data = None

        id, code = chann.cid.split('|')

        streams = []

        if code != '':
            jsdata = '{"operationName":null,"variables":{"stationCode":"'+code+'"},"extensions":{"persistedQuery":{"version":1,"sha256Hash":"0b9649840619e548b01c33ae4bba6027f86eac5c48279adc04e9ac2533781e6b"}},"query":"query ($stationCode: String!) {\\n  currentProgramAsLive(stationCode: $stationCode) {\\n    id\\n    title\\n    subtitle\\n    date_start\\n    date_end\\n    date_current\\n    description\\n    description_long\\n    description_akpa_long\\n    description_akpa_medium\\n    description_akpa\\n    plrating\\n    npvr\\n    formats {\\n      mimeType\\n      url\\n      __typename\\n    }\\n    __typename\\n  }\\n}"}'
            data = json.loads(jsdata)
            response = requests.post('https://hbb-prod.tvp.pl/apps/manager/api/hub/graphql', json=data)

            if json.loads(response.text)['data']['currentProgramAsLive'] is not None:
                streams=json.loads(response.text)['data']['currentProgramAsLive']['formats']

            else:
                xbmcgui.Dialog().notification('TVPGO', 'Przerwa w emisji', xbmcgui.NOTIFICATION_INFO)

        else:
            jsdata = '{"operationName":null,"variables":{"liveId":"'+id+'"},"extensions":{"persistedQuery":{"version":1,"sha256Hash":"f2fd34978dc0aea320ba2567f96aa72a184ca2d1e55b2a16dc0915bd03b54fb3"}},"query":"query ($liveId: String!) {\\n  getLive(liveId: $liveId) {\\n    error\\n    data {\\n      type\\n      title\\n      subtitle\\n      lead\\n      label {\\n        type\\n        text\\n        __typename\\n      }\\n      src\\n      vast_url\\n      duration_min\\n      subtitles {\\n        src\\n        autoDesc\\n        lang\\n        text\\n        __typename\\n      }\\n      is_live\\n      formats {\\n        mimeType\\n        totalBitrate\\n        videoBitrate\\n        audioBitrate\\n        adaptive\\n        url\\n        downloadable\\n        __typename\\n      }\\n      web_url\\n      __typename\\n    }\\n    __typename\\n  }\\n}"}'
            data = json.loads(jsdata)
            response = requests.post('https://hbb-prod.tvp.pl/apps/manager/api/hub/graphql', json=data)
            streams = json.loads(response.text)['data']['getLive']['data'][0]['formats']

        data = streams

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