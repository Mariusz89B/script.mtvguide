#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2013 Szakalit

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

import os, shutil
import xbmc, xbmcgui, xbmcvfs
import source as src
from strings import *

class clearDB:

    def __init__(self):
        self.database = src.Database()
        self.command = sys.argv[1]
        deb('ClearDB onInitialized param {}'.format(self.command))
        if self.command == 'deleteDbFile' or self.command == 'deleteAll' or self.command == 'deleteDb59908':
            self.database.deleteDbFile()
            self.database.close()
            #Delete skinsFix check            
            if sys.version_info[0] > 2:
                try:
                    self.profilePath = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
                except:
                    self.profilePath = xbmcvfs.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')
            else:
                try:
                    self.profilePath = xbmc.translatePath(ADDON.getAddonInfo('profile'))
                except:
                    self.profilePath = xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')
 
            if xbmcvfs.exists(os.path.join(self.profilePath, 'skin_fonts.ini')) == True:
                os.remove(os.path.join(self.profilePath, 'skin_fonts.ini'))
                with open(os.path.join(self.profilePath, 'skin_fonts.ini'), 'w+') as fp:
                    fp.write('')
                    fp.close()
            if self.command == 'deleteAll' or self.command == 'deleteDb59908':
                settingsFile = os.path.join(self.profilePath , 'settings.xml')
                os.remove(settingsFile)
                try:
                    shutil.rmtree(self.profilePath)
                except:
                    pass
            xbmcgui.Dialog().ok(strings(DB_DELETED), strings(30969))
        else:
            self.database.initialize(self.onInitialized)

    def onDBCleared(self):
        xbmcgui.Dialog().ok(strings(CLEAR_DB), strings(DONE_DB))

    def onInitialized(self, success):
        if success:
            if self.command == 'clearAll':
                self.database.clearDB()
            if self.command == 'clearCustom':
                self.database.deleteAllStreams()
            if self.command == 'clearRecordings':
                self.database.removeAllRecordings()

            self.database.close(self.onDBCleared)
        else:
            self.database.close()


cleardb = clearDB()
