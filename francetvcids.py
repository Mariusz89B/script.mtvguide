#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2020 Mariusz89B

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
#   This add-on is unoffical and is not endorsed or supported by France Télévisions in any way. Any trademarks used belong to their owning companies and organisations.

from __future__ import unicode_literals

import sys

import re, os
import time
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, xbmcvfs

import dateutil.parser
from requests import Session
from requests.exceptions import RequestException
from strings import *
from serviceLib import *

serviceName         = 'France TV'

_BASE_URL = 'https://www.france.tv'
_API_URL = 'http://api-front.yatta.francetv.fr'
_VIDEO_API_URL = 'http://sivideo.webservices.francetelevisions.fr/tools/getInfosOeuvre/v2/'
_GEOLOCATION_API_URL = 'http://geo.francetv.fr/ws/edgescape.json'
_VIDEO_TOKEN_URL = 'http://hdfauthftv-a.akamaihd.net/esi/TA'

class FranceTVAPIException(Exception):
    pass

class FranceTVUpdater(baseServiceUpdater):
    def __init__(self):
        self.serviceName        = serviceName
        self.localMapFile       = 'basemap_french.xml'
        baseServiceUpdater.__init__(self)
        self.serviceEnabled     = ADDON.getSetting('francetv_enabled')
        self.servicePriority    = int(ADDON.getSetting('priority_francetv'))
        self.addDuplicatesToList = True

    class _UTF8DictNotEmpty(dict):
        def __setitem__(self, key, value):
            if value:
                dict.__setitem__(self, key, value)
            else:
                if key in self:
                    del self[key]

    def loginService(self):
        return True

    def _http_request(self, _url, json=True, **query):
        if _url and not _url.startswith(('http://', 'https://')):
            _url = _API_URL + _url

        try:
            with Session() as session:
                response = session.get(_url, params=query)
                return response.json() if json else response.text
        except RequestException as ex:
            raise FranceTVAPIException(ex)

    def _parse_media_data(self, media_data):
        result = self._UTF8DictNotEmpty()
        if not media_data:
            return result

        for pattern in media_data.get('patterns') or []:
            if pattern.get('type') == 'carre' and 'w:400' in pattern.get('urls') or {}:
                thumb_file = pattern['urls'].get('w:400')
                if thumb_file:
                    result['thumb'] = _BASE_URL + thumb_file
            elif pattern.get('type') == 'vignette_16x9' and 'w:1024' in pattern.get('urls') or {}:
                fanart_file = pattern['urls'].get('w:1024')
                if fanart_file:
                    result['fanart'] = _BASE_URL + fanart_file

        return result

    def _parse_topic_data(self, data, artwork=False):
        cid = self._UTF8DictNotEmpty()
        name = self._UTF8DictNotEmpty()
        img = self._UTF8DictNotEmpty()

        result = (cid, name, img)

        if not data:
            return result

        cid['channel_id'] = data.get('channel')
        

        topic_id = data.get('url_complete')
        if topic_id:
            cid['id'] = topic_id.replace('/', '_')


        name['title'] = data.get('label')
        if 'title' in name:
            name['title'] = name['title'].capitalize() + ' FR'
            name['title'] = re.sub(r'\W\sFR', 'O FR', name['title'])

        img.update(self._parse_media_data(data.get('media_image')))

        return result

    def getChannelList(self, silent):
        result = list()
        data = self._http_request('/standard/edito/directs')

        if not self.loginService():
            return result

        self.log('\n\n')
        self.log('[UPD] Downloading list of available {} channels from {}'.format(self.serviceName, self.url))
        self.log('[UPD] -------------------------------------------------------------------------------------')
        self.log('[UPD] %-10s %-35s %-15s %-20s %-35s' % ( '-CID-', '-NAME-', '-GEOBLOCK-', '-ACCESS STATUS-', '-IMG-'))

        live = True

        cid = self._UTF8DictNotEmpty()

        try:
            data = self._http_request('/standard/publish/channels')
            if not data:
                return result

            for item in data.get('result') or []:
                cid, name, img = self._parse_topic_data(item)
                cid = cid['id']
                name = name['title']
                img = img['fanart']

                program = TvCid(cid, name, name, img=img)
                result.append(program)
            

            for item in [d['collection'][0] for d in (data.get('result') or []) if d.get('collection')]:
                program = TvCid(cid, name, name, img=img)
                result.append(program)

            if len(result) <= 0:
                self.log('Error while parsing service {}, returned data is: {}'.format(self.serviceName, str(response)))
                self.loginErrorMessage()
        except:
            self.log('getChannelList exception: {}'.format(getExceptionString()))
        return result 

    def _get_country_code(self):
        data = self._http_request(_GEOLOCATION_API_URL)
        try:
            return data['reponse']['geo_info']['country_code']
        except (KeyError, TypeError):
            return None

    def get_video_stream(self, chann):
        chann = re.sub('-', '', chann)
        video = 'SIM_' + chann
        results = self._UTF8DictNotEmpty()
        data = self._http_request(_VIDEO_API_URL, idDiffusion = video)
        if not data:
            return results

        for video in data.get('videos') or []:
            video_url = video.get('url')
            if not video_url:
                continue

            # Ignore georestricted streams
            countries = video.get('geoblocage')
            if countries and self._get_country_code() not in countries:
                self.geoBlockErrorMessage()
                return

            # Ignore streaming protocols not natively supported by Kodi
            video_format = video.get('format')
            if not video_format or video_format == 'dash' or 'hds' in video_format:
                continue

            # Ignore expired content
            now = time.time()
            for interval in video.get('plages_ouverture') or []:
                if (interval.get('debut') or 0) <= now <= (interval.get('fin') or sys.maxsize):
                    break
            else:
                continue

            video_url = self._http_request(_VIDEO_TOKEN_URL, json=False, url=video_url)
            results['video'] = video_url
            break

        return results

    def channCid(self, cid):
        try:
            r = re.compile('^(.*?)_TS_.*$', re.IGNORECASE)
            cid = r.findall(cid)[0]
        except:
            cid 

        return cid

    def getChannelStream(self, chann):
        data = None
        video = self.channCid(chann.cid)

        try:
            data = self.get_video_stream(video)
            video_url = data.get('video')

            data = video_url
        
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