#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2020 Mariusz89B
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

if sys.version_info[0] > 2:
  import configparser
else:
  import ConfigParser

import os
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, xbmcvfs
from strings import *
from skins import Skin

if sys.version_info[0] > 2:
  config = configparser.RawConfigParser()
else:
  config = ConfigParser.RawConfigParser()
config.read(os.path.join(Skin.getSkinPath(), 'settings.ini'))
try:
    skin_resolution = config.getboolean("Skin", "resolution")
except:
    skin_resolution = '720p'

class KeyListener(xbmcgui.WindowXMLDialog):

  def __new__(cls):
    return super(KeyListener, cls).__new__(cls, 'DialogSetKey.xml', Skin.getSkinBasePath(), Skin.getSkinName(), skin_resolution)

  def onInit(self):
    self.key = 0
    self.a_info = 0
    self.a_home = 0
    self.a_stop = 0
    self.a_pp = 0
    self.a_pm = 0
    self.a_ctxt = 0
    self.a_rec = 0
    self.a_list = 0
    self.a_volUp = 0
    self.a_volDown = 0
    self.a_switchLastKey = 0
    self.getControl(7001).setLabel(str(ADDON.getSetting('info_key')))
    self.getControl(7002).setLabel(str(ADDON.getSetting('stop_key')))
    self.getControl(7003).setLabel(str(ADDON.getSetting('pp_key')))
    self.getControl(7004).setLabel(str(ADDON.getSetting('pm_key')))
    self.getControl(7005).setLabel(str(ADDON.getSetting('home_key')))
    self.getControl(7006).setLabel(str(ADDON.getSetting('context_key')))
    self.getControl(7007).setLabel(str(ADDON.getSetting('record_key')))
    self.getControl(7021).setLabel(str(ADDON.getSetting('list_key')))
    self.getControl(7009).setLabel(str(ADDON.getSetting('volume_up_key')))
    self.getControl(7010).setLabel(str(ADDON.getSetting('volume_down_key')))
    try:
        self.getControl(7020).setLabel(str(ADDON.getSetting('switch_to_last_key')))
    except:
        pass

  def onAction(self, action):

    if action.getId() == 107 or action.getId() == 100 or action.getId() == 7 or action.getButtonCode() == 61453 or action.getId() == 10:
        return
    else:
       self.key = action.getButtonCode()
       if self.key == 0:
            self.key = action.getId()

       if self.a_info == 1 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_list == 0 and self.a_volUp == 0 and self.a_volDown == 0 and self.a_switchLastKey == 0:
          ADDON.setSetting(id="info_key", value=str(self.key))
          self.getControl(7001).setLabel(str(self.key))
          self.getControl(7001).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(8001).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(9001).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.a_info = 0
       if self.a_info == 0 and self.a_stop == 1 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_list == 0 and self.a_volUp == 0 and self.a_volDown == 0 and self.a_switchLastKey == 0:
          ADDON.setSetting(id="stop_key", value=str(self.key))
          self.getControl(7002).setLabel(str(self.key))
          self.getControl(7002).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(8002).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(9002).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.a_stop = 0
       if self.a_info == 0 and self.a_stop == 0 and self.a_pp == 1 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_list == 0 and self.a_volUp == 0 and self.a_volDown == 0 and self.a_switchLastKey == 0:
          ADDON.setSetting(id="pp_key", value=str(self.key))
          self.getControl(7003).setLabel(str(self.key))
          self.getControl(7003).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(8003).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(9003).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.a_pp = 0
       if self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 1 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_list == 0 and self.a_volUp == 0 and self.a_volDown == 0 and self.a_switchLastKey == 0:
          ADDON.setSetting(id="pm_key", value=str(self.key))
          self.getControl(7004).setLabel(str(self.key))
          self.getControl(7004).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(8004).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(9004).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.a_pm = 0
       if self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 1 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_list == 0 and self.a_volUp == 0 and self.a_volDown == 0 and self.a_switchLastKey == 0:
          ADDON.setSetting(id="home_key", value=str(self.key))
          self.getControl(7005).setLabel(str(self.key))
          self.getControl(7005).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(8005).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(9005).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.a_home = 0
       if self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 1 and self.a_rec == 0 and self.a_list == 0 and self.a_volUp == 0 and self.a_volDown == 0 and self.a_switchLastKey == 0:
          ADDON.setSetting(id="context_key", value=str(self.key))
          self.getControl(7006).setLabel(str(self.key))
          self.getControl(7006).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(8006).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(9006).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.a_ctxt = 0
       if self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 1 and self.a_list == 0 and self.a_volUp == 0 and self.a_volDown == 0 and self.a_switchLastKey == 0:
          ADDON.setSetting(id="record_key", value=str(self.key))
          self.getControl(7007).setLabel(str(self.key))
          self.getControl(7007).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(8007).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(9007).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.a_rec = 0
       if self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_list == 1 and self.a_volUp == 0 and self.a_volDown == 0 and self.a_switchLastKey == 0:
          ADDON.setSetting(id="list_key", value=str(self.key))
          self.getControl(7021).setLabel(str(self.key))
          self.getControl(7021).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(8021).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(9021).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.a_list = 0
       if self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_list == 0 and self.a_volUp == 1 and self.a_volDown == 0 and self.a_switchLastKey == 0:
          ADDON.setSetting(id="volume_up_key", value=str(self.key))
          self.getControl(7009).setLabel(str(self.key))
          self.getControl(7009).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(8009).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(9009).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.a_volUp = 0
       if self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_list == 0 and self.a_volUp == 0 and self.a_volDown == 1 and self.a_switchLastKey == 0:
          ADDON.setSetting(id="volume_down_key", value=str(self.key))
          self.getControl(7010).setLabel(str(self.key))
          self.getControl(7010).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(8010).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(9010).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.a_volDown = 0
       if self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_list == 0 and self.a_volUp == 0 and self.a_volDown == 0 and self.a_switchLastKey == 1:
          ADDON.setSetting(id="switch_to_last_key", value=str(self.key))
          self.getControl(7020).setLabel(str(self.key))
          self.getControl(7020).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(8020).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.getControl(9020).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=False pulse=True')])
          self.a_switchLastKey = 0

  def onClick(self, controlId):
        if controlId == 9001 and self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_list == 0 and self.a_volUp == 0 and self.a_volDown == 0 and self.a_switchLastKey == 0:
            self.a_info = 1
            self.getControl(7001).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(8001).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(9001).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
        if controlId == 9002 and self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_list == 0 and self.a_volUp == 0 and self.a_volDown == 0 and self.a_switchLastKey == 0:
            self.a_stop = 1
            self.getControl(7002).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(8002).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(9002).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
        if controlId == 9003 and self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_list == 0 and self.a_volUp == 0 and self.a_volDown == 0 and self.a_switchLastKey == 0:
            self.a_pp = 1
            self.getControl(7003).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(8003).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(9003).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
        if controlId == 9004 and self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_list == 0 and self.a_volUp == 0 and self.a_volDown == 0 and self.a_switchLastKey == 0:
            self.a_pm = 1
            self.getControl(7004).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(8004).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(9004).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
        if controlId == 9005 and self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_list == 0 and self.a_volUp == 0 and self.a_volDown == 0 and self.a_switchLastKey == 0:
            self.a_home = 1
            self.getControl(7005).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(8005).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(9005).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])

        if controlId == 9006 and self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_list == 0 and self.a_volUp == 0 and self.a_volDown == 0 and self.a_switchLastKey == 0:
            self.a_ctxt = 1
            self.getControl(7006).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(8006).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(9006).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])

        if controlId == 9007 and self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_list == 0 and self.a_volUp == 0 and self.a_volDown == 0 and self.a_switchLastKey == 0:
            self.a_rec = 1
            self.getControl(7007).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(8007).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(9007).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])

        if controlId == 9021 and self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_list == 0 and self.a_volUp == 0 and self.a_volDown == 0 and self.a_switchLastKey == 0:
            self.a_list = 1
            self.getControl(7021).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(8021).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(9021).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])

        if controlId == 9020 and self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_list == 0 and self.a_volUp == 0 and self.a_volDown == 0 and self.a_switchLastKey == 0:
            self.a_switchLastKey = 1
            self.getControl(7020).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(8020).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(9020).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])

        if controlId == 9008 and self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_list == 0 and self.a_volUp == 0 and self.a_volDown == 0 and self.a_switchLastKey == 0:
            deb('Key settings reset!')
            ADDON.setSetting(id="info_key", value=str(''))
            ADDON.setSetting(id="stop_key", value=str(''))
            ADDON.setSetting(id="pp_key", value=str(''))
            ADDON.setSetting(id="pm_key", value=str(''))
            ADDON.setSetting(id="home_key", value=str(''))
            ADDON.setSetting(id="context_key", value=str(''))
            ADDON.setSetting(id="record_key", value=str(''))
            ADDON.setSetting(id="list_key", value=str(''))
            ADDON.setSetting(id="volume_up_key", value=str(''))
            ADDON.setSetting(id="volume_down_key", value=str(''))
            ADDON.setSetting(id="switch_to_last_key", value=str(''))
            self.close()
            xbmcgui.Dialog().ok(strings(31013),"\n" + strings(310014))

        if controlId == 9009 and self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_list == 0 and self.a_volUp == 0 and self.a_volDown == 0 and self.a_switchLastKey == 0:
            self.a_volUp = 1
            self.getControl(7009).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(8009).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(9009).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])

        if controlId == 9010 and self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_list == 0 and self.a_volUp == 0 and self.a_volDown == 0 and self.a_switchLastKey == 0:
            self.a_volDown = 1
            self.getControl(7010).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(8010).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])
            self.getControl(9010).setAnimations([('Conditional', 'effect=fade start=0 end=100 time=1000 condition=True pulse=True')])

        if controlId == 9099 and self.a_info == 0 and self.a_stop == 0 and self.a_pp == 0 and self.a_pm == 0 and self.a_home == 0 and self.a_ctxt == 0 and self.a_rec == 0 and self.a_list == 0 and self.a_volUp == 0 and self.a_volDown == 0 and self.a_switchLastKey == 0:
            self.close()


if __name__ == '__main__':
    dialog = KeyListener()
    dialog.doModal()
    del dialog
