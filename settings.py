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

import sys

if sys.version_info[0] > 2:
    PY3 = True
else:
    PY3 = False
    
import os
import xbmc, xbmcaddon, xbmcvfs, xbmcgui
from strings import *

class Settings:
    if PY3:
        try:
            addonPath = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path'))
        except:
            addonPath = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path')).decode('utf-8')
    else:
        try:
            addonPath = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path'))
        except:
            addonPath = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')).decode('utf-8')

    @staticmethod
    def formatter():
        if PY3:
            copy = os.path.join(Settings.addonPath, 'resources', 'format', 'settings_py3.xml')
            dest = os.path.join(Settings.addonPath, 'resources', 'settings.xml')

            copyStat = os.stat(copy)
            copySize = copyStat.st_size

            stat = os.stat(dest)
            size = stat.st_size

            if os.stat(copy).st_size == os.stat(dest).st_size:
                pass
            else:
                if size < copySize:
                    success = xbmcvfs.copy(copy, dest)
                
        else:
            copy = os.path.join(Settings.addonPath, 'resources', 'format', 'settings_py2.xml')
            dest = os.path.join(Settings.addonPath, 'resources', 'settings.xml')

            copyStat = os.stat(copy)
            copySize = copyStat.st_size

            stat = os.stat(dest)
            size = stat.st_size
            
            if os.stat(copy).st_size == os.stat(dest).st_size:
                pass
            else:   
                if size > (copySize):
                    success = xbmcvfs.copy(copy, dest)