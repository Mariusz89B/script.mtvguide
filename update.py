#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2022 Mariusz89B

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

import xbmc, xbmcaddon, xbmcgui
from strings import *
import requests

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.124 Safari/537.36 Edg/102.0.1245.41'

class Update():
    def __init__(self):
        self.close()
        self.UpdateAddon()
        deb('Update Addon from repository')

    def close(self):
        xbmc.executebuiltin('Dialog.Close(all, true)')

    def UpdateAddon(self):
        """Update Add-on from mods-kodi repository"""
        url = 'https://raw.githubusercontent.com/Mariusz89B/mods-kodi/master/script.mtvguide/changelog.txt'

        headers = {
            'authority': 'raw.githubusercontent.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6,fr;q=0.5',
            'dnt': '1',
            'referer': 'https://github.com/Mariusz89B/mods-kodi/blob/master/script.mtvguide/changelog.txt',
            'user-agent': UA,
        }

        response = requests.get(url, headers=headers)
        status = response.status_code

        if status < 400:
            version = response.content.splitlines()[0].decode('utf-8').replace('v', '')

            msg = strings(30173).format(version)

            xbmc.executebuiltin('UpdateAddonRepos')
            xbmc.executebuiltin('UpdateLocalAddons')
            xbmc.executebuiltin('ActivateWindow(addonbrowser, addons://repository.mods-kodi/xbmc.addon.video/)')

            xbmcgui.Dialog().ok(strings(57051), msg)

        else:
            msg = strings(30174).format(status)
            xbmcgui.Dialog().ok(strings(57051), msg)

run = Update()