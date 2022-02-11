#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2014 Krzysztof Cebulski
#   Copyright (C) 2012 Tommy Winther

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

import xbmc, xbmcaddon
import source
from strings import *
from settings import Settings

class Service(object):
    def __init__(self):
        pass
        #self.database = source.Database()
        #self.database.initialize(self.onInit)

    def onInit(self, success):
        Settings.formatter()
        
        #if success:
            #self.database.updateChannelAndProgramListCaches(callback=self.onCachesUpdated, startup=True)
        #else:
            #self.database.close()

    #def onCachesUpdated(self):
        #self.database.close(None)

try:
    global ADDON_AUTOSTART
    ADDON = xbmcaddon.Addon(id = ADDON_ID)

    if ADDON_AUTOSTART == False:
        ADDON_AUTOSTART = True
        if ADDON.getSetting('autostart_mtvguide') == 'true' and xbmc.getCondVisibility('System.HasAddon(%s)' % ADDON_ID):
            xbmc.executebuiltin('RunAddon(%s)' % ADDON_ID)

except source.SourceNotConfiguredException:
    pass  # ignore
    
except Exception as ex:
    deb('[%s] Uncaugt exception in service.py: %s' % (ADDON_ID, getExceptionString()))
