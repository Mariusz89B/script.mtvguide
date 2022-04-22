#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2018 Mariusz89B
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
    PY3 = True
else:
    PY3 = False

if PY3: 
    import urllib.request, urllib.error, urllib.parse, http.client, http.cookiejar
else:
    import urllib, urllib2, httplib
    import cookielib

import os, sys, io, re, socket, copy, threading
import time, datetime
import xbmc, xbmcgui, xbmcvfs
from unidecode import unidecode
from xml.etree import ElementTree
from collections import OrderedDict
from strings import *
from groups import *
import simplejson as json
import strings as strings2
import zlib
import ast
import codecs

try:
    import ssl
except:
    pass

if PY3:
    urllibURLError = urllib.error.URLError
    urllibHTTPError = urllib.error.HTTPError
    httplibBadStatusLine = http.client.BadStatusLine
    httplibIncompleteRead = http.client.IncompleteRead
else:
    urllibURLError = urllib2.URLError
    urllibHTTPError = urllib2.HTTPError
    httplibBadStatusLine = httplib.BadStatusLine
    httplibIncompleteRead = httplib.IncompleteRead

HOST        = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36 Edg/98.0.1108.50'
pathAddons  = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'addons.ini')
pathMapBase = os.path.join(ADDON.getAddonInfo('path'), 'resources')

if PY3:
    try:
        PROFILE_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
    except:
        PROFILE_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')
else:
    try:
        PROFILE_PATH = xbmc.translatePath(ADDON.getAddonInfo('profile'))
    except:
        PROFILE_PATH = xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')

if PY3:
    try:
        pathMapExtraBase  = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
    except:
        pathMapExtraBase  = xbmcvfs.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')
else:
    try:
        pathMapExtraBase  = xbmc.translatePath(ADDON.getAddonInfo('profile'))
    except:
        pathMapExtraBase  = xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')

onlineMapPathBase = M_TVGUIDE_SUPPORT + 'maps/'

try:
    MAX_CONNECTION_TIME = int(ADDON.getSetting('max_connection_time'))
except:
    MAX_CONNECTION_TIME = 30

HTTP_ConnectionTimeout = 10

BASE_LIST = []

CC_DICT = ccDict()

for k, v in CC_DICT.items():
    cc = ADDON.getSetting('country_code_{}'.format(k.lower()))
    if cc == 'true' and cc != '':
        BASE_LIST.append(k)

XXX = ADDON.getSetting('XXX_EPG')
if XXX != '' and XXX != 'false':
    XXX_EPG = True
else:
    XXX_EPG = False

VOD = ADDON.getSetting('VOD_EPG')
if VOD != '' and XXX != 'false':
    VOD_EPG = True
else:
    VOD_EPG = False

class ShowList:
    def __init__(self, logCall=deb):
        self.logCall = logCall

    def decode(self, string):
        json_ustr = json.dumps(string, ensure_ascii=False)
        return json_ustr

    def JsonToSortedTab(self, json):
        strTab = []
        outTab = []
        for v,k in json.items():
            strTab.append(int(v))
            strTab.append(k)
            outTab.append(strTab)
            strTab = []
        outTab.sort(key=lambda x: x[0])
        return outTab

    def getJsonFromAPI(self, url, post={}):
        result_json = None
        raw_json = None

        try:
            if PY3:
                data     = urllib.parse.urlencode(post).encode("utf-8")
                reqUrl   = urllib.request.Request(url, data)
            else:
                data     = urllib.urlencode(post)
                reqUrl   = urllib2.Request(url, data)

            reqUrl.add_header('User-Agent', HOST)
            reqUrl.add_header('Keep-Alive', 'timeout=60')
            reqUrl.add_header('Connection', 'Keep-Alive')
            reqUrl.add_header('authority', 'raw.githubusercontent.com')
            reqUrl.add_header('upgrade-insecure-requests', '1')

            startTime = datetime.datetime.now()
            while (datetime.datetime.now() - startTime).seconds < MAX_CONNECTION_TIME and strings2.M_TVGUIDE_CLOSING == False:
                try:
                    if PY3:
                        raw_json = urllib.request.urlopen(reqUrl, timeout = HTTP_ConnectionTimeout)
                    else:
                        raw_json = urllib2.urlopen(reqUrl, timeout = HTTP_ConnectionTimeout)
                    content_json = raw_json.read()
                    if raw_json.headers.get("Content-Encoding", "") == "gzip":
                        content_json = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(content_json)

                    result_json = json.loads(content_json)
                    raw_json.close()
                    break
                except (httplibIncompleteRead, socket.timeout) as ex:
                    self.logCall('ShowList getJsonFromAPI exception: %s - retrying seconds = %s' % (str(ex), (datetime.datetime.now() - startTime).seconds))

                except urllibHTTPError as ex:
                    if ex.code in [500, 408]:
                        self.logCall('ShowList getJsonFromAPI exception: %s - retrying seconds = %s' % (str(ex), (datetime.datetime.now() - startTime).seconds))
                    else:
                        raise

                except urllibURLError as ex:
                    if 'timed out' in str(ex) or 'Timeout' in str(ex):
                        self.logCall('ShowList getJsonFromAPI exception: %s - retrying seconds = %s' % (str(ex), (datetime.datetime.now() - startTime).seconds))
                    else:
                        raise

                try:
                    if raw_json:
                        raw_json.close()
                        raw_json = None
                except:
                    pass
                if strings2.M_TVGUIDE_CLOSING:
                    self.logCall('ShowList getJsonFromAPI M_TVGUIDE_CLOSING - aborting!')
                    break
                xbmc.sleep(150)

        except (urllibURLError, NameError, ValueError, httplibBadStatusLine) as ex:
            self.logCall('ShowList getJsonFromAPI exception: %s - aborting!' % str(ex))
            return None
        return result_json

    def getJsonFromExtendedAPI(self, url, post_data = None, save_cookie = False, load_cookie = False, cookieFile = None, jsonLoadsResult = False, jsonLoadResult = False, customHeaders = None, max_conn_time = MAX_CONNECTION_TIME, getResponseUrl=False, skipSslCertificate=False, json_dumps_post=False, http_timeout=HTTP_ConnectionTimeout, verbose=True):
        result_json = None
        raw_json = None
        customOpeners = []
        if PY3:
            cj = http.cookiejar.LWPCookieJar()
        else:
            cj = cookielib.LWPCookieJar()

        url = url.replace(' ','%20')

        def urlOpen(req, customOpeners):
            if skipSslCertificate and sys.version_info >= (2, 7, 9):
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                if PY3:
                    customOpeners += [urllib.request.HTTPSHandler(context=ctx)]
                else:
                    customOpeners += [urllib2.HTTPSHandler(context=ctx)]

            if len(customOpeners) > 0:
                if PY3:
                    opener = urllib.request.build_opener( *customOpeners )
                else:
                    opener = urllib2.build_opener( *customOpeners )
                response = opener.open(req, timeout = http_timeout)
            else:
                try:
                    if PY3:
                        response = urllib.request.urlopen(req, timeout = http_timeout)
                    else:
                        response = urllib2.urlopen(req, timeout = http_timeout)
                except:
                    response = None

            return response

        try:
            if cookieFile is not None:
                if PY3:
                    customOpeners.append( urllib.request.HTTPCookieProcessor(cj) )
                else:
                    customOpeners.append( urllib2.HTTPCookieProcessor(cj) )
                if load_cookie == True and cookieFile is not None and os.path.isfile(cookieFile):
                    cj.load(cookieFile, ignore_discard = True)

            if customHeaders is not None:
                headers = customHeaders
            else:
                headers = { 'User-Agent' : HOST }
                headers['Keep-Alive'] = 'timeout=60'
                headers['Connection'] = 'Keep-Alive'
                headers['authority'] = 'raw.githubusercontent.com'
                headers['upgrade-insecure-requests'] = '1'

            if json_dumps_post:
                if PY3:
                    data = json.dumps(post_data).encode("utf-8")
                else:
                    data = json.dumps(post_data)
            elif post_data:
                if PY3:
                    data = urllib.parse.urlencode(post_data).encode("utf-8")
                else:
                    data = urllib.urlencode(post_data)
            else:
                data = None

            if PY3:
                reqUrl = urllib.request.Request(url=url, data=data, headers=headers)
            else:
                reqUrl = urllib2.Request(url=url, data=data, headers=headers)

            startTime = datetime.datetime.now()
            while (datetime.datetime.now() - startTime).seconds < max_conn_time and strings2.M_TVGUIDE_CLOSING == False:
                try:
                    raw_json = urlOpen(reqUrl, customOpeners)
                    if raw_json:
                        if getResponseUrl:
                            result = raw_json.geturl()
                            raw_json.close()
                            return result
                        result_json = raw_json.read()
                        if raw_json.headers.get("Content-Encoding", "") == "gzip":
                            result_json = zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(result_json)

                        if jsonLoadsResult == True:
                            result_json = json.loads(result_json)
                        raw_json.close()
                        break
                    else:
                        result_json = None
                        return result_json
                except (httplibIncompleteRead, socket.timeout) as ex:
                    if verbose:
                        self.logCall('ShowList getJsonFromExtendedAPI exception: %s, url: %s - retrying seconds = %s' % (str(ex), url, (datetime.datetime.now() - startTime).seconds))

                except urllibHTTPError as ex:
                    if ex.code in [500, 408]:
                        if verbose:
                            self.logCall('ShowList getJsonFromExtendedAPI exception: %s, url: %s - retrying seconds = %s' % (str(ex), url, (datetime.datetime.now() - startTime).seconds))
                    else:
                        raise

                except urllibURLError as ex:
                    if 'timed out' in str(ex) or 'Timeout' in str(ex):
                        if verbose:
                            self.logCall('ShowList getJsonFromExtendedAPI exception: %s, url: %s - retrying seconds = %s' % (str(ex), url, (datetime.datetime.now() - startTime).seconds))
                    else:
                        raise

                try:
                    if raw_json:
                        raw_json.close()
                        raw_json = None
                except:
                    pass
                if strings2.M_TVGUIDE_CLOSING:
                    self.logCall('ShowList getJsonFromExtendedAPI M_TVGUIDE_CLOSING - aborting!')
                    break
                xbmc.sleep(150)

            if cookieFile is not None and save_cookie == True:
                cj.save(cookieFile, ignore_discard = True)

        except (urllibURLError, NameError, ValueError, httplibBadStatusLine) as ex:
            if verbose:
                self.logCall('ShowList getJsonFromExtendedAPI exception: %s - aborting!' % str(ex))
            return None

        return result_json

    def getCookieItem(self, cookiefile, item = None):
        ret = ''
        if os.path.isfile(cookiefile):
            if PY3:
                cj = http.cookiejar.LWPCookieJar()
            else:
                cj = cookielib.LWPCookieJar()
            cj.load(cookiefile, ignore_discard = True)
            for cookie in cj:
                if not item:
                    ret += '%s=%s;' % (cookie.name, cookie.value)
                elif cookie.name == item:
                    ret = cookie.value
        return ret

    def downloadUrl(self, url, retryFailed = True):
        fileContent = None
        try:
            if PY3: 
                reqUrl   = urllib.request.Request(url)
            else:
                reqUrl   = urllib2.Request(url)

            reqUrl.add_header('User-Agent', HOST)
            reqUrl.add_header('Keep-Alive', 'timeout=25')
            reqUrl.add_header('authority', 'raw.githubusercontent.com')
            reqUrl.add_header('upgrade-insecure-requests', '1')
            reqUrl.add_header('Connection', 'Keep-Alive')

            if PY3: 
                urlFile = urllib.request.urlopen(reqUrl, timeout=HTTP_ConnectionTimeout)
            else:
                urlFile = urllib2.urlopen(reqUrl, timeout=HTTP_ConnectionTimeout)

            fileContent = urlFile.read()
            urlFile.close()

        except Exception as ex:
            self.logCall('File download error, exception: %s, url: %s' % (str(ex), url))
            fileContent = None
            if not strings2.M_TVGUIDE_CLOSING and retryFailed == True and ('HTTP Error 500' in str(ex) or 'HTTP Error 408' in str(ex) or 'timeout' in str(ex) or 'IncompleteRead' in str(ex)):
                return self.downloadUrl(url, retryFailed=False)

        return fileContent

    def parseDOM(self, html, name="", attrs={}, ret=False):
        # Copyright (C) 2010-2011 Tobias Ussing And Henrik Mosgaard Jensen
        if isinstance(html, str):   
            try:
                html = [html] # Replace with chardet thingy
            except:
                html = [html]
        elif isinstance(html, str):
            html = [html]
        elif not isinstance(html, list):
            return ""

        if not name.strip():
            return ""

        ret_lst = []
        for item in html:
            temp_item = re.compile('(<[^>]*?\n[^>]*?>)').findall(item)
            for match in temp_item:
                item = item.replace(match, match.replace("\n", " "))

            lst = []
            for key in attrs:
                lst2 = re.compile('(<' + name + '[^>]*?(?:' + key + '=[\'"]' + attrs[key] + '[\'"].*?>))', re.M | re.S).findall(item)
                if len(lst2) == 0 and attrs[key].find(" ") == -1:  # Try matching without quotation marks
                    lst2 = re.compile('(<' + name + '[^>]*?(?:' + key + '=' + attrs[key] + '.*?>))', re.M | re.S).findall(item)

                if len(lst) == 0:
                    lst = lst2
                    lst2 = []
                else:
                    test = list(range(len(lst)))
                    test.reverse()
                    for i in test:  # Delete anything missing from the next list.
                        if not lst[i] in lst2:
                            del(lst[i])

            if len(lst) == 0 and attrs == {}:
                lst = re.compile('(<' + name + '>)', re.M | re.S).findall(item)
                if len(lst) == 0:
                    lst = re.compile('(<' + name + ' .*?>)', re.M | re.S).findall(item)

            if isinstance(ret, str):
                lst2 = []
                for match in lst:
                    attr_lst = re.compile('<' + name + '.*?' + ret + '=([\'"].[^>]*?[\'"])>', re.M | re.S).findall(match)
                    if len(attr_lst) == 0:
                        attr_lst = re.compile('<' + name + '.*?' + ret + '=(.[^>]*?)>', re.M | re.S).findall(match)
                    for tmp in attr_lst:
                        cont_char = tmp[0]
                        if cont_char in "'\"":
                            # Limit down to next variable.
                            if tmp.find('=' + cont_char, tmp.find(cont_char, 1)) > -1:
                                tmp = tmp[:tmp.find('=' + cont_char, tmp.find(cont_char, 1))]

                            # Limit to the last quotation mark
                            if tmp.rfind(cont_char, 1) > -1:
                                tmp = tmp[1:tmp.rfind(cont_char)]
                        else:
                            if tmp.find(" ") > 0:
                                tmp = tmp[:tmp.find(" ")]
                            elif tmp.find("/") > 0:
                                tmp = tmp[:tmp.find("/")]
                            elif tmp.find(">") > 0:
                                tmp = tmp[:tmp.find(">")]

                        lst2.append(tmp.strip())
                lst = lst2
            else:
                lst2 = []
                for match in lst:
                    endstr = "</" + name

                    start = item.find(match)
                    end = item.find(endstr, start)
                    pos = item.find("<" + name, start + 1 )

                    while pos < end and pos != -1:
                        tend = item.find(endstr, end + len(endstr))
                        if tend != -1:
                            end = tend
                        pos = item.find("<" + name, pos + 1)

                    if start == -1 and end == -1:
                        temp = ""
                    elif start > -1 and end > -1:
                        temp = item[start + len(match):end]
                    elif end > -1:
                        temp = item[:end]
                    elif start > -1:
                        temp = item[start + len(match):]

                    if ret:
                        endstr = item[end:item.find(">", item.find(endstr)) + 1]
                        temp = match + temp + endstr

                    item = item[item.find(temp, item.find(match)) + len(temp):]
                    lst2.append(temp)
                lst = lst2
            ret_lst += lst

        return ret_lst

class TvCid:
    def __init__(self, cid, name, title, strm="", catchup="", lic="", img=""):
        self.cid = cid
        self.name = unidecode(name)
        self.title = unidecode(title)
        self.strm = strm
        self.catchup = catchup
        self.lic = lic
        self.src = ""
        self.img = img
        self.rtmpdumpLink = None
        self.ffmpegdumpLink = None

class MapString:
    def __init__(self, channelid, titleRegex, strm, src, displayName=None):
        self.channelid = channelid
        self.titleRegex = titleRegex
        self.strm = strm
        self.src = src
        self.displayName = displayName

    @staticmethod
    def FastParse(xmlstr, epg_channels=None, logCall=deb):
        rstrm = ''
        categories = {}
        if logCall:
            logCall('\n\n')
            logCall('[UPD] Parsing basemap file')
            logCall('-------------------------------------------------------------------------------------')

        if PY3:
            xmlstr = xmlstr.decode('utf-8')
        else:
            xmlstr = xmlstr if isinstance(xmlstr, unicode) else xmlstr.decode('utf-8')

        if logCall:
            logCall('[UPD] %-35s %-50s %-35s' % ('-TITLE-', '-REGEX-', '-STRM-'))

        result = list()

        if epg_channels is not None:
            for title, titles in epg_channels:
                string_xml = '\n<channel id="{}" title="" strm=""/>'.format(title)
                xmlstr += string_xml

                if titles:
                    string_xml = '\n<channel id="{0}" title="" titles="{1}" strm=""/>'.format(title, titles)
                    xmlstr += string_xml

        channelRe       = re.compile('(<channel.*?/>)', re.DOTALL)
        channelIdRe     = re.compile('<channel\sid="(.*?)"', re.DOTALL)
        channelTitleRe  = re.compile('title="(.*?)"', re.DOTALL)
        channelTitlesRe = re.compile('titles="(.*?)"', re.DOTALL)
        channelStrmRe   = re.compile('strm="(.*?)"/>', re.DOTALL)

        channels = channelRe.findall(xmlstr)

        for channel in channels:
            r = channelIdRe.search(channel)
            aid = r.group(1) if r else ''

            for achannel in aid.split(', '):
                r = channelTitleRe.search(channel)
                atitle = r.group(1) if r else ''

                r = channelTitlesRe.search(channel)
                atitles = r.group(1) if r else ''

                r = channelStrmRe.search(channel)
                astrm = r.group(1) if r else ''

                if logCall:
                    try:
                        logCall('[UPD] %-35s %-50s %-35s' % (achannel, atitle, astrm))
                    except:
                        logCall('[UPD] %-35s %-50s %-35s' % (achannel.decode('utf-8'), atitle, astrm))

                if atitles == '':
                    result.append(MapString(channelid=achannel, titleRegex=atitle, strm=astrm, src='', displayName=''))
                else:
                    for dtitle in atitles.split(', '):
                        result.append(MapString(channelid=achannel, titleRegex=atitle, strm=astrm, src='', displayName=dtitle))

                rstrm = astrm

        categoriesRe    = re.compile('(<category name=".*?".*tags=".*?"/>)')
        categoryRe      = re.compile('<category name="(.*?)"', re.DOTALL)
        tagsRe          = re.compile('tags="(.*?)"/>', re.DOTALL)

        category = categoriesRe.findall(xmlstr)

        for cat in category:
            category_tags_set = set()
            category_name = categoryRe.search(cat).group(1)
            category_tags = tagsRe.search(cat).group(1).split('|')
            for tag in category_tags:
                category_tags_set.add(('' + tag.lower()))
            categories[category_name] = category_tags_set

        if logCall:
            logCall('-------------------------------------------------------------------------------------')

        return [result, rstrm, categories]

    @staticmethod
    def loadFile(path, logCall=deb):
        try:
            logCall('[UPD] Loading basemap => mtvguide: %s' % path)
            logCall('\n')
            with open(path, 'rb') as content_file:
                content = content_file.read()

        except Exception as ex:
            logCall('loadFile exception: %s' % getExceptionString())
            content = ""
        return content

class SleepSupervisor(object):
    def __init__(self, stopCallback):
        self.stopPlaybackCall = stopCallback
        self.sleepEnabled = ADDON.getSetting('sleep__enabled')
        self.sleepAction = ADDON.getSetting('sleep__action')
        self.sleepTimer = int(ADDON.getSetting('sleep_timer')) * 60 #time in secs
        self.timer = None
        self.actions = {
            '0': 'PlayerControl(Stop)',
            '1': 'Quit',
            '2': 'Powerdown',
            '3': 'Suspend'
        }
        try:
            self.action = self.actions[self.sleepAction]
        except KeyError:
            self.action = 'PlayerControl(Stop)'
        deb('SleepSupervisor timer init: sleepEnabled %s, sleepAction: %s, sleepTimer: %s' % (self.sleepEnabled, self.action, self.sleepTimer))

    def Start(self):
        if self.sleepEnabled == 'true' and self.sleepTimer > 0:
            self.Stop()
            debug('SleepSupervisor timer Start, action = %s' % self.action)
            self.timer = threading.Timer(self.sleepTimer, self.sleepTimeout)
            self.timer.start()

    def Stop(self):
        if self.timer:
            self.timer.cancel()
            self.timer = None
            debug('SleepSupervisor timer Stop')

    def sleepTimeout(self):
        deb('SleepSupervisor sleepTimeout, executing action: %s' % self.action)
        self.timer = None
        self.stopPlaybackCall()
        xbmc.executebuiltin('%s' % self.action)

class baseServiceUpdater:
    locker = threading.Lock()
    logLocker = threading.Lock()
    baseMapContent = None
    categories = None
    def __init__(self):
        self.sl = ShowList(self.log)
        self.login = ''
        self.password = ''
        self.highQuality = 'true'
        self.url = ''
        self.thread = None
        self.serviceRegex = ''
        self.servicePriority = int(0)
        self.traceList = list()
        self.rstrm = ''
        self.forcePrintintingLog = False
        self.printLogTimer = None
        self.useOnlineMap = True
        self.maxAllowedStreams = 1
        self.addDuplicatesToList = False
        self.addDuplicatesAtBeginningOfList = False
        self.serviceEnabled   = 'false'
        self.baseMapFile      = 'basemap.xml'
        self.adultMapFile     = 'adultmap.xml'
        self.vodMapFile       = 'vodmap.xml'
        self.extraMapFile     = 'basemap_extra.xml'
        self.automap = list()
        self.mapsLoaded  = False
        self.channelList = None
        self.channels    = None
        self.refreshingStreams = False
        try:
            self.onlineMapFile = onlineMapPathBase + self.localMapFile
        except:
            self.log('baseServiceUpdater self.localMapFile is not defined!!!')
            self.onlineMapFile = ''
            self.localMapFile  = ''
        try:
            self.serviceRegex  = "service=" + self.serviceName + "&cid=%"
            self.rstrm         = self.serviceRegex + 's'
        except:
            self.log('baseServiceUpdater self.serviceName is not defined!!!')
            self.serviceName   = 'baseService'
            self.serviceRegex  = ''
            self.rstrm         = ''

    def waitUntilDone(self):
        if self.thread is not None:
            return self.thread.join()

    def log(self, message):
        if self.thread is not None and self.thread.is_alive() and self.forcePrintintingLog == False:
            self.traceList.append(self.__class__.__name__ + ' ' + message)
        else:
            deb(self.__class__.__name__ + ' ' + message)

    def printLog(self):
        baseServiceUpdater.logLocker.acquire()
        for trace in self.traceList:
            deb(trace)
        baseServiceUpdater.logLocker.release()
        del self.traceList[:]
        self.traceList = list()

    def wrongService(self):
        self.log('wrong service selected: {}'.format(self.serviceName))
        xbmcgui.Dialog().notification(self.serviceName, strings(SERVICE_WRONG), xbmcgui.NOTIFICATION_WARNING, time=15000, sound=True)

    def connErrorMessage(self):
        self.log('connection error for service: {}'.format(self.serviceName))
        xbmcgui.Dialog().notification(self.serviceName, strings(SERVICE_ERROR), xbmcgui.NOTIFICATION_WARNING, time=15000, sound=True)

    def loginErrorMessage(self):
        self.log('login error for service: {}'.format(self.serviceName))
        xbmcgui.Dialog().notification(self.serviceName, strings(SERVICE_LOGIN_INCORRECT), xbmcgui.NOTIFICATION_WARNING, time=15000, sound=True)

    def maxDeviceIdMessage(self):
        self.log('max amount of devices added: {}'.format(self.serviceName))
        xbmcgui.Dialog().notification(self.serviceName, strings(SERVICE_MAX_DEVICE_ID), xbmcgui.NOTIFICATION_WARNING, time=15000, sound=True)

    def proxyErrorMessage(self):
        self.log('proxy error for service: {}'.format(self.serviceName))
        xbmcgui.Dialog().notification(self.serviceName, strings(SERVICE_PROXY_BLOCK), sound=False)

    def geoBlockErrorMessage(self):
        self.log('geoblock error for service: {}'.format(self.serviceName))
        xbmcgui.Dialog().notification(self.serviceName, strings(SERVICE_GEO_BLOCK), sound=False)

    def noPremiumMessage(self):
        self.log('no premium for service: {}'.format(self.serviceName))
        xbmcgui.Dialog().notification(self.serviceName, strings(SERVICE_NO_PREMIUM), sound=False)

    def noContentMessage(self):
        self.log('no content for service: {}'.format(self.serviceName))
        xbmcgui.Dialog().notification(self.serviceName, strings(SERVICE_NO_CONTENT), sound=False)

    def startLoadingChannelList(self, automap, cache):
        if self.thread is None or not self.thread.is_alive():
            self.traceList.append('\n')
            self.traceList.append('##############################################################################################################')
            self.traceList.append('\n')
            if cache:
                self.thread = threading.Thread(name='cachedChannelList thread', target = self.cachedChannelList, args=(automap,))
            else:
                self.thread = threading.Thread(name='loadChannelList thread', target = self.loadChannelList, args=(automap,))
            self.thread.start()
            self.printLogTimer = threading.Timer(15, self.printLogTimeout)
            self.printLogTimer.start()

    def printLogTimeout(self):
        self.printLogTimer = None
        self.forcePrintintingLog = True
        self.printLog()

    def close(self):
        if self.printLogTimer is not None:
            self.printLogTimer.cancel()
        self.printLog()
        self.forcePrintintingLog = True
        self.refreshingStreams = False

    def unlockService(self):
        pass

    def resetService(self):
        self.automap = list()
        self.channelList = None
        self.mapsLoaded = False
        self.refreshingStreams = True
        self.forcePrintintingLog = False

    def getCategoriesFromMap(self):
        if not baseServiceUpdater.categories:
            self.getBaseMap()
        return baseServiceUpdater.categories

    def getBaseMap(self, epg_channels=None):
        baseServiceUpdater.locker.acquire()

        self.log('\n')
        if not baseServiceUpdater.baseMapContent:
            baseServiceUpdater.baseMapContent = list()
            baseServiceUpdater.categories = {}

            self.loadSingleBaseMap('base', self.baseMapFile, epg_channels)

            if XXX_EPG:
                self.loadSingleBaseMap('adult', self.adultMapFile)

            if VOD_EPG:
                self.loadSingleBaseMap('vod', self.vodMapFile)

            for k in BASE_LIST:
                self.loadSingleBaseMap('base_' + k.lower(), 'basemap_{}.xml'.format(k.lower()))

            self.loadExtraBaseMap('base_extra', self.extraMapFile)

        else:
            self.log('loading cached base map')

        baseServiceUpdater.locker.release()
        return copy.deepcopy(baseServiceUpdater.baseMapContent)

    def loadSingleBaseMap(self, lang, mapFilePath, epg_channels=None):
        self.log('Loading {} channel map'.format(lang))
        entries = None
        map = ""

        localMapFilename      = os.path.join(pathMapBase, mapFilePath)
        onlineMapFilename     = onlineMapPathBase + mapFilePath
        map                   = self.sl.getJsonFromExtendedAPI(onlineMapFilename, max_conn_time=9, http_timeout=5, verbose=False)

        if map:
            self.log('successfully downloaded online {} map file: {}'.format(lang, onlineMapFilename))

        if xbmcvfs.exists(localMapFilename):
            map += MapString.loadFile(localMapFilename, self.log)

        else:
            map += MapString.loadFile(os.path.join(pathMapBase, 'basemap.xml'), self.log)
            self.log('{} file download failed - using local map: {}'.format(lang, localMapFilename))

        entries, _, seCat         = MapString.FastParse(map, epg_channels, False)

        if entries is not None:
            baseServiceUpdater.baseMapContent.extend(entries)
            for id in seCat:
                if id in baseServiceUpdater.categories:
                    baseServiceUpdater.categories[id].update(seCat[id])
                else:
                    baseServiceUpdater.categories[id] = seCat[id]

    def loadExtraBaseMap(self, lang, mapFilePath):
        self.log('Loading {} channel map'.format(lang))
        if not xbmcvfs.exists(os.path.join(pathMapExtraBase, mapFilePath)):
            xbmcvfs.copy(os.path.join(pathMapBase, mapFilePath), os.path.join(pathMapExtraBase, mapFilePath))
        localMapFilename      = os.path.join(pathMapExtraBase, mapFilePath)
        map                   = MapString.loadFile(localMapFilename, self.log)
        entries, _, seCat         = MapString.FastParse(map, None, False)
        baseServiceUpdater.baseMapContent.extend(entries)
        for id in seCat:
            if id in baseServiceUpdater.categories:
                baseServiceUpdater.categories[id].update(seCat[id])
            else:
                baseServiceUpdater.categories[id] = seCat[id]


    def loadMapFile(self, epg_channels=None):
        try:
            if not self.mapsLoaded:
                self.automap = self.getBaseMap(epg_channels)

                if self.useOnlineMap:
                    dedicatedMapfile = self.sl.getJsonFromExtendedAPI(self.onlineMapFile, max_conn_time=6, verbose=False)
                else:
                    dedicatedMapfile = None

                if dedicatedMapfile is None:
                    dedicatedMapFilename = os.path.join(pathMapBase, self.localMapFile)
                    if os.path.isfile(dedicatedMapFilename):
                        if self.useOnlineMap:
                            self.log('loadMapFile: dedicated map download failed - using local map')
                        dedicatedMapfile = MapString.loadFile(dedicatedMapFilename, self.log)
                    else:
                        dedicatedMapfile = None
                        self.log('loadMapFile: dedicated map doesnt exist - using just base map')
                else:
                    self.log('loadMapFile: success downloading online map file: %s' % self.onlineMapFile)

                if dedicatedMapfile:
                    if not self.refreshingStreams:
                        dedicatedMap, rstrm, _ = MapString.FastParse(dedicatedMapfile, None, False) #self.log)
                    else:
                        #Avoid printing content of map to log on every refresh
                        dedicatedMap, rstrm, _ = MapString.FastParse(dedicatedMapfile, None, False)
                    for dedicatedEntry in dedicatedMap:
                        for baseEntry in self.automap:
                            if dedicatedEntry.channelid == baseEntry.channelid:
                                self.automap.remove(baseEntry)
                                break
                    self.automap.extend(dedicatedMap)

                    if not self.rstrm or self.rstrm == '':
                        self.rstrm = rstrm

                self.mapsLoaded = True

        except Exception as ex:
            self.log('loadMapFile: Error %s' % getExceptionString())

    def isChannelListStillValid(self):
        return True

    def getDisplayName(self):
        try:
            return self.serviceDisplayName
        except:
            pass 
        return self.serviceName

    def getBaseChannelList(self, silent=False, returnCopy=True, cache=False):
        result = list()
        try:
            if cache and 'playlist_' in self.serviceName:
                cachefile = os.path.join(PROFILE_PATH, 'playlists', '{playlist}.m3u'.format(playlist=self.serviceName))
                cachepath = os.path.join(PROFILE_PATH, 'playlists', '{playlist}.cache'.format(playlist=self.serviceName))
                if os.path.exists(cachepath) and os.path.exists(cachefile):
                    if PY3:
                        with open(cachepath, 'r', encoding='utf-8') as f:
                            data = [line.strip() for line in f]
                    else:
                        with codecs.open(cachepath, 'r', encoding='utf-8') as f:
                            data = [line.strip() for line in f]

                    cachedList = []
                    for line in data:
                        y = ast.literal_eval(line)
                        cachedList.append(TvCid(cid=y[0], name=y[1], title=y[2], strm=y[3], catchup=y[4]))

                    self.channelList = cachedList

                else:
                    if not cache:
                        if os.path.exists(cachepath):
                            os.remove(cachepath)

            if self.channelList and self.isChannelListStillValid():
                self.log('getBaseChannelList return cached channel list')
                if returnCopy:
                    return copy.deepcopy(self.channelList)
                else:
                    return self.channelList

            tmpresult = self.getChannelList(silent)
            if len(tmpresult) > 0:
                result = tmpresult

            self.channelList = copy.deepcopy(result)
        except:
            self.log('getBaseChannelList exception: %s' % getExceptionString())

        if 'playlist_' in self.serviceName:
            refr = ADDON.getSetting('{playlist}_refr'.format(playlist=self.serviceName))
            if refr == 'true':
                self.cache = threading.Thread(name='saveCacheList thread', target = self.saveCacheList, args=(self.channelList, self.serviceName,))
                self.cache.start()

        return result

    def saveCacheList(self, result, serviceName):
        cachedList = ([[y.cid, y.name, y.title, y.strm, y.catchup] for y in result])

        cachepath = os.path.join(PROFILE_PATH, 'playlists', '{playlist}.cache'.format(playlist=serviceName))
        if PY3:
            with open(cachepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join([str(i) for i in cachedList]))
        else:
            with codecs.open(cachepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join([str(i) for i in cachedList]))

    def decodeString(self, s):
        if sys.version_info[0] < 3:
            s = s if isinstance(s, unicode) else s.decode('utf-8')

        return s

    def cachedChannelList(self, epg_channels=None):
        startTime = datetime.datetime.now()

        self.channels = self.getBaseChannelList(cache=True)
        if len(self.channels) <= 0:
            self.log('loadChannelList error lodaing channel list for service {} - aborting!'.format(self.serviceName))
            self.close()
            return

        if strings2.M_TVGUIDE_CLOSING:
            self.log('loadChannelList service {} requested abort!'.format(self.serviceName))
            self.close()
            return

        self.log('Loading channel list took: %s seconds' % (datetime.datetime.now() - startTime).seconds)

    def loadChannelList(self, epg_channels=None):
        from re import match

        try:
            startTime = datetime.datetime.now()
            self.channels = self.getBaseChannelList()
            if len(self.channels) <= 0:
                self.log('loadChannelList error lodaing channel list for service {} - aborting!'.format(self.serviceName))
                self.close()
                return

            if strings2.M_TVGUIDE_CLOSING:
                self.log('loadChannelList service {} requested abort!'.format(self.serviceName))
                self.close()
                return

            self.log('Loading channel list took: %s seconds' % (datetime.datetime.now() - startTime).seconds)
            self.loadMapFile(epg_channels)
            self.log('Loading channels and map took: %s seconds' % (datetime.datetime.now() - startTime).seconds)

            self.log('\n\n')
            self.log('[UPD] Matched streams')
            self.log('-------------------------------------------------------------------------------------')
            self.log('[UPD]     %-40s %-40s %-35s' % ('-TITLE-', '-ORIG NAME-', '-SERVICE-'))

            channelList = []
            filtered_channels = []

            for x in self.automap[:]:
                if strings2.M_TVGUIDE_CLOSING:
                    self.log('loadChannelList loop service {} requested abort!'.format(self.serviceName))
                    self.close()
                    return

                if x.strm != '':
                    x.src = 'CONST'
                    self.log('[UPD]     %-40s %-12s %-35s' % (unidecode(x.channelid), x.src, x.strm))
                    continue

                try:
                    if x.titleRegex:
                        filtered_channels = [z for z in self.channels if match(x.titleRegex, z.title, re.IGNORECASE)]
                        if x.displayName != '':
                            filtered_channels = [z for z in self.channels if match(x.titleRegex, z.name, re.IGNORECASE)]

                    elif x.displayName:
                        try:
                            filtered_channels = [z for z in self.channels if unidecode(x.displayName.upper()) == unidecode(z.title.upper())]
                        except:
                            filtered_channels = [z for z in self.channels if unidecode(x.displayName.upper()) == unidecode(self.decodeString(z.title).upper())]
                        if not filtered_channels:
                            try:
                                filtered_channels = [z for z in self.channels if unidecode(x.displayName.upper()) == unidecode(z.name.upper())]
                            except:
                                filtered_channels = [z for z in self.channels if unidecode(x.displayName.upper()) == unidecode(self.decodeString(z.name).upper())]


                    elif x.displayName == '':
                        try:
                            filtered_channels = [z for z in self.channels if unidecode(x.channelid.upper()) == unidecode(z.title.upper())]
                        except:
                            filtered_channels = [z for z in self.channels if unidecode(x.channelid.upper()) == unidecode(self.decodeString(z.title).upper())]
                        if not filtered_channels:
                            try:
                                filtered_channels = [z for z in self.channels if unidecode(x.channelid.upper()) == unidecode(z.name.upper())]
                            except:
                                filtered_channels = [z for z in self.channels if unidecode(x.channelid.upper()) == unidecode(self.decodeString(z.name).upper())]

                    for y in filtered_channels:
                        if x.strm != '' and self.addDuplicatesToList:
                            newMapElement = copy.deepcopy(x)
                            newMapElement.strm = self.rstrm % y.cid

                            y.src = newMapElement.src
                            y.strm = newMapElement.strm

                            try:
                                self.log('[UPD] [B] %-40s %-40s %-35s ' % (unidecode(newMapElement.channelid), unidecode(y.title), newMapElement.strm))
                            except:
                                self.log('[UPD] [B] %-40s %-40s %-35s ' % (unidecode(newMapElement.channelid), unidecode(self.decodeString(y.title)), newMapElement.strm))
                            if not self.addDuplicatesAtBeginningOfList:
                                self.automap.append(newMapElement)
                            else:
                                self.automap.insert(0, newMapElement)
                        else:
                            x.strm = self.rstrm % y.cid
                            y.strm = x.strm
                            x.src  = self.serviceName
                            y.src = x.src

                            try:
                                if y.strm == '':
                                    y.strm == 'None'
                                try:
                                    channelList.append(unidecode(y.title) + ', ' + y.strm)
                                except:
                                    channelList.append(unidecode(self.decodeString(y.title)) + ', ' + y.strm)
                            except:
                                pass

                            try:
                                self.log('[UPD]     %-40s %-40s %-35s ' % (unidecode(x.channelid), unidecode(y.title), x.strm))
                            except:
                                self.log('[UPD]     %-40s %-40s %-35s ' % (unidecode(x.channelid), unidecode(self.decodeString(y.title)), x.strm))

                except Exception as ex:
                    self.log('{} Error: {} {}'.format(unidecode(x.channelid), x.titleRegex, getExceptionString()))

            self.log('-------------------------------------------------------------------------------------')
            self.log('\n\n')

            self.printNotMatched = threading.Thread(name='notMatched thread', target = self.notMatched, args=(channelList,))
            self.printNotMatched.start()

            self.log('-------------------------------------------------------------------------------------')
            self.log("[UPD] The analysis has been completed...")
            self.log('Loading everything took: %s seconds' % (datetime.datetime.now() - startTime).seconds)
            self.log('\n')

        except Exception as ex:
            self.log('loadChannelList exception: {}'.format(getExceptionString()))
        self.close()

    def notMatched(self, channelList):
        self.log('[UPD] Not matched streams for {} channels:'.format(self.serviceName))
        self.log('-------------------------------------------------------------------------------------')
        self.log('[UPD]     %-40s %-40s %-12s %-35s' % ('-TITLE-', '-ORIG NAME-', '-CID-', '-STRM-'))

        file_name = os.path.join(pathMapExtraBase, 'custom_channels.list')
        if not os.path.exists(pathMapExtraBase):
            os.makedirs(pathMapExtraBase)

        for y in self.channels:
            if y.src == '' or y.src != self.serviceName:
                if y.title != '':
                    try:
                        if y.strm == '':
                            y.strm == 'None'
                        try:
                            channelList.append(unidecode(y.title) + ', ' + y.strm)
                        except:
                            channelList.append(unidecode(self.decodeString(y.title)) + ', ' + y.strm)
                    except:
                        pass

                    try:
                        self.log('[UPD]     %-40s %-40s %-12s %-35s' % (unidecode(y.title.upper()), unidecode(y.name), y.cid, y.strm))
                    except:
                        self.log('[UPD]     %-40s %-40s %-12s %-35s' % (unidecode(self.decodeString(y.title.upper())), unidecode(self.decodeString(y.name)), y.cid, y.strm))

        channelList = list(OrderedDict.fromkeys(channelList))

        if PY3:
            with open(file_name, 'ab+') as f:
                f.seek(0)
                data = f.read()
                if len(data) > 0:
                    f.write(bytearray('\n', 'utf-8'))
                f.write(bytearray('\n'.join(channelList), 'utf-8'))
        else:
            newline = False

            try:
                with open(file_name, 'r') as f:
                    data = f.read()
                    if len(data) > 0:
                        newline = True
            except:
                pass

            with open(file_name, 'a') as f:
                f.seek(0)
                if newline:
                    f.write(str('\n'))
                f.write(str('\n'.join(channelList)))

        self.log('-------------------------------------------------------------------------------------')

    def getChannel(self, cid, service=None):
        try:
            channels = self.getBaseChannelList(silent=True, returnCopy=False)
            for chann in channels:
                if chann.cid == cid:
                    return self.getChannelStream(copy.deepcopy(chann))
            self.log('ERROR getChannel not found cid: {} in channel list!'.format(cid))
        except:
            self.log('getChannel exception: {}'.format(getExceptionString()))
        return None