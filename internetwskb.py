#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon

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

#   Some implementations are modified and taken from "plugin.video.internetws" - thank you very much mbebe!

import sys

import re, os
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, xbmcvfs
import string

from strings import *
from serviceLib import *

if sys.version_info[0] > 2:
    PY3 = True
else:
    PY3 = False

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

windowDialog   = xbmcgui.WindowDialog()

def Keyboard(response):
    try:
        image = os.path.join(profilePath, 'captcha')
        f = xbmcvfs.File(image, 'w')
        f.write(response)
        f.close()
        f = xbmcgui.ControlImage(385, 10, 510, 90, image)

        d = windowDialog
        d.addControl(f)
        xbmcvfs.delete(image)
        d.show()

        #xbmc.executebuiltin('Notification(Captcha,Generated by internetowa.ws,86400000,%s)' % image)

        kb = xbmc.Keyboard('','')
        kb.setHeading(strings(30009).encode('utf-8', 'replace'))
        kb.setHiddenInput(False)
        kb.doModal()
        c = kb.getText() if kb.isConfirmed() else None
        if c == '': c = None
        d.removeControl(f)
        d.close()
        return c.upper()

    except:
        return
