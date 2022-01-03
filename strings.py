#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2019 Mariusz89B
#   Copyright (C) 2014 Krzysztof Cebulski
#   Copyright (C) 2013 Szakalit
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

import xbmcaddon, xbmc
import traceback, sys

ADDON_ID            = 'script.mtvguide'
RSS_FILE            = 'http://mods-kodi.pl/infusions/kodi_info/kodi_info.txt' 
RSS_FILE_BACKUP     = 'https://raw.githubusercontent.com/Mariusz89B/script.mtvguide-support/main/kodi_info.txt'
M_TVGUIDE_SUPPORT   = 'https://raw.githubusercontent.com/Mariusz89B/script.mtvguide-support/main/'
ADDON               = xbmcaddon.Addon(id = ADDON_ID)
ADDON_PATH          = ADDON.getAddonInfo('path')
ADDON_CIDUPDATED    = False    #zabezpieczenie przed ponownym updatem cidow
ADDON_AUTOSTART     = False    #zabezpieczenie przed ponownym uruchomieniem wtyczki
FORCE_ADD_LOG_DEBUG = True     #True - Logowanie nawet jezeli wylaczone debugowanie w XBMC
global M_TVGUIDE_CLOSING
M_TVGUIDE_CLOSING   = False

KODI_VERSION        = int(xbmc.getInfoLabel("System.BuildVersion").split(".")[0])

RSS_MESSAGE = 30504
NO_DESCRIPTION = 30000
NO_CATEGORY = 30164
CALCULATING_REMAINING_TIME = 30002
TIME_LEFT = 30003
BACKGROUND_UPDATE_IN_PROGRESS = 30004

NO_STREAM_AVAILABLE_TITLE = 30100
NO_STREAM_AVAILABLE_LINE1 = 30101
NO_STREAM_AVAILABLE_LINE2 = 30102

CLEAR_CACHE = 30104
CLEAR_NOTIFICATIONS = 30108
CLEAR_DB = 30950
DONE = 30105
DONE_DB = 30951

DB_DELETED = 30955

LOAD_ERROR_TITLE = 30150
LOAD_ERROR_LINE1 = 30151
LOAD_ERROR_LINE2 = 30152
CONFIGURATION_ERROR_LINE2 = 30153
EPG_FORMAT_ERROR = 69069
LOAD_NOT_CRITICAL_ERROR = 30160
LOAD_CRITICAL_ERROR = 30161

SKIN_ERROR_LINE1 = 30154
SKIN_ERROR_LINE2 = 30155
SKIN_ERROR_LINE3 = 30156
SKIN_ERROR_LINE4 = 30149

NOTIFICATION_5_MINS = 30200
NOTIFICATION_NOW = 30201
NOTIFICATION_POPUP_NAME = 30202
NOTIFICATION_POPUP_QUESTION = 30203
NOTIFICATION_CANCEL = 30204

RECORDED_FILE_POPUP = 310012
RECORDED_FILE_QUESTION = 310013
RECORD_PROGRAM_STRING = 69039
RECORD_PROGRAM_CANCEL_STRING = 30303

DOWNLOAD_PROGRAM_STRING = 69056
DOWNLOAD_PROGRAM_CANCEL_STRING = 69057

WATCH_CHANNEL = 30300
REMIND_PROGRAM = 30301
DONT_REMIND_PROGRAM = 30302
CHOOSE_STRM_FILE = 30304
REMOVE_STRM_FILE = 30306

PREVIEW_STREAM = 30604
STOP_PREVIEW = 30607

WEEBTV_WEBTV_MISSING_1 = 30802
WEEBTV_WEBTV_MISSING_2 = 30803
WEEBTV_WEBTV_MISSING_3 = 30804

SERVICE_WRONG = 57041
SERVICE_ERROR = 57042
SERVICE_NO_PREMIUM = 57039
SERVICE_LOGIN_INCORRECT = 57048
SERVICE_PROXY_BLOCK = 57053
SERVICE_GEO_BLOCK = 57054
SERVICE_MAX_DEVICE_ID = 57055
SERVICE_NO_CONTENT = 57040

DATABASE_SCHEMA_ERROR_1 = 30157
DATABASE_SCHEMA_ERROR_2 = 30158
DATABASE_SCHEMA_ERROR_3 = 30159

#Controls ID
C_MAIN_SERVICE_NAME = 4918  
C_MAIN_CHAN_NAME = 4919     #nazwa kanalu
C_MAIN_TITLE = 4920         #nazwa programu telewizyjnego
C_MAIN_TIME = 4921          #godziny trwania progrmay
C_MAIN_DESCRIPTION = 4922   #opis programu tv
C_MAIN_IMAGE = 4923         #obraz programu
C_MAIN_LOGO = 4924          #logo programu
C_MAIN_LIVE = 4944          #na zywo
C_PROGRAM_SLIDER = 4998     #slider dla postepu programu
C_PROGRAM_PROGRESS = 4999   #postep programu w info i vosd

C_PROGRAM_EPISODE  = 4925   #odcinek
C_PROGRAM_CATEGORY = 4926   #kategoria
C_PROGRAM_ACTORS = 4928     #aktorzy
C_PROGRAM_PRODUCTION_DATE = 4929    #data produkcji
C_PROGRAM_DIRECTOR = 4930   #rezyser
C_PROGRAM_AGE_ICON = 4932   #od lat
C_PROGRAM_RATING = 4933     #ocena
C_VOSD_SERVICE = 4940       #nazwa serwisu
C_MAIN_CHAN_PLAY = 4952     #kanal odtwarzany
C_MAIN_PROG_PLAY = 4953     #program odtwarzany
C_MAIN_TIME_PLAY = 4954     #czas odtwarzanego programu
C_MAIN_NUMB_PLAY = 4955     #numer odtwarzanego kanalu

C_MAIN_DAY = 4960           #weekday
C_MAIN_REAL_DATE = 4961          #date

C_MAIN_PROGRAM_PROGRESS = 4230  #postep aktualnego programu aktywnego
C_MAIN_PROGRAM_PROGRESS_EPG = 4231  #postep programu wybrangeo w epg 
C_MAIN_CALC_TIME_EPG = 4232      #czas trwania programu w epg

C_MAIN_EPG = 5000

DEBUG = True

def strings(id, replacements = None):
    string = ADDON.getLocalizedString(id)
    if replacements is not None:
        return string.format(replacements)
    else:
        return string

def getStateLabel(control, label_idx, default=0):
    """Pobiera z <label2>1234|5678</label2> na podstawie label_idx odpowiednia wartosc
       Jezeli chcesz uzyc tylko jednej wartosci wpisz tak:  1234|
       Jezeli nie wpiszesz znaku | to label2 zostanie uznane za puste - nie moga byc same cyfry
    """
    try:
        values = control.getLabel2().split("|")
        return int(values[label_idx])
    except Exception:
        pass
    return default

def deb(s):
    if sys.version_info[0] > 2:
        try:
            xbmc.log("MTVGUIDE @ " + str(s), xbmc.LOGINFO)
        except:
            xbmc.log("MTVGUIDE @ " + str(s.encode('ascii', 'ignore')), xbmc.LOGINFO)
    else:
        try:
            xbmc.log("MTVGUIDE @ " + str(s), xbmc.LOGNOTICE)
        except:
            xbmc.log("MTVGUIDE @ " + str(s.encode('ascii', 'ignore')), xbmc.LOGNOTICE)

def debug(s):
    if sys.version_info[0] > 2:
        try:
            try:
                xbmc.log("Debug @ " + str(s), xbmc.LOGINFO)
            except:
                xbmc.log("Debug @ " + str(s.encode('ascii', 'ignore')), xbmc.LOGINFO)
        except:
            xbmc.log("Debug @ " + str(s.encode('ascii', 'ignore')), xbmc.LOGINFO)

    else:
        try:
            try:
                xbmc.log("Debug @ " + str(s), xbmc.LOGNOTICE)
            except:
                xbmc.log("Debug @ " + str(s.encode('ascii', 'ignore')), xbmc.LOGNOTICE)
        except:
            xbmc.log("Debug @ " + str(s.encode('ascii', 'ignore')), xbmc.LOGNOTICE)

def getExceptionString():
    except_string = ''
    try:
        (etype, value, traceback_obj) = sys.exc_info()
        excString = traceback.extract_tb(traceback_obj)
        except_string = ''.join(' %s, \nBacktrace: %s' % (str(value), str(excString)))
    except:
        pass
    return except_string