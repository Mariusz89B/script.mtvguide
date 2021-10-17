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

from __future__ import unicode_literals

import sys
import os

import xbmc, xbmcgui, xbmcvfs, xbmcaddon

import requests
import urllib3
import json
from strings import *

ADDON_ID = 'script.mtvguide'
ADDON = xbmcaddon.Addon(id = ADDON_ID)

onlineMapPathBase = M_TVGUIDE_SUPPORT + 'maps/'

def ccDict():
    try:
        headers = {
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36 Edg/94.0.992.38',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6',
        }

        onlineMapFilename = onlineMapPathBase + 'server_groups.json'

        try:
            http = urllib3.PoolManager()
            response = http.request('GET', onlineMapFilename, headers=headers, timeout=10)#.json()
            ccDict = json.loads(response.data)
        except:
            ccDict = requests.get(onlineMapFilename, headers=headers, timeout=10).json()
    except:
        pathMapBase = os.path.join(ADDON.getAddonInfo('path'), 'resources')
        path = os.path.join(pathMapBase, 'groups.json')

        if sys.version_info[0] > 2:
            with open(path, 'r', encoding='utf-8') as f:
                data = f.read()
        else:
            import codecs
            with codecs.open(path, 'r', encoding='utf-8') as f:
                data = f.read()

        ccDict = json.loads(data)

    sortedDict = {k : ccDict[k] for k in sorted(ccDict)}

    return sortedDict
