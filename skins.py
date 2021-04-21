#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2016 Andrzej Mleczko

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
    import io
else:
    import StringIO

import os, re, shutil, zipfile
import xbmcgui, xbmc, xbmcvfs
from strings import *
from serviceLib import ShowList

ACTION_UP = 3
ACTION_DOWN = 4
ACTION_PAGE_UP = 5
ACTION_PAGE_DOWN = 6
ACTION_SELECT_ITEM = 7
ACTION_PARENT_DIR = 9
ACTION_PREVIOUS_MENU = 10
KEY_NAV_BACK = 92
ACTION_MOUSE_WHEEL_UP = 104
ACTION_MOUSE_WHEEL_DOWN = 105

SKIN_IMAGE_CONTROL_ID = 5000
SKIN_NAME_CONTROL_ID = 5001

NAV_DOWN_BUTTON = 9000
NAV_UP_BUTTON = 9001
MOUSE_SELECT_BUTTON = 9002

try:
    skin_resolution = '1080i'
except:
    skin_resolution = '720p'

class SkinObject:
    def __init__(self, name, url="", version="", minGuideVersion="", icon = "", fanart="", description = ""):
        self.name = name
        self.url = url
        self.version = version
        self.icon = icon
        self.fanart = fanart
        self.description = description
        self.minGuideVersion = minGuideVersion

    def __eq__(self, other):
        return self.name == other.name

class Skin:
    if sys.version_info[0] > 2:
        try:
            PROFILE_PATH  = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
        except:
            PROFILE_PATH  = xbmcvfs.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')
    else:
        try:
            PROFILE_PATH  = xbmc.translatePath(ADDON.getAddonInfo('profile'))
        except:
            PROFILE_PATH  = xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')

    ADDON_EMBEDDED_SKINS    = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'skins')

    ADDON_CUSTOM_SKINS_RES  = os.path.join(PROFILE_PATH, 'resources')
    ADDON_CUSTOM_SKINS      = os.path.join(ADDON_CUSTOM_SKINS_RES, 'skins')

    if KODI_VERSION >= 17:
        NEW_SKINS_BASE_URL      = M_TVGUIDE_SUPPORT + 'skins_v9/'

    NEW_SKINS_URL           = NEW_SKINS_BASE_URL + 'skinlist.xml'

    CURRENT_SKIN            = ADDON.getSetting('Skin')
    CURRENT_SKIN_DIR        = None
    CURRENT_SKIN_BASE_DIR   = None
    SKIN_XML_REGEX          = 'skin\s*name\s*=\s*"(.+?)"\s*url\s*=\s*"(.+?)"\s*version\s*=\s*"(.+?)"\s*mTVGuideVersion\s*=\s*"(.+?)"\s*icon\s*=\s*"(.*?)"\s*fanart\s*=\s*"(.*?)"\s*description\s*=\s*"(.*?)"'

    @staticmethod
    def getSkinPath():
        if Skin.CURRENT_SKIN_DIR is None:
            if os.path.isdir(os.path.join(Skin.ADDON_CUSTOM_SKINS, Skin.CURRENT_SKIN)):
                Skin.CURRENT_SKIN_DIR = os.path.join(Skin.ADDON_CUSTOM_SKINS, Skin.CURRENT_SKIN)
                Skin.CURRENT_SKIN_BASE_DIR = Skin.PROFILE_PATH
            elif os.path.isdir(os.path.join(Skin.ADDON_EMBEDDED_SKINS, Skin.CURRENT_SKIN)):
                Skin.CURRENT_SKIN_DIR = os.path.join(Skin.ADDON_EMBEDDED_SKINS, Skin.CURRENT_SKIN)
                Skin.CURRENT_SKIN_BASE_DIR = ADDON.getAddonInfo('path')

        return Skin.CURRENT_SKIN_DIR

    @staticmethod
    def getDefaultSkinBaseDir():
        if os.path.isdir(os.path.join(Skin.ADDON_CUSTOM_SKINS, 'skin.default')):
            return Skin.PROFILE_PATH
        else:
            return ADDON.getAddonInfo('path')

    @staticmethod
    def getSkinBasePath():
        if Skin.CURRENT_SKIN_BASE_DIR is None:
            Skin.getSkinPath()
        return Skin.CURRENT_SKIN_BASE_DIR

    @staticmethod
    def removeSkinsIfKodiVersionChanged():
        if ADDON.getSetting('kodi_version') != str(KODI_VERSION):
            deb('Detected new Kodi version, removing all skins')
            Skin.deleteCustomSkins(False)
            ADDON.setSetting(id="kodi_version", value=str(KODI_VERSION))

    @staticmethod
    def removeSkinsIfAddonVersionChanged():
        if ADDON.getSetting('mtvguide_version') != str(90100):
            deb('Detected new Kodi version, removing all skins')
            Skin.deleteCustomSkins(False)
            ADDON.setSetting(id="mtvguide_version", value=str(90100))

            if sys.version_info[0] > 2:
                try:
                    profilePath  = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
                except:
                    profilePath  = xbmcvfs.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')
            else:
                try:
                    profilePath  = xbmc.translatePath(ADDON.getAddonInfo('profile'))
                except:
                    profilePath  = xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')
            
            try:
                file = xbmcvfs.File(os.path.join(profilePath, 'fonts.list'), 'w+')
                file.write('')
                file.close()
            except:
                deb('Error: fonts.list is missing')

    @staticmethod
    def fixSkinIfNeeded():
        Skin.removeSkinsIfKodiVersionChanged()
        Skin.removeSkinsIfAddonVersionChanged()
        Skin.createCustomDirIfNeeded()
        if Skin.getSkinPath() is None:
            deb('Skins fixing skin!')
            success = False
            deb('Missing skin: %s' % Skin.getSkinName())
            skins = Skin.getSkinList()
            for skin in skins:
                #deb('Checking skin: %s, guideVersion: %s' % (skin.name, skin.minGuideVersion))
                if skin.name == Skin.getSkinName():
                    deb('Skin found online skin which is missing: %s, starting download!' % skin.name)
                    success = Skin.downloadSkin(skin)
                    xbmcgui.Dialog().notification(strings(30710), strings(30709) + ": " + skin.name, time=7000, sound=False)

            if success == False:
                ADDON.setSetting(id="Skin", value=str('skin.default'))
                xbmcgui.Dialog().ok(strings(LOAD_ERROR_TITLE), strings(SKIN_ERROR_LINE1), strings(SKIN_ERROR_LINE4))
                quit()

    @staticmethod
    def createCustomDirIfNeeded():
        if os.path.isdir(Skin.ADDON_CUSTOM_SKINS) == False:
            deb('Skins creating custom skin dir!')
            if os.path.isdir(Skin.ADDON_CUSTOM_SKINS_RES) == False:
                if os.path.isdir(Skin.PROFILE_PATH) == False:
                    os.makedirs(Skin.PROFILE_PATH)
                os.makedirs(Skin.ADDON_CUSTOM_SKINS_RES)
            os.makedirs(Skin.ADDON_CUSTOM_SKINS)
            try:
                shutil.copytree(os.path.join(Skin.ADDON_EMBEDDED_SKINS, 'skin.default'), os.path.join(Skin.ADDON_CUSTOM_SKINS, 'skin.default'))
            except Exception as ex:
                deb('Skins exception: %s' % getExceptionString())

    @staticmethod
    def selectSkin():
        picker = SkinPicker()
        picker.doModal()
        picker.close()

    @staticmethod
    def getCurrentSkinsList():
        Skin.createCustomDirIfNeeded()
        embedded_skins = os.listdir(Skin.ADDON_EMBEDDED_SKINS)
        custom_skins = os.listdir(Skin.ADDON_CUSTOM_SKINS)
        skin_list = list()

        for skin in custom_skins:
            deb('Skins custom %s' % skin)
            image = os.path.join(Skin.ADDON_CUSTOM_SKINS, skin, 'fanart.jpg')
            if not os.path.isfile(image):
                image = os.path.join(Skin.NEW_SKINS_BASE_URL, skin, 'fanart.jpg')
            icon = os.path.join(Skin.ADDON_CUSTOM_SKINS, skin, 'name.png')
            if not os.path.isfile(icon):
                icon = os.path.join(Skin.NEW_SKINS_BASE_URL, skin, 'name.png')
            skin_list.append(SkinObject(skin, icon=icon, fanart=image))

        for skin in embedded_skins:
            deb('Skins basic: %s' % skin)
            if skin not in custom_skins:
                image = os.path.join(Skin.ADDON_EMBEDDED_SKINS, skin, 'fanart.jpg')
                if not os.path.isfile(image):
                    image = os.path.join(Skin.NEW_SKINS_BASE_URL, skin, 'fanart.jpg')
                icon = os.path.join(Skin.ADDON_EMBEDDED_SKINS, skin, 'name.png')
                if not os.path.isfile(icon):
                    icon = os.path.join(Skin.NEW_SKINS_BASE_URL, skin, 'name.png')
                skin_list.append(SkinObject(skin, icon=icon, fanart=image))
            else:
                deb('Skipping skin %s since its duplicated' % skin)
        return skin_list

    @staticmethod
    def downloadSkin(skinToDownload):
        Skin.createCustomDirIfNeeded()
        skin_to_download = Skin.NEW_SKINS_BASE_URL + skinToDownload.url
        deb('Downloading skin from: %s' % skin_to_download)
        downloader = ShowList()
        skin_zip = downloader.getJsonFromExtendedAPI(skin_to_download)
        if skin_zip:
            if sys.version_info[0] > 2:
                skin_zip = io.BytesIO(skin_zip)
            else:
                skin_zip = StringIO.StringIO(skin_zip)
            skin_zip = zipfile.ZipFile(skin_zip)
            for name in skin_zip.namelist():
                deb('Skins extracting file: %s' % name)
                try:
                    skin_zip.extract(name, Skin.ADDON_CUSTOM_SKINS)
                except:
                    deb('Unable to extract file: %s, exception: %s' % (name, getExceptionString()) )

            skin_zip.close()
            return True
        else:
            deb('Failed to download skin')
        return False

    @staticmethod
    def setAddonSkin(skinName):
        ADDON.setSetting(id="Skin", value=skinName)
        deb('Settings skin: %s' % skinName)

    @staticmethod
    def getSkinName():
        return Skin.CURRENT_SKIN

    @staticmethod
    def getSkinList():
        deb('getSkinList')
        skin_list = list()
        matching_skins = list()
        downloader = ShowList()
        xml = downloader.getJsonFromExtendedAPI(Skin.NEW_SKINS_URL)
        if xml:
            xml = xml.decode('utf-8')
            #deb('Decoded XML is %s' % xml)
            items = re.compile(Skin.SKIN_XML_REGEX).findall(xml)

            for item in items:
                #deb('Skin in XML: %s' % str(item))
                skin_list.append(SkinObject(name=str(item[0]), url=str(item[1]), version=float(item[2]), minGuideVersion=Skin.parseVersion(item[3]), icon=(Skin.NEW_SKINS_BASE_URL + item[4]).replace(' ', '%20'), fanart=(Skin.NEW_SKINS_BASE_URL + item[5]).replace(' ', '%20'), description=item[6]))
                #deb('Skin: %s, img: %s' % ( skin_list[len(skin_list)-1].name, skin_list[len(skin_list)-1].icon ))
        else:
            deb('Failed to download online skin list')

        currentGuideVersion   = Skin.getCurrentGuideVersion()
        for skin in skin_list:
            addSkin = True
            if skin.minGuideVersion > currentGuideVersion:
                addSkin = False
                continue

            for skin2 in skin_list:
                if skin.name == skin2.name:
                    if skin.version != skin2.version:
                        #we dont compare same skin isinstance
                        if skin.version < skin2.version:
                            #newer version is available
                            addSkin = False
                            break

            if addSkin:
                matching_skins.append(skin)

        return matching_skins

    @staticmethod
    def checkForUpdates():
        import threading
        threading.Timer(0, Skin._checkForUpdates).start()

    @staticmethod
    def _checkForUpdates():
        deb('_checkForUpdates')
        skins = Skin.getSkinList()
        regex = re.compile('version\s*=\s*(.*)', re.IGNORECASE)
        usedSkinUpdated = False
        for skin in skins:
            iniFile = os.path.join(Skin.ADDON_CUSTOM_SKINS, skin.name, 'settings.ini')
            if os.path.isfile(iniFile):
                try:
                    fileContent = open(iniFile, 'r').read()
                except:
                    continue
                localVersion = float(regex.search(fileContent).group(1))
                if skin.version > localVersion:
                    deb('Skin: %s, local version: %s, online version: %s - downloading new version' % (skin.name, localVersion, skin.version))
                    success = Skin.downloadSkin(skin)
                    if success:
                        xbmcgui.Dialog().notification(strings(30702), strings(30709) + ": " + skin.name, time=7000, sound=False)
                    if success and skin.name == Skin.getSkinName():
                        usedSkinUpdated = True
        if usedSkinUpdated:
            if not xbmc.getCondVisibility('Window.IsVisible(yesnodialog)'):
                xbmcgui.Dialog().ok(strings(30709), strings(30979))
                exit()
        deb('Skin finished update')

    @staticmethod
    def parseVersion(version):
        regex = re.compile('(\d*)\.(\d*)\.(\d*)', re.IGNORECASE)
        items = regex.findall(version)
        for item in items:
            return [int(item[0]), int(item[1]), int(item[2])]
        return [int(0), int(0), int(0)]

    @staticmethod
    def getCurrentGuideVersion():
        return Skin.parseVersion(ADDON.getAddonInfo('version'))

    @staticmethod
    def deleteCustomSkins(show_dialog):
        if os.path.isdir(Skin.ADDON_CUSTOM_SKINS_RES):
            try:
                shutil.rmtree(Skin.ADDON_CUSTOM_SKINS_RES)
            except:
                pass
        if show_dialog:
            xbmcgui.Dialog().ok(strings(31004), strings(30969))


class SkinPicker(xbmcgui.WindowXMLDialog):
    def __new__(cls):
        return super(SkinPicker, cls).__new__(cls, 'script-tvguide-skins.xml', Skin.getSkinBasePath(), Skin.getSkinName(), defaultRes=skin_resolution)

    def __init__(self):
        self.go_down_control = None
        self.go_up_control = None
        self.select_control = None
        self.currentlySelectedSkin = None
        self.skin_image_control = None
        self.download_skin_list = self.getDownloadSkinList()
        self.skin_list = self.getAllSkinList()

    def onInit(self):
        self.go_down_control = self.getControl(NAV_DOWN_BUTTON)
        self.go_up_control = self.getControl(NAV_UP_BUTTON)
        self.select_control = self.getControl(MOUSE_SELECT_BUTTON)
        self.skin_image_control = self.getControl(SKIN_IMAGE_CONTROL_ID)
        self.skin_name_control = self.getControl(SKIN_NAME_CONTROL_ID)
        self.resetVisibleSkin()

    def resetVisibleSkin(self):
        if len(self.skin_list) > 0:
            self.currentlySelectedSkin = self.skin_list[0]
        else:
             self.currentlySelectedSkin = None
        self.updateVisibleSkin()

    def showNextSkin(self):
        try:
            currentIndex = self.skin_list.index(self.currentlySelectedSkin)
            newIndex = currentIndex + 1
            if(newIndex < len(self.skin_list)):
                self.currentlySelectedSkin = self.skin_list[newIndex]
            self.updateVisibleSkin()
        except:
            self.resetVisibleSkin()

    def showPreviousSkin(self):
        try:
            currentIndex = self.skin_list.index(self.currentlySelectedSkin)
            newIndex = currentIndex -1
            if(newIndex >= 0):
                self.currentlySelectedSkin = self.skin_list[newIndex]
            self.updateVisibleSkin()
        except:
            self.resetVisibleSkin()

    def updateVisibleSkin(self):
        if self.currentlySelectedSkin is not None:
            self.setFanartImage(self.currentlySelectedSkin)

    def setFanartImage(self, skin):
        if skin:
            self.skin_image_control.setImage(skin.fanart)
            self.skin_name_control.setImage(skin.icon)

    def setCurrentSkin(self):
        try:
            if self.currentlySelectedSkin is not None:
                success = True
                if self.currentlySelectedSkin in self.download_skin_list:
                    success = Skin.downloadSkin(self.currentlySelectedSkin)
                    if success:
                        xbmcgui.Dialog().notification(strings(30710), strings(30709) + ": " + self.currentlySelectedSkin.name, time=7000, sound=False)
                if success:
                    Skin.setAddonSkin(self.currentlySelectedSkin.name)
                    if sys.version_info[0] > 2:
                        try:
                            profilePath  = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
                        except:
                            profilePath  = xbmcvfs.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')
                    else:
                        try:
                            profilePath  = xbmc.translatePath(ADDON.getAddonInfo('profile'))
                        except:
                            profilePath  = xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')
                    try:
                        file = os.path.join(profilePath, 'fonts.list')
                        os.remove(file)
                    except:
                        deb('Error: fonts.list is missing')

                else:
                    deb('Failed to wnload skin %s' % self.currentlySelectedSkin.name)
            else:
                deb('setCurrentSkin selected skin is none!')
        except:
            deb('setCurrentSkin exception: %s' % getExceptionString() )


    def onClick(self, controlId):
        deb('onClick controlId: %s' % controlId )
        clicked_control = self.getControl(controlId).getId()

        if clicked_control == self.go_down_control.getId():
            deb('SkinPicker godown control')
            self.showNextSkin()
        elif clicked_control == self.go_up_control.getId():
            deb('SkinPicker goup control')
            self.showPreviousSkin()
        elif clicked_control == self.select_control.getId():
            deb('SkinPicker select control')
            self.setCurrentSkin()
            self.close()


    def getAllSkinList(self):
        skin_list = Skin.getCurrentSkinsList()
        try:
            if self.download_skin_list is None:
                download_list = self.getDownloadSkinList()
            else:
                download_list = self.download_skin_list
            if download_list is not None:
                skin_list.extend(download_list)
            else:
                deb('getAllSkinList getDownloadSkinList returned none')
        except:
            pass
        return skin_list


    def getDownloadSkinList(self):
        deb('getDownloadSkinList')
        download_list = Skin.getSkinList()
        current_list = Skin.getCurrentSkinsList()
        for skin_to_download in download_list[:]:
            try:
                current_list.index(skin_to_download)
                download_list.remove(skin_to_download)
                deb('SkinPicker Skin removing skin: %s from download list since its already installed!' % skin_to_download.name)
            except:
                pass
        return download_list


    def onAction(self, action):
        deb('SkinPicker onAction actId %d, buttonCode %d' % (action.getId(), action.getButtonCode()))
        if action.getId() in [ACTION_PARENT_DIR, KEY_NAV_BACK, ACTION_PREVIOUS_MENU]:
            self.close()

        elif action.getId() in [ACTION_MOUSE_WHEEL_UP, ACTION_PAGE_UP, ACTION_UP]:
            self.showPreviousSkin()

        elif action.getId() in [ACTION_DOWN, ACTION_MOUSE_WHEEL_DOWN, ACTION_PAGE_DOWN]:
            self.showNextSkin()

        elif action.getId() in [ACTION_SELECT_ITEM]:
            self.setCurrentSkin()
            self.close()


    def close(self):
        super(SkinPicker, self).close()


if len(sys.argv) > 1 and sys.argv[1] == 'SelectSkin':
    #Skin._checkForUpdates()
    Skin.selectSkin()

    if sys.version_info[0] > 2:
        try:
            profilePath  = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
        except:
            profilePath  = xbmcvfs.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')
    else:
        try:
            profilePath  = xbmc.translatePath(ADDON.getAddonInfo('profile'))
        except:
            profilePath  = xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')

    currentSkin = xbmc.getSkinDir()
    try:
        with open(os.path.join(profilePath, 'skin_fonts.ini'), "r") as f:
            lines = f.readlines()
            lines.remove(currentSkin+'\n')
            with open(os.path.join(profilePath, 'skin_fonts.ini'), "w") as new_f:
                for line in lines:        
                    new_f.write(line)
    except:
        None
elif len(sys.argv) > 1 and sys.argv[1] == 'DeleteSkins':
    Skin.deleteCustomSkins(True)
