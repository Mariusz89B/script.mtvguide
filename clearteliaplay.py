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
#   This add-on is unoffical and is not endorsed or supported by C More Entertainment in any way. Any trademarks used belong to their owning companies and organisations.

from __future__ import unicode_literals

import sys

import os, shutil
import xbmc, xbmcgui, xbmcvfs
import source as src
from strings import *

class clearTeliaPlay:

    def __init__(self):
        self.reset_login()
        deb('ClearTeliaPlay Completed')

    def set_setting(self, key, value):
        return xbmcaddon.Addon('script.mtvguide').setSetting(key, value)

    def reset_login(self):
        self.set_setting('teliaplay_subtoken', '')
        self.set_setting('teliaplay_timestamp', '')
        self.set_setting('teliaplay_tv_client_boot_id', '')
        self.set_setting('teliaplay_validTo', '')
        self.set_setting('teliaplay_sess_id', '')
        self.set_setting('teliaplay_devush', '')
        self.set_setting('teliaplay_beartoken', '')
        self.set_setting('teliaplay_refrtoken', '')
        self.set_setting('teliaplay_cookies', '')
        self.set_setting('teliaplay_usern', '')
        xbmcgui.Dialog().ok(strings(30371), strings(30372))

clearteliaplay = clearTeliaPlay()