#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2020 mbebe
#   Copyright (C) 2020 Mariusz89B

#   Some implementations are modified and taken from "plugin.video.cpgo" - thank you very much mbebe!

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
#   This add-on is unoffical and is not endorsed or supported by Cyfrowy Polsat S.A. in any way. Any trademarks used belong to their owning companies and organisations.

from __future__ import unicode_literals

import sys

try:
   import urllib.parse as urlparse
except ImportError:
    import urlparse

try:
    import http.cookiejar as cookielib
except ImportError:
    import  cookielib

try:
    from urllib.parse import urlencode, quote_plus, quote
except ImportError:
    from urllib import urlencode, quote_plus, quote

import re, os
import requests
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, xbmcvfs
import string

from strings import *
from serviceLib import *

import random
import time

serviceName         = 'Cyfrowy Polsat GO'

UA = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36'

auth_url='https://b2c.redefine.pl/rpc/auth/'
navigate_url='https://b2c.redefine.pl/rpc/navigation/'

clid = ADDON.getSetting('cpgo_clientId')
devid = ADDON.getSetting('cpgo_devid')

stoken = ADDON.getSetting('cpgo_sesstoken')
sexpir = ADDON.getSetting('cpgo_sessexpir')
skey = ADDON.getSetting('cpgo_sesskey')

class PolsatGoUpdater(baseServiceUpdater):
    def __init__(self):
        self.serviceName        = serviceName
        self.localMapFile       = 'basemap.xml'
        baseServiceUpdater.__init__(self)
        self.serviceEnabled     = ADDON.getSetting('cpgo_enabled')
        self.login              = ADDON.getSetting('cpgo_username').strip()
        self.password           = ADDON.getSetting('cpgo_password').strip()
        self.servicePriority    = int(ADDON.getSetting('priority_cpgo'))
        self.addDuplicatesToList = True
        if sys.version_info[0] > 2:
            try:
                self.profilePath  = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
            except:
                self.profilePath  = xbmcvfs.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')
        else:
            try:
                self.profilePath  = xbmc.translatePath(ADDON.getAddonInfo('profile'))
            except:
                self.profilePath  = xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')


    def loginService(self):
        try:
            headers = {
            'Host': 'b2c.redefine.pl',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
            'Content-Type': 'application/json; utf-8',
            'Origin': 'https://go.cyfrowypolsat.pl',
            'DNT': '1',
            'Referer': 'https://go.cyfrowypolsat.pl/',
            }
            osinfo = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36"
            uaipla = "www_iplatv/12345 (Mozilla/5.0 Windows NT 10.0; WOW64 AppleWebKit/537.36 KHTML, like Gecko Chrome/62.0.3202.9 Safari/537.36)"
            
            
            clid = ADDON.getSetting('cpgo_clientId')
            devid = ADDON.getSetting('cpgo_devid')
            
            stoken = ADDON.getSetting('cpgo_sesstoken')
            sexpir = ADDON.getSetting('cpgo_sessexpir')
            skey = ADDON.getSetting('cpgo_sesskey')
            
            def gen_hex_code(myrange=6):
                return ''.join([random.choice('0123456789ABCDEF') for x in range(myrange)])
            
            def ipla_system_id():
                myrand = gen_hex_code(10) + '-' + gen_hex_code(4) + '-' + gen_hex_code(4) + '-' + gen_hex_code(4) + '-' + gen_hex_code(12)
            
                return myrand

            if not clid and not devid:
                clientid = ipla_system_id()
                deviceid = ipla_system_id()
                
                ADDON.setSetting('cpgo_clientId', clientid)
                ADDON.setSetting('cpgo_devid', deviceid)
                self.loginService()

            else:
                usernameCP = self.login
                passwordCP = self.password
                if usernameCP and passwordCP:
                    data = {"jsonrpc":"2.0","method":"login","id":1,"params":{"authData":{"loginICOK":usernameCP,"passwordICOK":passwordCP,"deviceIdICOK":{"value":devid,"type":"other"}},"ua":"cpgo_www/2015"}}
                    response = requests.post(auth_url, headers = headers, json = data, verify = False, timeout = 15).json()
                    deb('Print: {}'.format(response))
                    try:
                        error = response['error']
                        if response['error']['message'] == 'Unauthorized access':
                            self.loginErrorMessage()
                            return False

                        elif response['error']['message'] == 'Forbidden access':
                            self.loginErrorMessage()
                            return False

                        elif response['error']['message'] == 'Device limit exceeded':
                            dictLimit = error['data']
                            xbmcgui.Dialog().ok('Cyfrowy Polsat GO', str(error['message']) + '. Maximum limit: '+ str(dictLimit.get('limit')))
                            self.maxDeviceIdMessage()
                            return False

                    except:
                        sesja = response['result']['session']

                        sesstoken = sesja['id']
                        sessexpir = str(sesja['keyExpirationTime'])
                        sesskey = sesja['key']
                        
                        ADDON.setSetting('cpgo_sesstoken', sesstoken)
                        ADDON.setSetting('cpgo_sessexpir', str(sessexpir))
                        ADDON.setSetting('cpgo_sesskey', sesskey)
                        accesgroup = response['result']['accessGroups']

                        ADDON.setSetting('cpgo_accgroups', str(accesgroup))
                        return True

                else:
                    self.loginErrorMessage()
                    return False

        except:
            self.log('Exception while trying to log in: {}'.format(getExceptionString()))
            self.connErrorMessage()  
        return False

    def getChannelList(self, silent):
        result = list()

        if not self.loginService():
            return result

        self.log('\n\n')
        self.log('[UPD] Downloading list of available {} channels from {}'.format(self.serviceName, self.url))
        self.log('[UPD] -------------------------------------------------------------------------------------')
        self.log('[UPD] %-10s %-35s %-15s %-20s %-35s' % ( '-CID-', '-NAME-', '-GEOBLOCK-', '-ACCESS STATUS-', '-IMG-'))

        try:     
            headers = {
            'Host': 'b2c.redefine.pl',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
            'Content-Type': 'application/json; utf-8',
            'Origin': 'https://go.cyfrowypolsat.pl',
            'DNT': '1',
            'Referer': 'https://go.cyfrowypolsat.pl/',
            }


            stoken = ADDON.getSetting('cpgo_sesstoken')
            sexpir = ADDON.getSetting('cpgo_sessexpir')


            items = []
            myperms = []
            ff = ADDON.getSetting('cpgo_accgroups')
            lista = eval(ff)
            
            for l in lista:
                if 'sc:' in l:
                    myperms.append(l)

            dane = stoken+'|'+sexpir+'|navigation|getTvChannels'
            authdata = getHmac(dane)
            data = {"jsonrpc":"2.0","method":"getTvChannels","id":1,"params":{"filters":[],"ua":"cpgo_www/2015","authData":{"sessionToken":authdata}}}
            response = requests.post(navigate_url, headers=headers, json=data, timeout=15).json()
            aa = response['result']['results']
            for i in aa:
                item = {}
                channelperms = i['grantExpression'].split('*')
                channelperms = [w.replace('+plat:all', '') for w in channelperms]   
                for j in myperms:
                    if j in channelperms or i['title']=='Polsat' or i['title']=='TV4':
                        img = i['thumbnails'][-1]['src']
                        cid = i['id'] + '_TS_3H'
                        name = i['title'].upper() + ' PL'

                        program = TvCid(cid, name, name, img=img)
                        result.append(program)
            
            if len(result) <= 0:
                self.log('Error while parsing service {}, returned data is: {}'.format(self.serviceName, str(response)))
                self.loginErrorMessage()

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

    def getChannelStream(self, chann):
        data = None
        cpid = int(0)
        id = self.channCid(chann.cid)

        try:
            stoken = ADDON.getSetting('cpgo_sesstoken')
            sexpir = ADDON.getSetting('cpgo_sessexpir')

            dane = stoken+'|'+sexpir+'|auth|getSession'
            authdata = getHmac(dane)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
                'Content-Type': 'application/json; utf-8',
                'Origin': 'https://go.cyfrowypolsat.pl',
                'Connection': 'keep-alive',
            }
            
            cdata = {"jsonrpc":"2.0","method":"getSession","id":1,"params":{"ua":"cpgo_www/2015","authData":{"sessionToken":authdata}}}
            
            response = requests.post(auth_url, headers=headers, json=cdata, timeout=15).json()
            sesja = response['result']['session']
            
            sesstoken = sesja['id']
            sessexpir = str(sesja['keyExpirationTime'])
            sesskey = sesja['key']
            
            ADDON.setSetting('cpgo_sesstoken', sesstoken)
            ADDON.setSetting('cpgo_sessexpir', str(sessexpir))
            ADDON.setSetting('cpgo_sesskey', sesskey)
            
            stoken = ADDON.getSetting('cpgo_sesstoken')
            sexpir = ADDON.getSetting('cpgo_sessexpir')
            
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.9 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
                'Content-Type': 'text/plain;charset=UTF-8',
                'Origin': 'https://go.cyfrowypolsat.pl',
                'Connection': 'keep-alive',
                'Referer': 'https://go.cyfrowypolsat.pl/tv/channel/'+id,
            }
            dane = stoken+'|'+sexpir+'|navigation|prePlayData'
            authdata = getHmac(dane)
            cdata = {"jsonrpc":"2.0","id":1,"method":"prePlayData","params":{"ua":"cpgo_www_html5/2 (Windows 10; widevine=true)","cpid":cpid,"mediaId":id,"authData":{"sessionToken":authdata}}}
            
            response = requests.post(navigate_url, headers=headers, json=cdata ,timeout=15).json()
            playback = response['result']['mediaItem']['playback']
            mediaid = playback['mediaId']['id']
            mediaSources = playback['mediaSources'][0]
            keyid = mediaSources['keyId']
            sourceid = mediaSources['id']

            stream_url = mediaSources['url']
            dane = stoken+'|'+sexpir+'|drm|getWidevineLicense'
            authdata = getHmac(dane)
            devcid = devid.replace('-','')
            cdata = quote('{"jsonrpc":"2.0","id":1,"method":"getWidevineLicense","params":{"cpid":%d,"mediaId":"'%cpid+mediaid+'","sourceId":"'+sourceid+'","keyId":"'+keyid+'","object":"b{SSM}","deviceId":{"type":"other","value":"'+devcid+'"},"ua":"cpgo_www_html5/2","authData":{"sessionToken":"'+authdata+'"}}}')

            licenseUrl = cdata
            data = stream_url
        
            if data is not None and data != "":
                chann.strm = data
                chann.lic = licenseUrl
                self.log('getChannelStream found matching channel: cid: {}, name: {}, rtmp:{}'.format(chann.cid, chann.name, chann.strm))
                return chann
            else:
                self.log('getChannelStream error getting channel stream2, result: {}'.format(str(data)))
                return None

        except Exception as e:
            self.log('getChannelStream exception while looping: {}\n Data: {}'.format(getExceptionString(), str(data)))
        return None

def getHmac(dane):
    skey = ADDON.getSetting('cpgo_sesskey')
    import hmac
    import hashlib 
    import binascii
    import base64
    from hashlib import sha256
    ssdalej = dane
    import base64

    def base64_decode(s):
        """Add missing padding to string and return the decoded base64 string."""
        #log = logging.getLogger()
        s = str(s).strip()
        try:
            return base64.b64decode(s)
        except TypeError:
            padding = len(s) % 4
            if padding == 1:
                #log.error("Invalid base64 string: {}".format(s))
                return ''
            elif padding == 2:
                s += b'=='
            elif padding == 3:
                s += b'='
            return base64.b64decode(s)
    secretAccessKey = base64_decode(skey.replace('-','+').replace('_','/'))
    
    auth = hmac.new(secretAccessKey, ssdalej.encode("ascii"), sha256)
    vv = base64.b64encode(bytes(auth.digest())).decode("ascii")

    aa = vv
    bb = ssdalej+'|'+aa.replace('+','-').replace('/','_')
    return bb
    
    
