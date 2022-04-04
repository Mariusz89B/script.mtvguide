#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2021 Mariusz89B
#   Copyright (C) 2016 Andrzej Mleczko
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

from __future__ import unicode_literals

import sys

from threading import Timer

import os
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, xbmcvfs
import time
from strings import *

ACTION_MOUSE_MOVE = 107
KEYLIST = list()

class SettingsImp():
    def __init__(self):
        try:
            self.command = sys.argv[1]
        except:
            self.command = None

        if self.command is None or self.command == '':
            return

        if self.command == 'Key':
            self.set_key()

    def set_key(self):
        a_info = ADDON.getSetting(id="info_key")
        a_stop = ADDON.getSetting(id="stop_key")
        a_pp = ADDON.getSetting(id="pp_key")
        a_pm = ADDON.getSetting(id="pm_key")
        a_home = ADDON.getSetting(id="home_key")
        a_ctxt = ADDON.getSetting(id="context_key")
        a_rec = ADDON.getSetting(id="record_key")
        a_list = ADDON.getSetting(id="list_key")
        a_volUp = ADDON.getSetting(id="volume_up_key")
        a_volDown = ADDON.getSetting(id="volume_down_key")
        a_switchLastKey = ADDON.getSetting(id="switch_to_last_key")

        for k in KEYLIST:
            if 'info_key' == k[0]:
                a_info = k[1]
            elif 'stop_key' == k[0]:
                a_stop = k[1]
            elif 'pp_key' == k[0]:
                a_pp = k[1]
            elif 'pm_key' == k[0]:
                a_pm = k[1]
            elif 'home_key' == k[0]:
                a_home = k[1]
            elif 'context_key' == k[0]:
                a_ctxt = k[1]
            elif 'record_key' == k[0]:
                a_rec = k[1]
            elif 'list_key' == k[0]:
                a_list = k[1]
            elif 'volume_up_key' == k[0]:
                a_volUp = k[1]
            elif 'volume_down_key' == k[0]:
                a_volDown = k[1]
            elif 'switch_to_last_key' == k[0]:
                a_switchLastKey = k[1]

        info = strings(31009) + '     ' + '[COLOR selected]' + a_info + '[/COLOR]'
        stop = strings(31008) + '     ' + '[COLOR selected]' + a_stop + '[/COLOR]'
        pp = strings(31007) + '     ' + '[COLOR selected]' + a_pp + '[/COLOR]'
        pm = strings(31006) + '     ' + '[COLOR selected]' + a_pm + '[/COLOR]'
        home = strings(31005) + '     ' + '[COLOR selected]' + a_home + '[/COLOR]'
        ctxt = strings(31010) + '     ' + '[COLOR selected]' + a_ctxt + '[/COLOR]'
        rec = strings(31011) + '     ' + '[COLOR selected]' + a_rec + '[/COLOR]'
        listing = strings(31018) + '     ' + '[COLOR selected]' + a_list + '[/COLOR]'
        volUp = strings(31015) + '     ' + '[COLOR selected]' + a_volUp + '[/COLOR]'
        volDown = strings(31016) + '     ' + '[COLOR selected]' + a_volDown + '[/COLOR]'
        switchLastKey = strings(31017) + '     ' + '[COLOR selected]' + a_switchLastKey + '[/COLOR]'
        resetAll = '[COLOR red]' + strings(30010) + '[/COLOR]'

        keyList = ['info_key', 'stop_key', 'pp_key', 'pm_key', 'home_key', 'context_key', 'record_key', 'list_key', 'volume_up_key', 'volume_down_key', 'switch_to_last_key']

        ret = xbmcgui.Dialog().select(strings(31002), [info, stop, pp, pm, home, ctxt, rec, listing, volUp, volDown, switchLastKey, resetAll])

        if ret >= 0 and ret < len(keyList):
            self.get_key(keyList, ret)

        elif ret == len(keyList):
            xbmcgui.Dialog().ok(strings(31002), strings(30013))
            a_info = ADDON.setSetting(id="info_key", value="")
            a_stop = ADDON.setSetting(id="stop_key", value="")
            a_pp = ADDON.setSetting(id="pp_key", value="")
            a_pm = ADDON.setSetting(id="pm_key", value="")
            a_home = ADDON.setSetting(id="home_key", value="")
            a_ctxt = ADDON.setSetting(id="context_key", value="")
            a_rec = ADDON.setSetting(id="record_key", value="")
            a_list = ADDON.setSetting(id="list_key", value="")
            a_volUp = ADDON.setSetting(id="volume_up_key", value="")
            a_volDown = ADDON.setSetting(id="volume_down_key", value="")
            a_switchLastKey = ADDON.setSetting(id="switch_to_last_key", value="")

        else:
            return xbmc.executebuiltin('Addon.OpenSettings(%s)' % ADDON_ID)

    def get_key(self, keyList, ret):
        newkey = KeyListener.record_key()
        newid = keyList[ret]
        ADDON.setSetting(id=newid, value=newkey)
        KEYLIST.append([newid, newkey])
        return xbmc.executebuiltin('Addon.OpenSettings(%s)' % ADDON_ID)

class KeyListener(xbmcgui.WindowXMLDialog):
    TIMEOUT = 10

    def __new__(cls):
        gui_api = tuple(map(int, xbmcaddon.Addon('xbmc.gui').getAddonInfo('version').split('.')))
        file_name = "DialogNotification.xml" if gui_api >= (5, 11, 0) else "DialogKaiToast.xml"
        return super(KeyListener, cls).__new__(cls, file_name, "")

    def __init__(self):
        """Initialize key variable."""
        self.key = None

    def onInit(self):
        try:
            icon = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('path')), 'icon.png')
        except:
            icon = os.path.join(xbmcvfs.translatePath(ADDON.getAddonInfo('path')), 'icon.png')

        self.getControl(400).setImage(icon)
        try:
            self.getControl(401).addLabel(strings(30011))
            self.getControl(402).addLabel(strings(30012).format(self.TIMEOUT))
        except AttributeError:
            self.getControl(401).setLabel(strings(30011))
            self.getControl(402).setLabel(strings(30012).format(self.TIMEOUT))

    def onAction(self, action):
        if action.getId() != ACTION_MOUSE_MOVE:
            code = action.getButtonCode()
            self.key = None if code == 0 else str(code)
            self.close()

    @staticmethod
    def record_key():
        dialog = KeyListener()
        timeout = Timer(KeyListener.TIMEOUT, dialog.close)
        timeout.start()
        dialog.doModal()
        timeout.cancel()
        key = dialog.key
        del dialog
        return key

settingI = SettingsImp()