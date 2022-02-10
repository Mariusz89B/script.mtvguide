#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2021 Mariusz89B
#   Copyright (C) 2020 mbebe

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

#   Disclaimer
#   This add-on is unoffical and is not endorsed or supported by TVN S.A. in any way. Any trademarks used belong to their owning companies and organisations.

from __future__ import unicode_literals

import sys

if sys.version_info[0] > 2:
    PY3 = True
else:
    PY3 = False
    
import xbmc, xbmcvfs

if PY3:
    import urllib.request, urllib.parse, urllib.error
    import http.cookiejar as cookielib
else:
    import urllib
    import cookielib

import os, copy, re

from strings import *
from serviceLib import *
from random import randrange
import requests
import base64
import json

serviceName         = 'PlayerPL'

UA = 'okhttp/3.3.1 Android'

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

sess = requests.Session()

timeouts = (15, 30)

class PlayerPLUpdater(baseServiceUpdater):
    def __init__(self):
        self.serviceName        = serviceName
        self.localMapFile       = 'basemap_pl.xml'
        baseServiceUpdater.__init__(self)
        self.serviceEnabled     = ADDON.getSetting('playerpl_enabled')
        self.servicePriority    = int(ADDON.getSetting('priority_playerpl'))
        self.api_base           = 'https://player.pl/playerapi/'
        self.login_api          = 'https://konto.tvn.pl/oauth/' 
        self.mylist             = None
        
        self.GETTOKEN = self.login_api + 'tvn-reverse-onetime-code/create'
        self.POSTTOKEN = self.login_api + 'token'
        self.SUBSCRIBER = self.api_base + 'subscriber/login/token'
        self.SUBSCRIBERDETAIL = self.api_base + 'subscriber/detail' 
        self.JINFO = self.api_base + 'info'
        self.TRANSLATE = self.api_base + 'item/translate'
        self.KATEGORIE = self.api_base + 'item/category/list'
        
        self.PRODUCTVODLIST = self.api_base + 'product/vod/list'
        self.PRODUCTLIVELIST= self.api_base + 'product/list/list'
        
        self.PARAMS = {'4K': 'true','platform': 'ANDROID_TV'}
        
        self.HEADERS3 = {
            'Host': 'konto.tvn.pl',
            'user-agent': UA,
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        
        self.ACCESS_TOKEN = ADDON.getSetting('playerpl_access_token')
        self.USER_PUB = ADDON.getSetting('playerpl_user_pub')
        self.USER_HASH = ADDON.getSetting('playerpl_user_hash')
        self.REFRESH_TOKEN = ADDON.getSetting('playerpl_refresh_token')
        self.DEVICE_ID = ADDON.getSetting('playerpl_device_id')
        self.TOKEN = ADDON.getSetting('playerpl_token')
        self.MAKER = ADDON.getSetting('playerpl_maker_id')
        self.USAGENT = ADDON.getSetting('playerpl_usagent_id')
        self.USAGENTVER = ADDON.getSetting('playerpl_usagentver_id')
        self.SELECTED_PROFILE = ADDON.getSetting('playerpl_selected_profile')
        self.SELECTED_PROFILE_ID = ADDON.getSetting('playerpl_selected_profile_id')
        self.ENABLE_SUBS = ADDON.getSetting('playerpl_subtitles')
        self.LOGGED = ADDON.getSetting('playerpl_logged')

        self.update_headers2()

    def createDatas(self):

        def gen_hex_code(myrange=6):
            import random
            return ''.join([random.choice('0123456789abcdef') for x in range(myrange)])
            
        def uniq_usagent():
            usagent_id = ''
        
            if ADDON.getSetting('playerpl_usagent_id'):
                usagent_id = ADDON.getSetting('playerpl_usagent_id')
            else:
                usagent_id = '2e520525f3'+ gen_hex_code(6)

            ADDON.setSetting('playerpl_usagent_id', usagent_id)
            return usagent_id
        
        def uniq_usagentver():
            usagentver_id = ''
        
            if ADDON.getSetting('playerpl_usagentver_id'):
                usagentver_id = ADDON.getSetting('playerpl_usagentver_id')
            else:
                usagentver_id = '2e520525f2'+ gen_hex_code(6)

            ADDON.setSetting('playerpl_usagentver_id', usagentver_id)
            return usagentver_id
            
        def uniq_maker():
            maker_id = ''
        
            if ADDON.getSetting('playerpl_maker_id'):
                maker_id = ADDON.getSetting('playerpl_maker_id')
            else:
                maker_id = gen_hex_code(16)

            ADDON.setSetting('playerpl_maker_id', maker_id)
            return maker_id
            
        def uniq_id():
            device_id = ''
        
            if ADDON.getSetting('playerpl_device_id'):
                device_id = ADDON.getSetting('playerpl_device_id')
            else:
                device_id = gen_hex_code(16)

            ADDON.setSetting('playerpl_device_id', device_id)
            return device_id

        self.DEVICE_ID = uniq_id()
        self.MAKER = uniq_maker()
        self.USAGENT = uniq_usagent()
        self.USAGENTVER = uniq_usagentver()

        return

    def getRequests(self, url, data={}, headers={}, params ={}):
        if data:
            if headers.get('Content-Type', '').startswith('application/json'):
                content = sess.post(url, headers=headers, json=data, params=params, verify=False, timeout=timeouts).json()

            else:
                content = sess.post(url, headers=headers, data=data, params=params, verify=False, timeout=timeouts).json()

        else:
            content = sess.get(url, headers=headers, params=params, verify=False, timeout=timeouts).json()

        return content

    def loginService(self):
        self.REFRESH_TOKEN = ADDON.getSetting('playerpl_refresh_token')
        self.LOGGED = ADDON.getSetting('playerpl_logged')

        try:
            if not self.DEVICE_ID or not self.MAKER or not self.USAGENT or not self.USAGENTVER:
                self.createDatas()
            
            if not self.REFRESH_TOKEN and self.LOGGED != 'true':
                POST_DATA = 'scope=/pub-api/user/me&client_id=Player_TV_Android_28d3dcc063672068'
                data = self.getRequests(self.GETTOKEN, data = POST_DATA, headers=self.HEADERS3)
                kod = data.get('code')
                dg = xbmcgui.DialogProgress()
                dg.create('Uwaga','Przepisz kod: [COLOR gold][B]{}[/COLOR][/B]\nNa stronie https://player.pl/zaloguj-tv'.format(kod))
                
                time_to_wait = 340
                secs = 0
                increment = 100 // time_to_wait
                cancelled = False
                b = 'acces_denied'

                while secs <= time_to_wait:
                    if (dg.iscanceled()): cancelled = True; break
                    if secs != 0: xbmc.sleep(3000)
                    secs_left = time_to_wait - secs
                    if secs_left == 0: percent = 100
                    else: percent = increment * secs
                    
                    POST_DATA = 'grant_type=tvn_reverse_onetime_code&code={}&client_id=Player_TV_Android_28d3dcc063672068'.format(kod)
                    data = self.getRequests(self.POSTTOKEN, data=POST_DATA, headers=self.HEADERS3)
                    token_type = data.get("token_type", None)
                    errory = data.get('error', None)
                    if token_type == 'bearer': break
                    secs += 1
                
                    dg.update(percent)
                    secs += 1

                dg.close()
                
                if not cancelled:
                    self.ACCESS_TOKEN = data.get('access_token', None)
                    self.USER_PUB = data.get('user_pub', None)
                    self.USER_HASH = data.get('user_hash', None)
                    self.REFRESH_TOKEN = data.get('refresh_token', None)

                    ADDON.setSetting('playerpl_access_token', self.ACCESS_TOKEN)
                    ADDON.setSetting('playerpl_user_pub', self.USER_PUB)
                    ADDON.setSetting('playerpl_user_hash', self.USER_HASH)
                    ADDON.setSetting('playerpl_refresh_token', self.REFRESH_TOKEN)

            if self.REFRESH_TOKEN:
                PARAMS = {'4K': 'true','platform': 'ANDROID_TV'}
                self.HEADERS2['Content-Type'] =  'application/json; charset=UTF-8'

                POST_DATA = {"agent":self.USAGENT,"agentVersion":self.USAGENTVER,"appVersion":"1.0.38(62)","maker":self.MAKER,"os":"Android","osVersion":"9","token":self.ACCESS_TOKEN,"uid":self.DEVICE_ID}
                data = self.getRequests(self.SUBSCRIBER, data=POST_DATA, headers=self.HEADERS2, params=PARAMS)
            
                self.SELECTED_PROFILE = data.get('profile',{}).get('name', None)
                self.SELECTED_PROFILE_ID = data.get('profile',{}).get('externalUid', None)
            
                self.HEADERS2['API-ProfileUid'] =  self.SELECTED_PROFILE_ID
                
                ADDON.setSetting('playerpl_selected_profile_id', self.SELECTED_PROFILE_ID)
                ADDON.setSetting('playerpl_selected_profile', self.SELECTED_PROFILE)
                return True

            #if self.LOGGED != 'true':
                #ADDON.setSetting('playerpl_logged', 'false')
                #return False

            if self.LOGGED == 'true':
                return True
            else:
                return False

        except:
            self.log('Exception while trying to log in: {}'.format(getExceptionString()))
            self.connErrorMessage()
        return False

    def getChannelList(self, silent):
        self.refreshTokenTVN()

        result = list()
        if not self.loginService():
            return result

        self.log('\n\n')
        self.log('[UPD] Downloading list of available {} channels from {}'.format(self.serviceName, self.url))
        self.log('[UPD] -------------------------------------------------------------------------------------')
        self.log('[UPD] %-10s %-35s %-15s %-20s %-35s' % ( '-CID-', '-NAME-', '-GEOBLOCK-', '-ACCESS STATUS-', '-IMG-'))

        try:
            regexReplaceList = list()

            regexReplaceList.append( re.compile('(\s|^)(International)(?=\s|$)',  re.IGNORECASE) )

            urlk = 'https://player.pl/playerapi/product/live/list?platform=ANDROID_TV'
            
            out = []
            
            data = self.getRequests(urlk, headers=self.HEADERS2, params={})

            self.mylist = self.getRequests('https://player.pl/playerapi/subscriber/product/available/list?platform=ANDROID_TV', headers=self.HEADERS2, params={})

            if PY3:
                jdata = data
            else:
                jdata = json.loads(json.dumps(data))

            for channel in jdata:
                if channel['id'] in self.mylist or 'TVN HD' == channel['title']:
                    id_ = channel['id']
                    name = channel['title']
                    title = channel['title'] + ' PL'
                    img = channel['images']['pc'][0]['mainUrl']

                    for regexReplace in regexReplaceList:
                        name = regexReplace.sub('', name)
                        title = regexReplace.sub('', title)

                    name = re.sub(r'^\s*', '', str(name))
                    title = re.sub(r'^\s*', '', str(title))

                    cid = '%s:%s' % (id_,'kanal')
                    program = TvCid(cid=cid, name=name, title=title, img=img)
                    result.append(program)

                if len(result) <= 0:
                    self.loginErrorMessage()
                    self.log('Error while parsing service {}, returned data is: {}'.format(self.serviceName, str(data)))

        except:
            self.log('getChannelList exception: {}'.format(getExceptionString()))
        return result

    def channCid(self, cid):
        try:
            r = re.compile('^(.*?)_TS_.*$', re.IGNORECASE)
            cid = r.findall(cid)[0]
        except:
            cid 

        return cid

    def update_headers2(self):
        self.HEADERS2 = {
            'Authorization': 'Basic',
            'API-DeviceInfo': '%s;%s;Android;9;%s;1.0.38(62);' % (
                self.USAGENT, self.USAGENTVER, self.MAKER),
            'API-DeviceUid': self.DEVICE_ID,
            'User-Agent': UA,
            'Host': 'player.pl',
            'X-NewRelic-ID': 'VQEOV1JbABABV1ZaBgMDUFU=',
            'API-Authentication': self.ACCESS_TOKEN,
            'API-SubscriberHash': self.USER_HASH,
            'API-SubscriberPub': self.USER_PUB,
            'API-ProfileUid': self.SELECTED_PROFILE_ID,
        }

    def refreshTokenTVN(self):
        POST_DATA = 'grant_type=refresh_token&refresh_token={}&client_id=Player_TV_Android_28d3dcc063672068'.format(self.REFRESH_TOKEN)
        data = self.getRequests(self.POSTTOKEN, data=POST_DATA, headers=self.HEADERS3)
        if data.get('error_description', None) == 'Token is still valid.':
            return

        else:
            self.ACCESS_TOKEN = data.get('access_token', None)
            self.USER_PUB = data.get('user_pub', None)
            self.USER_HASH = data.get('user_hash', None)
            self.REFRESH_TOKEN = data.get('refresh_token', None)

            ADDON.setSetting('playerpl_access_token', self.ACCESS_TOKEN)
            ADDON.setSetting('playerpl_user_pub', self.USER_PUB )
            ADDON.setSetting('playerpl_user_hash', self.USER_HASH)
            ADDON.setSetting('playerpl_refresh_token', self.REFRESH_TOKEN)
            self.update_headers2()
            return data

    def getTranslate(self, id_):
        PARAMS = {'4K': 'true','platform': 'ANDROID_TV', 'id': id_}
        data = self.getRequests(self.TRANSLATE,headers = self.HEADERS2, params = PARAMS)
        return data

    def getPlaylist(self, id_):
        self.refreshTokenTVN()

        HEADERSz = {
            'Authorization': 'Basic',
            'API-DeviceInfo': '{};{};Android;9;{};1.0.38(62);'.format(self.USAGENT, self.USAGENTVER, self.MAKER ),
            'API-Authentication': self.ACCESS_TOKEN,
            'API-DeviceUid': self.DEVICE_ID,
            'API-SubscriberHash': self.USER_HASH,
            'API-SubscriberPub': self.USER_PUB,
            'API-ProfileUid': self.SELECTED_PROFILE_ID,
            'User-Agent': 'okhttp/3.3.1 Android',
            'Host': 'player.pl',
            'X-NewRelic-ID': 'VQEOV1JbABABV1ZaBgMDUFU=',
        }
    
    
        if 'kanal' in id_:
            id_= id_.split(':')[0]
            rodzaj = 'LIVE'

        urlk = 'https://player.pl/playerapi/product/%s/player/configuration?type=%s&4K=true&platform=ANDROID_TV' % (str(id_), rodzaj)
    
        data = self.getRequests(urlk, headers=HEADERSz)
    
        try:
            vidsesid = data["videoSession"]["videoSessionId"]
            prolongvidses = data["prolongVideoSessionUrl"]
        
        except:
            vidsesid = False
            pass

        PARAMS = {'type': rodzaj, 'platform': 'ANDROID_TV'}
    
        data = self.getRequests(self.api_base+'item/%s/playlist' % (str(id_)), headers=HEADERSz, params=PARAMS)
    
        if not data:
            urlk = 'https://player.pl/playerapi/item/%s/playlist?type=%s&platform=ANDROID_TV&videoSessionId=%s' % (str(id_), rodzaj, str(vidsesid))
            data = self.getRequests(urlk,headers = HEADERSz, params = {})
    
        vid = data['movie']
        outsub = []

        try:
            subs = vid['video']['subtitles']
            for lan, sub in subs.items():
                lang = sub['label']
                srcsub = sub['src']
                outsub.append({'lang':lang, 'url':srcsub})

        except:
            pass

        src = vid['video']['sources']['dash']['url'] + ('&dvr=7201000' if rodzaj == 'LIVE' else '')
        widev = vid['video']['protections']['widevine']['src']
        if vidsesid:
            widev += '&videoSessionId=%s' % vidsesid
    
        src = requests.get(src, allow_redirects=False, verify=False)
        src = src.headers['Location']

        return src, widev, outsub

    def getChannelStream(self, chann):
        data = None

        cid = self.channCid(chann.cid)
        
        try:
            run = self.getTranslate(str(cid))

            stream_url, license_url, subtitles = self.getPlaylist(str(cid))
            check = any(cid for item in self.mylist)

            if check is False:
                self.noPremiumMessage()
                return

            data = stream_url

            if data is not None and data != "":
                chann.strm = data
                chann.lic = license_url
                try:
                    self.log('getChannelStream found matching channel: cid: {}, name: {}, rtmp:{}'.format(chann.cid, chann.name, chann.strm))
                except:
                    self.log('getChannelStream found matching channel: cid: {}, name: {}, rtmp:{}'.format(str(chann.cid), str(chann.name), str(chann.strm)))
                return chann
            else:
                self.log('getChannelStream error getting channel stream2, result: {}'.format(str(data)))
                return None

        except Exception as e:
            self.log('getChannelStream exception while looping: {}\n Data: {}'.format(getExceptionString(), str(data)))
        return None
