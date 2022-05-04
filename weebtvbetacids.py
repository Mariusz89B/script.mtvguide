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

import sys

if sys.version_info[0] > 2:
    PY3 = True
else:
    PY3 = False

if PY3:
    import urllib.request, urllib.parse, urllib.error
    from cmf3 import parseDOM
    from cmf3 import replaceHTMLCodes
else:
    import urllib2
    from cmf2 import parseDOM
    from cmf2 import replaceHTMLCodes    

import copy, re
import xbmcgui
from strings import *
from serviceLib import *
import requests
import json

serviceName = 'Weeb TV Beta'
url        = 'https://beta.weeb.tv'
jsonUrl    = url + '/channels'
playerUrl  = url + '/api/setPlayer?channel={}&format=json'

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.41 Safari/537.36 Edg/101.0.1210.32'

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

cacheFile = os.path.join(profilePath, 'cache.db')

sess = requests.Session()

class WeebTVBetaUpdater(baseServiceUpdater):
    def __init__(self):
        self.serviceName        = serviceName
        self.localMapFile       = 'weebtvbetamap.xml'
        baseServiceUpdater.__init__(self)
        self.serviceEnabled     = ADDON.getSetting('weebtvbeta_enabled')
        self.login              = ADDON.getSetting('weebtvbeta_username').strip()
        self.password           = ADDON.getSetting('weebtvbeta_password').strip()
        self.servicePriority    = int(ADDON.getSetting('priority_weebtvbeta'))
        self.url                = jsonUrl

    def saveToDB(self, table_name, value):
        import sqlite3
        import os
        if os.path.exists(cacheFile):
            os.remove(cacheFile)
        else:
            deb('File does not exists')
        conn = sqlite3.connect(cacheFile, detect_types=sqlite3.PARSE_DECLTYPES, cached_statements=20000)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS Cache(%s TEXT)' % table_name)
        c.execute("INSERT INTO Cache('%s') VALUES ('%s')" % (table_name, value))
        conn.commit()
        c.close()

    def readFromDB(self):
        import sqlite3
        conn = sqlite3.connect(cacheFile, detect_types=sqlite3.PARSE_DECLTYPES, cached_statements=20000)
        c = conn.cursor()
        c.execute("SELECT * FROM Cache")
        for row in c:
            if row:
                c.close()
                return row[0]

    def cookiesToString(self, cookies):
        try:
            return "; ".join([str(x) + "=" + str(y) for x, y in cookies.items()])
        except Exception as ex:
            deb('cookiesToString exception: ' + ex)
            return ''

    def loginService(self):
        cookies = {
            'weeb-tv_language': 'en',
            'weeb-tv_last_topic': 'privacy',
        }

        headers = {
            'authority': 'beta.weeb.tv',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6,fr;q=0.5',
            'dnt': '1',
            'origin': 'https://beta.weeb.tv',
            'referer': 'https://beta.weeb.tv/account/login',
            'user-agent': UA,
        }

        data = {
            'username': self.login,
            'userpassword': self.password,
            'option': 'do',
        }

        response = sess.post('https://beta.weeb.tv/account/login', cookies=cookies, headers=headers, data=data)

        statusRe = re.compile(r'Status konta:(.*?)<br>', re.DOTALL|re.MULTILINE)

        r = statusRe.search(response.text)
        status = r.group(1) if r else 'Free'

        if status == 'Free':
            xbmcgui.Dialog().notification('Weeb TV Beta', strings(59910))

        self.saveToDB('weebtv_cache', self.cookiesToString(response.cookies))
        return True

    def getChannelList(self, silent):
        result = list()

        if not self.loginService():
            return result

        self.log('\n\n')
        self.log('[UPD] Pobieram liste dostepnych kanalow Weeb.tv z %s' % self.url)
        self.log('[UPD] -------------------------------------------------------------------------------------')
        self.log('[UPD] %-15s %-35s %-30s' % ('-CID-', '-NAME-', '-TITLE-'))

        headers = {
            'authority': 'beta.weeb.tv',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6,fr;q=0.5',
            'dnt': '1',
            'user-agent': UA,
        }

        cookies = self.readFromDB()
        headers.update({'Cookie': cookies})

        html = requests.get(self.url + '/channel/', headers=headers, verify=False).text

        if html is None:
            self.log('getChannelList: Error while loading getJsonFromAPI Url: %s - aborting' % self.url)
            self.loginErrorMessage()
            return result

        try:
            channels = parseDOM(html, 'div', attrs={'class': "col-6 col-md-4 col-lg-2 pb-2"}) 
            for channel in channels:
                cid = parseDOM(channel, 'a', ret='href')[0].replace('https://beta.weeb.tv/channel/', '')
                name = parseDOM(channel, 'p', attrs={'class': "my-1 channelTitle"})[0].replace('<strong>', '').replace('</strong>', '')
                title = parseDOM(channel, 'p', attrs={'class': "my-1 channelTitle"})[0].replace('<strong>', '').replace('</strong>', '')+' PL'
                img = parseDOM(channel, 'img', ret='src')[0]

                program = TvCid(cid=cid, name=name, title=title, img=img)  
                result.append(program)

            if len(result) <= 0:
                self.log('Error while parsing service {}, returned data is: {}'.format(self.serviceName, str(html)))
                self.noPremiumMessage()

        except:
            self.log('getChannelList exception: {}'.format(getExceptionString()))
            self.noPremiumMessage()

        return result

    def getChannelStream(self, chann):
        data = None
        url = chann.cid
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0',
                'Accept': '*/*',
                'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
                'Origin': 'https://beta.weeb.tv',
                'DNT': '1',
                'Referer': 'https://beta.weeb.tv/',}

            cookies = self.readFromDB()
            headers.update({'Cookie': cookies})

            try:
                if PY3:
                    request = urllib.request.Request(playerUrl.format(url), headers = headers)
                    response = urllib.request.urlopen(request)

                else:
                    request = urllib2.Request(playerUrl.format(url), headers = headers)
                    response = urllib2.urlopen(request)

                html = response.read()

            except:
                html = None

            json_data = json.loads(html)

            if json_data.get('0', None) == -3 or html is None:
                xbmcgui.Dialog().notification(self.serviceName, strings(69037), time=5000)
                return None

            else:
                stream_url = json_data.get('10', None)
                try:
                    response = requests.get(stream_url, headers = headers, verify = False).text
                except:
                    xbmcgui.Dialog().notification(self.serviceName, strings(69037), time=5000)
                    return None

                if ADDON.getSetting('weebtvbeta_video_quality') == 'false':
                    jakoscstream_url = re.findall('RESOLUTION=(.*?)\\n(.*?)\\n', response, re.DOTALL + re.IGNORECASE)[0]
                    str_url_max = jakoscstream_url[max([(i) for i,v in enumerate(jakoscstream_url)])]
                else:
                    jakoscstream_url = re.findall('RESOLUTION=(.*?)\\n(.*?)\\n', response, re.DOTALL + re.IGNORECASE)
                    str_url_max = jakoscstream_url[max([(i) for i,v in enumerate(jakoscstream_url)])][1]

                chunk = re.findall('(.+?)\?to',str_url_max)[0]
                stream_url = stream_url.replace('playlist.m3u8',chunk)

                data = stream_url

            if data is not None and data != "":
                chann.strm = data
                self.log('getChannelStream found matching channel: cid: {}, name: {}, rtmp:{}'.format(chann.cid, chann.name, chann.strm))
                return chann
            else:
                self.log('getChannelStream error getting channel stream2, result: {}'.format(str(data)))
                return None

        except Exception as e:
            self.log('getChannelStream exception while looping: {}\n Data: {}'.format(getExceptionString(), str(data)))
        return None