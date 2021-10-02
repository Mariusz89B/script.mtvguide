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

#   Disclaimer
#   This add-on is unoffical and is not endorsed or supported by XXX in any way. Any trademarks used belong to their owning companies and organisations.

from __future__ import unicode_literals

import sys

import os, copy, re
import xbmc, xbmcvfs
import requests

try:
    from urllib.parse import urlencode, quote_plus, quote
except ImportError:
    from urllib import urlencode, quote_plus, quote

import random

from strings import *
from serviceLib import *

serviceName         = 'Polsat GO'

UA = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'
UAPG = "pg_pc_windows_firefox_html/1 (Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0)"
UAPGwidevine = "pg_pc_windows_firefox_html/1 (Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0) (Windows 7; widevine=true)"

try:
    if sys.version_info[0] > 2:
        COOKIEFILE = os.path.join(xbmcvfs.translatePath(ADDON.getAddonInfo('profile')), 'pgo.cookie')
    else:
        COOKIEFILE = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('profile')), 'pgo.cookie')
except:
    if sys.version_info[0] > 2:
        COOKIEFILE = os.path.join(xbmcvfs.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8'), 'pgo.cookie')
    else:
        COOKIEFILE = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8'), 'pgo.cookie')

sess = requests.Session()
if sys.version_info[0] > 2:
    sess.cookies = http.cookiejar.LWPCookieJar(COOKIEFILE)
else:
    sess.cookies = cookielib.LWPCookieJar(COOKIEFILE)

timeouts = (15, 30)

class PolsatGoUpdater(baseServiceUpdater):
    def __init__(self):
        self.serviceName        = serviceName
        self.localMapFile       = 'basemap.xml'
        baseServiceUpdater.__init__(self)
        self.serviceEnabled     = ADDON.getSetting('polsatgo_enabled')
        self.login              = ADDON.getSetting('polsatgo_username').strip()
        self.password           = ADDON.getSetting('polsatgo_password').strip()
        self.servicePriority    = int(ADDON.getSetting('priority_polsatgo'))
        self.clid               = ADDON.getSetting('polsatgo_clientId')
        self.devid              = ADDON.getSetting('polsatgo_devid')
        self.stoken             = ADDON.getSetting('polsatgo_sesstoken')
        self.sexpir             = ADDON.getSetting('polsatgo_sessexpir')
        self.skey               = ADDON.getSetting('polsatgo_sesskey')
        self.auth               = 'https://b2c-www.redefine.pl/rpc/auth/'
        self.host               = 'b2c-www.redefine.pl'
        self.origin             = 'https://polsatgo.pl'
        self.navigate           = 'https://b2c-www.redefine.pl/rpc/navigation/'
        self.client = ADDON.getSetting('polsatgo_client')

    def getHmac(self, data):
        skey = ADDON.getSetting('polsatgo_sesskey')
        import hmac
        import hashlib 
        import binascii
        import base64
        from hashlib import sha256
        ss = data
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
        
        auth = hmac.new(secretAccessKey, ss.encode("ascii"), sha256)
        vv = base64.b64encode(bytes(auth.digest())).decode("ascii")

        aa = vv
        bb = ss+'|'+aa.replace('+','-').replace('/','_')
        return bb

    def getRequests(self, url, data={}, headers={}, params ={}):
        if data:
            content = sess.post(url, headers=headers, json=data, params=params, verify=True, timeout=timeouts).json()
        else:
            content = sess.get(url, headers=headers, params=params, verify=True, timeout=timeouts).json()
        return content

    def loginService(self):
        try:
            headers = {
                'Host': self.host,
                'User-Agent': UA,
                'Accept': 'application/json',
                'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
                'Content-Type': 'application/json;charset=utf-8',
                'Origin': self.origin,
                'Referer': self.origin,
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
            }

            def gen_hex_code(myrange=6):
                return ''.join([random.choice('0123456789ABCDEF') for x in range(myrange)])
            
            def ipla_system_id():
                myrand = gen_hex_code(10) + '-' + gen_hex_code(4) + '-' + gen_hex_code(4) + '-' + gen_hex_code(4) + '-' + gen_hex_code(12)
                return myrand

            if not self.clid and not self.devid:
                self.clid = ipla_system_id()
                ADDON.setSetting('polsatgo_clientId', self.clid)

                self.devid = ipla_system_id()
                ADDON.setSetting('polsatgo_devid', self.devid)
                
                return self.loginService()
            else:
                self.login = ADDON.getSetting('polsatgo_username')
                self.password = ADDON.getSetting('polsatgo_password')   

                if self.login and self.password:
                    data = {
                        "id": 1,
                        "jsonrpc": "2.0",
                        "method": "login",
                        "params": {
                            "ua": UAPG,
                            "deviceId": {
                                "type": "other",
                                "value": self.devid
                            },
                            "userAgentData": {
                                "portal": "pg",
                                "deviceType": "pc",
                                "application": "firefox",
                                "player": "html",
                                "build": 1,
                                "os": "windows",
                                "osInfo": UA
                            },
                            "clientId": "",
                            "authData": {
                                "login": self.login,
                                "password": self.password,
                                "deviceId": {
                                    "type": "other",
                                    "value": self.devid}}}
                    }

                    jdata = self.getRequests(self.auth, data=data, headers=headers)

                    if sys.version_info[0] > 2:
                        response = jdata
                    else:
                        response = json.loads(json.dumps(jdata))

                    try:
                        error = response['error']
                        if error:
                            message = error['message']
                            self.loginErrorMessage()
                        return False
                    except:
                        pass

                        session = response['result']['session']
                        sesstoken = session['id']
                        sessexpir = str(session['keyExpirationTime'])
                        sesskey = session['key']

                        ADDON.setSetting('polsatgo_sesstoken', sesstoken)
                        ADDON.setSetting('polsatgo_sessexpir', str(sessexpir))
                        ADDON.setSetting('polsatgo_sesskey', sesskey)

                        dane = sesstoken+'|'+sessexpir+'|auth|getSession'
                        authdata = self.getHmac(dane)

                        data = {
                            "id": 1,
                            "jsonrpc": "2.0",
                            "method": "getSession",
                            "params": {
                                "ua": UAPG,
                                "deviceId": {
                                    "type": "other",
                                    "value": self.devid
                                },
                                "userAgentData": {
                                    "portal": "pg",
                                    "deviceType": "pc",
                                    "application": "firefox",
                                    "player": "html",
                                    "build": 1,
                                    "os": "windows",
                                    "osInfo": UA
                                },
                                "authData": {
                                    "sessionToken": authdata
                                },
                                "clientId": ""}
                        }

                        jdata = self.getRequests(self.auth, data=data, headers=headers)
                        if sys.version_info[0] > 2:
                            response = jdata
                        else:
                            response = json.loads(json.dumps(jdata))

                        session = response['result']['session']

                        sesstoken = session['id']
                        sessexpir = str(session['keyExpirationTime'])
                        sesskey = session['key']

                        ADDON.setSetting('polsatgo_sesstoken', sesstoken)
                        ADDON.setSetting('polsatgo_sessexpir', str(sessexpir))
                        ADDON.setSetting('polsatgo_sesskey', sesskey)

                        accesgroup = response['result']['accessGroups']
                        ADDON.setSetting('polsatgo_accgroups', str(accesgroup))

                        dane = sesstoken+'|'+sessexpir+'|auth|getProfiles'
                        authdata = self.getHmac(dane)

                        data = {
                            "id": 1,
                            "jsonrpc": "2.0",
                            "method": "getProfiles",
                            "params": {
                                "ua": UAPG,
                                "deviceId": {
                                    "type": "other",
                                    "value": self.devid
                                },
                                "userAgentData": {
                                    "portal": "pg",
                                    "deviceType": "pc",
                                    "application": "firefox",
                                    "player": "html",
                                    "build": 1,
                                    "os": "windows",
                                    "osInfo": UA
                                },
                                "authData": {
                                    "sessionToken": authdata
                                },
                                "clientId": ""}
                        }

                        jdata = self.getRequests(self.auth, data=data, headers=headers)
                        if sys.version_info[0] > 2:
                            response = jdata
                        else:
                            response = json.loads(json.dumps(jdata))

                        nids = []
                        for result in response['result']:
                            nids.append({'id':result['id'],'nazwa':result["name"],'img':result["avatarId"]})    
                        if len(nids) > 1:
                            profile = [x.get('nazwa') for x in nids]
                            sel = xbmcgui.Dialog().select('Wybierz profil', profile)    
                            if sel > -1:
                                id = nids[sel].get('id')
                                nazwa = nids[sel].get('nazwa')
                                avt = nids[sel].get('img')
                                profil = nazwa+'|'+id
                            else:
                                id = str(nids[0].get('id'))
                                nazwa = nids[0].get('nazwa')
                                avt = nids[sel].get('img')
                                profil = nazwa+'|'+id

                        else:
                            id = str(nids[0].get('id'))
                            nazwa = nids[0].get('nazwa')
                            avt = nids[0].get('img')
                            profil = nazwa+'|'+id

                        dane = sesstoken+'|'+sessexpir+'|auth|setSessionProfile'
                        authdata = self.getHmac(dane)

                        data = {
                            "id": 1,
                            "jsonrpc": "2.0",
                            "method": "setSessionProfile",
                            "params": {
                                "ua": UAPG,
                                "deviceId": {
                                    "type": "other",
                                    "value": self.devid
                                },
                                "userAgentData": {
                                    "portal": "pg",
                                    "deviceType": "pc",
                                    "application": "firefox",
                                    "player": "html",
                                    "build": 1,
                                    "os": "windows",
                                    "osInfo": UA
                                },
                                "authData": {
                                    "sessionToken": authdata
                                },
                                "clientId": "",
                                "profileId": id}
                        }

                        jdata = self.getRequests(self.auth, data=data, headers=headers)
                        if sys.version_info[0] > 2:
                            response = jdata
                        else:
                            response = json.loads(json.dumps(jdata))

                        dane = sesstoken+'|'+sessexpir+'|auth|getSession'
                        authdata = self.getHmac(dane)

                        data = {
                            "id": 1,
                            "jsonrpc": "2.0",
                            "method": "getSession",
                            "params": {
                                "ua": UAPG,
                                "deviceId": {
                                    "type": "other",
                                    "value": self.devid
                                },
                                "userAgentData": {
                                    "portal": "pg",
                                    "deviceType": "pc",
                                    "application": "firefox",
                                    "player": "html",
                                    "build": 1,
                                    "os": "windows",
                                    "osInfo": UA
                                },
                                "authData": {
                                    "sessionToken": authdata
                                },
                                "clientId": ""}
                        }

                        jdata = self.getRequests(self.auth, data=data, headers=headers)
                        if sys.version_info[0] > 2:
                            response = jdata
                        else:
                            response = json.loads(json.dumps(jdata))

                        session = response['result']['session']

                        sesstoken = session['id']
                        sessexpir = str(session['keyExpirationTime'])
                        sesskey = session['key']

                        ADDON.setSetting('polsatgo_sesstoken', sesstoken)
                        ADDON.setSetting('polsatgo_sessexpir', str(sessexpir))
                        ADDON.setSetting('polsatgo_sesskey', sesskey)

                        accesgroup = response['result']['accessGroups']
                        ADDON.setSetting('polsatgo_accgroups', str(accesgroup))

                        return True

                else:
                    self.loginErrorMessage()
                    return False

        except:
            self.log('getLogin exception: {}'.format(getExceptionString()))
            self.connErrorMessage()
        return False

    def getChannelList(self, silent):
        result = list()

        if not self.loginService():
            return result
        
        self.log('\n\n')
        self.log('[UPD] Downloading list of available {}'.format(self.serviceName))
        self.log('[UPD] -------------------------------------------------------------------------------------')
        self.log('[UPD] %-15s %-35s %-30s' % ('-CID-', '-NAME-', '-TITLE-'))
        
        try:    
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36 Edg/93.0.961.52',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Referer': 'https://polsatgo.pl/kanaly-tv',
                'Accept-Language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6',
            }

            url = 'https://polsatgo.pl/kanaly-tv'

            res = requests.get(url, headers)

            text = re.findall('type=\"application\/json\">(.+?)<\/script>', res.text)[0]
            json_data = json.loads(text)

            jdata = json_data['props']['pageProps']['lists']['results']

            for item in jdata:
                cid = item['id']
                name = item['title']
                title = item['title'] + ' PL'
                img = item['thumbnails'][-1]['src']

                program = TvCid(cid=cid, name=name, title=title, img=img) 
                result.append(program)

            if len(result) <= 0:
                self.log('Error while parsing service {}, returned data is: {}'.format(self.serviceName, str(response)))

        except:
            self.log('getChannelList exception: {}'.format(getExceptionString()))
            self.wrongService()
        return result

    def getChannelStream(self, chann):
        data = None
        cpid = int(0)
        id = chann.cid

        try:
            stoken = ADDON.getSetting('polsatgo_sesstoken')
            sexpir = ADDON.getSetting('polsatgo_sessexpir')

            headers = {
                'Host': self.host,
                'User-Agent': UA,
                'Accept': 'application/json',
                'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
                'Content-Type': 'application/json;charset=utf-8',
                'Origin': self.origin,
                'Referer': self.origin,
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
            }

            dane = stoken+'|'+sexpir+'|auth|getSession'
            authdata = self.getHmac(dane)

            data = {
                "id": 1,
                "jsonrpc": "2.0",
                "method": "getSession",
                "params": {
                    "ua": UAPG,
                    "deviceId": {
                        "type": "other",
                        "value": self.devid
                    },
                    "userAgentData": {
                        "portal": "pg",
                        "deviceType": "pc",
                        "application": "firefox",
                        "player": "html",
                        "build": 1,
                        "os": "windows",
                        "osInfo": UA
                    },
                    "authData": {
                        "sessionToken": authdata
                    },
                    "clientId": ""}}

            response = requests.post(self.auth, headers=headers, json=data, timeout=15, verify=True).json()
            session = response['result']['session']

            sesstoken = session['id']
            sessexpir = str(session['keyExpirationTime'])
            sesskey = session['key']

            ADDON.setSetting('polsatgo_sesstoken', sesstoken)
            ADDON.setSetting('polsatgo_sessexpir', str(sessexpir))
            ADDON.setSetting('polsatgo_sesskey', sesskey)

            stoken = ADDON.getSetting('polsatgo_sesstoken')
            sexpir = ADDON.getSetting('polsatgo_sessexpir')

            dane = stoken+'|'+sexpir+'|navigation|prePlayData'
            authdata = self.getHmac(dane)

            data = {"jsonrpc":"2.0","id":1,"method":"prePlayData","params":{"ua":UAPGwidevine,"userAgentData":{"deviceType":"pc","application":"firefox","os":"windows","build":2150100,"portal":"pg","player":"html","widevine":True},"cpid":cpid,"mediaId":id,"authData":{"sessionToken":authdata},"clientId":self.clid}}

            response = requests.post(self.navigate, headers=headers, json=data, timeout=15, verify=True).json()
            playback = response['result']['mediaItem']['playback']
            mediaid = playback['mediaId']['id']
            mediaSources = playback['mediaSources'][0]
            keyid = mediaSources['keyId']
            sourceid = mediaSources['id']

            try:
                cc = mediaSources['authorizationServices']['pseudo']
                dane = stoken+'|'+sexpir+'|drm|getPseudoLicense'
                authdata = self.getHmac(dane)
                devcid = self.devid.replace('-','')
                
                data = {
                    "jsonrpc":"2.0",
                    "id":1,
                    "method":"getPseudoLicense",
                    "params": {
                        "ua":"cpgo_www_html5/2",
                        "cpid":1,
                        "mediaId":mediaid,
                        "sourceId":sourceid,
                        "deviceId": {
                            "type":"other",
                            "value":devcid 
                        },
                        "authData": {
                            "sessionToken":authdata}}}

                response = requests.post('https://b2c-www.redefine.pl/rpc/drm/', headers=headers, json=data, timeout=15, verify=True).json()

                licenseUrl = None
                data = response['result']['url']
            except:
                stream_url = mediaSources['url']
                
                dane = stoken+'|'+sexpir+'|drm|getWidevineLicense'
                authdata = self.getHmac(dane)
                devcid = self.devid.replace('-','')

                cdata = quote('{"jsonrpc":"2.0","id":1,"method":"getWidevineLicense","params":{"cpid":%d,"mediaId":"'%cpid+mediaid+'","sourceId":"'+sourceid+'","keyId":"'+keyid+'","object":"b{SSM}","deviceId":{"type":"other","value":"'+self.devid+'"},"ua":"pg_pc_windows_firefox_html/2150100","authData":{"sessionToken":"'+authdata+'"}}}')

                licenseUrl = cdata
                data = stream_url
        
            if data is not None and data != "":
                chann.lic = licenseUrl
                chann.strm = data
                self.log('getChannelStream found matching channel: cid: {}, name: {}, rtmp:{}'.format(id, chann.name, chann.strm))
                return chann
            else:
                self.log('getChannelStream error getting channel stream2, result: {}'.format(str(data)))
                return None

        except Exception as e:
            self.log('getChannelStream exception while looping: {}\n Data: {}'.format(getExceptionString(), str(data)))
        return None
            