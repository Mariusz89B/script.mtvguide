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

if sys.version_info[0] > 2:
    PY3 = True
else:
    PY3 = False

if PY3:
    import urllib.request, urllib.parse, urllib.error
    from urllib.parse import urlencode, quote_plus, quote, unquote, parse_qsl
    import http.cookiejar
else:
    import urllib
    from urllib import urlencode, quote_plus, quote, unquote
    import cookielib

import urllib3
import requests

requests.packages.urllib3.disable_warnings()
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
try:
    requests.packages.urllib3.contrib.pyopenssl.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
except AttributeError:
    # no pyopenssl support used / needed / available
    pass

import re, os, copy, random, json
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, xbmcvfs
from strings import *
from serviceLib import *

serviceName = 'Polsat GO'

OSINFO = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0"
UAPG = "pg_pc_windows_firefox_html/1 (Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0)"

WIDEVINE = "pg_pc_windows_firefox_html/1 (Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0) (Windows 7; widevine=true)"

HOST = 'b2c-www.redefine.pl'
ORIGIN = 'https://polsatgo.pl'
REFERER = 'https://polsatgo.pl'

try:
    if PY3:
        COOKIEFILE = os.path.join(xbmcvfs.translatePath(ADDON.getAddonInfo('profile')), 'polsatgo.cookie')
    else:
        COOKIEFILE = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('profile')), 'polsatgo.cookie')
except:
    if PY3:
        COOKIEFILE = os.path.join(xbmcvfs.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8'), 'polsatgo.cookie')
    else:
        COOKIEFILE = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8'), 'polsatgo.cookie')

sess = requests.Session()
if PY3:
    sess.cookies = http.cookiejar.LWPCookieJar(COOKIEFILE)
else:
    sess.cookies = cookielib.LWPCookieJar(COOKIEFILE)

timeouts = (15, 30)

class PolsatGoUpdater(baseServiceUpdater):
    def __init__(self):
        self.serviceName        = serviceName
        self.localMapFile       = 'basemap_pl.xml'
        baseServiceUpdater.__init__(self)
        self.serviceEnabled     = ADDON.getSetting('polsatgo_enabled')
        self.login              = ADDON.getSetting('polsatgo_username').strip()
        self.password           = ADDON.getSetting('polsatgo_password').strip()
        self.api_base           = 'https://b2c-www.redefine.pl/rpc/'

        self.navigate           = self.api_base+'navigation/'   
        
        self.auth               = self.api_base+'auth/'

        self.headers = {
            'Accept': 'application/json',
            'DNT': '1',
            'Content-Type': 'application/json;charset=UTF-8',
            'User-Agent': OSINFO,
            'Origin': 'https://polsatgo.pl',
            'Referer': 'https://polsatgo.pl/',
            'Accept-Language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6',
        }

        self.device_id = ADDON.getSetting('polsatgo_device_id')
        self.client_id = ADDON.getSetting('polsatgo_client_id')

        self.sesstoken = ADDON.getSetting('polsatgo_sesstoken')
        self.sessexpir = ADDON.getSetting('polsatgo_sessexpir')
        self.sesskey = ADDON.getSetting('polsatgo_sesskey')
        
        self.myperms = ADDON.getSetting('polsatgo_myperm')

        self.servicePriority    = int(ADDON.getSetting('priority_polsatgo'))
        self.addDuplicatesToList = True

        self.client = ADDON.getSetting('polsatgo_client')

        self.dane = self.sesstoken+'|'+self.sessexpir+'|{0}|{1}'
    

    def getRequests(self, url, data={}, headers={}, params ={}):
        if data:
            content = sess.post(url, headers=headers, json=data, params=params, verify=False, timeout=timeouts).json()
        else:
            content = sess.get(url, headers=headers, params=params, verify=False, timeout=timeouts).json()
        return content

    def loginService(self):
        try:
            headers = {
                'Host': HOST,
                'User-Agent': OSINFO,
                'Accept': 'application/json',
                'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
                'Content-Type': 'application/json;charset=utf-8',
                'Origin': ORIGIN,
                'Referer': REFERER,
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
            }

            self.device_id = ADDON.getSetting('polsatgo_device_id')
            self.client_id = ADDON.getSetting('polsatgo_client_id')

            self.sesstoken = ADDON.getSetting('polsatgo_sesstoken')
            self.sessexpir = ADDON.getSetting('polsatgo_sessexpir')
            self.sesskey = ADDON.getSetting('polsatgo_sesskey')

            def gen_hex_code(myrange=6):
                return ''.join([random.choice('0123456789abcdef') for x in range(myrange)])

            def ipla_system_id():
                myrand = gen_hex_code(10) + '-' + gen_hex_code(4) + '-' + gen_hex_code(4) + '-' + gen_hex_code(4) + '-' + gen_hex_code(12)
                return myrand

            def ipla_dev_id():
                myrand = gen_hex_code(32) + '_'
                return myrand

            if not self.client_id and not self.device_id:

                clientid = ipla_system_id()
                deviceid = ipla_dev_id()

                ADDON.setSetting('polsatgo_client_id', clientid)
                ADDON.setSetting('polsatgo_device_id', deviceid)
                return self.loginService()

            else:
                if self.login and self.password:
                    data = {
                            "id": 1,
                            "jsonrpc": "2.0",
                            "method": "login",
                            "params": {
                                "ua": UAPG,
                                "deviceId": {
                                    "type": "other",
                                    "value": self.device_id
                                },
                                "userAgentData": {
                                    "portal": "pg",
                                    "deviceType": "pc",
                                    "application": "firefox",
                                    "player": "html",
                                    "build": 1,
                                    "os": "windows",
                                    "osInfo": OSINFO
                                },
                                "clientId": "",
                                "authData": {
                                    "login": self.login,
                                    "password": self.password,
                                    "deviceId": {
                                        "type": "other",
                                        "value": self.device_id}}}
                            }

                    response = requests.post(self.auth, headers=headers, json=data, timeout=15, verify=False).json()

                    try:
                        error = response['error']
                        if error:
                            message = error['message']
                            self.loginErrorMessage()
                        return False

                    except:
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
                                        "value": self.device_id
                                    },
                                    "userAgentData": {
                                        "portal": "pg",
                                        "deviceType": "pc",
                                        "application": "firefox",
                                        "player": "html",
                                        "build": 1,
                                        "os": "windows",
                                        "osInfo": OSINFO
                                    },
                                    "authData": {
                                        "sessionToken": authdata
                                    },
                                    "clientId": ""}}


                        response = requests.post(self.auth, headers=headers, json=data,timeout=15, verify=False).json()
                        session = response['result']['session']

                        sesstoken = session['id']
                        sessexpir = str(session['keyExpirationTime'])
                        sesskey = session['key']

                        ADDON.setSetting('polsatgo_sesstoken', sesstoken)
                        ADDON.setSetting('polsatgo_sessexpir', str(sessexpir))
                        ADDON.setSetting('polsatgo_sesskey', sesskey)

                        dane = sesstoken+'|'+sessexpir+'|auth|getProfiles'
                        authdata = self.getHmac(dane)
                        
                        data = {"id":1,"jsonrpc":"2.0","method":"getProfiles","params":{"ua":UAPG,"deviceId":{"type":"other","value":self.device_id},"userAgentData":{"portal":"pg","deviceType":"pc","application":"firefox","player":"html","build":1,"os":"windows","osInfo":OSINFO},"authData":{"sessionToken":authdata},"clientId":""}}
                        response = requests.post(self.auth, headers=headers, json=data,timeout=15, verify=False).json()
                        
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
                        
                        data = {"id":1,"jsonrpc":"2.0","method":"setSessionProfile","params":{"ua":UAPG,"deviceId":{"type":"other","value":self.device_id},"userAgentData":{"portal":"pg","deviceType":"pc","application":"firefox","player":"html","build":1,"os":"windows","osInfo":OSINFO},"authData":{"sessionToken":authdata},"clientId":"","profileId":id}}
                        
                        response = requests.post(self.auth, headers=headers, json=data, timeout=15, verify=False).json()
                        
                        dane = sesstoken+'|'+sessexpir+'|auth|getSession'
                        authdata = self.getHmac(dane)

                        data = {"id":1,"jsonrpc":"2.0","method":"getSession","params":{"ua":UAPG,"deviceId":{"type":"other","value":self.device_id},"userAgentData":{"portal":"pg","deviceType":"pc","application":"firefox","player":"html","build":1,"os":"windows","osInfo":OSINFO},"authData":{"sessionToken":authdata},"clientId":""}}

                        response = requests.post(self.auth, headers=headers, json=data, timeout=15, verify=False).json()
                        
                        session = response['result']['session']

                        sesstoken = session['id']
                        sessexpir = str(session['keyExpirationTime'])
                        sesskey = session['key']

                        ADDON.setSetting('polsatgo_sesstoken', sesstoken)
                        ADDON.setSetting('polsatgo_sessexpir', str(sessexpir))
                        ADDON.setSetting('polsatgo_sesskey', sesskey)

                        accesgroup = response['result']['accessGroups']

                        myper = []

                        m_pack = {'multiple_packet_tv' : 'sc:tv', 'multiple_packet_premium': 'sc:premium', 'multiple_packet_sport': 'sc:sport', 'pos:multiple_packet_dzieci' : 'sc:kat_odzieci', 'news:true': 'sc:news'}

                        for i in data["result"]["accessGroups"]:
                            for k,v in m_pack.items():
                                if k in i:
                                    myper.append(str(v))
                            if 'sc:' in i:
                                myper.append(str(i))
                            if 'oth:' in i:
                                myper.append(str(i))
                            if 'cpuser:true' in i:
                                myper.append(str(i))
                            if 'vip:true' in i:
                                myper.append(str(i))
                            if 'rodo:true' in i:
                                myper.append(str(i))
                            if 'plususer:true' in i:
                                myper.append(str(i))
                            if 'cp_sub_ext:' in i:
                                myper.append(str(i.replace('cp_sub_ext','sc')))
                            if 'cp_sub_base:' in i:
                                myper.append(str(i.replace('cp_sub_base','sc'))) 

                        w_myperm = ", ".join(myper)

                        ADDON.setSetting('polsatgo_myperm', str(w_myperm))
                        self.myperms = myper

                        return True
                        
                else:
                    self.loginErrorMessage()
                    return False
                
        except:
            self.log('getLogin exception: {}'.format(getExceptionString()))
            self.connErrorMessage()  
        return False

    def getHmac(self, dane):
        skey = ADDON.getSetting('polsatgo_sesskey')
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

    def sesja(self, data):
        sesja = data['result']['session']

        self.sesstoken = sesja['id']
        self.sessexpir = str(sesja['keyExpirationTime'])
        self.sesskey = sesja['key']

        ADDON.setSetting('polsatgo_sesstoken', self.sesstoken)
        ADDON.setSetting('polsatgo_sessexpir', str(self.sessexpir))
        ADDON.setSetting('polsatgo_sesskey', self.sesskey)
        return self.sesstoken+'|'+self.sessexpir+'|{0}|{1}'

    def getChannelList(self, silent):
        result = list()

        if not self.loginService():
            return result

        self.log('\n\n')
        self.log('[UPD] Downloading list of available {} channels from {}'.format(self.serviceName, self.url))
        self.log('[UPD] -------------------------------------------------------------------------------------')
        self.log('[UPD] %-12s %-35s %-35s' % ( '-CID-', '-NAME-', '-TITLE-'))

        try:
            self.getSesja()
            items = []

            self.sesstoken = ADDON.getSetting('polsatgo_sesstoken')
            self.sessexpir = ADDON.getSetting('polsatgo_sessexpir')

            self.dane = self.sesstoken+'|'+self.sessexpir+'|{0}|{1}'

            dane = (self.dane).format('navigation','getTvChannels')

            authdata = self.getHmac(dane)

            self.client_id = ADDON.getSetting('polsatgo_client_id')
            self.device_id = ADDON.getSetting('pgobox_device_id')

            postData = {
                "id":1,
                "jsonrpc":"2.0",
                "method":"getTvChannels",
                "params": {
                    "filters":[],
                    "ua":UAPG,
                    "deviceId": {
                        "type":"other",
                        "value":self.device_id
                        },

                    "userAgentData": {
                        "portal":"pg",
                        "deviceType":"pc",
                        "application":"firefox",
                        "player":"html",
                        "build":1,
                        "os":"windows",
                        "osInfo":OSINFO
                        },

                    "authData": {
                        "sessionToken":authdata
                        },

                    "clientId":self.client_id}
            }

            data = self.getRequests(self.navigate, data=postData, headers=self.headers)
            channels = data['result']['results']

            myper = []

            self.myperms = ADDON.getSetting('polsatgo_myperm')

            for i in self.myperms.split(', '):
                if 'sc:' in i:
                    myper.append(str(i))
                if 'oth:' in i:
                    myper.append(str(i))
                if 'cpuser:true' in i:
                    myper.append(str(i))
                if 'vip:true' in i:
                    myper.append(str(i))
                if 'rodo:true' in i:
                    myper.append(str(i))
                if 'plususer:true' in i:
                    myper.append(str(i))
                if 'cp_:' in i:
                    myper.append(str(i))

            for i in channels:
                channelperms = i['grantExpression'].split('*')
                channelperms = [w.replace('*plat:all', '') for w in channelperms]
                for j in myper:
                    if j in channelperms or i['title'] == 'Polsat' or i['title'] == 'TV4':
                        img = i['thumbnails'][0]['src']
                        cid = i['id']
                        name = i['title'].upper()
                        title = i['title'].upper() + ' PL'

                        name = name.replace(' SD', '')
                        title = title.replace(' SD', '')

                        program = TvCid(cid=cid, name=name, title=title, img=img)
                        result.append(program)

                        self.log('[UPD] %-12s %-35s %-35s' % (cid, name, title))

            if len(result) <= 0:
                self.noContentMessage()
                self.log('Error while parsing service %s' % (self.serviceName))

            self.log('-------------------------------------------------------------------------------------')

        except Exception as e:
            self.log('getChannelList exception: %s' % getExceptionString())
            xbmcgui.Dialog().notification(serviceName, strings(70139))
        return result

    def channCid(self, cid):
        try:
            r = re.compile('^(.*?)_TS_.*$', re.IGNORECASE)
            cid = r.findall(cid)[0]
        except:
            cid 

        return cid

    def getSesja(self):
        self.sesstoken = ADDON.getSetting('polsatgo_sesstoken')
        self.sessexpir = ADDON.getSetting('polsatgo_sessexpir')

        self.dane = self.sesstoken+'|'+self.sessexpir+'|{0}|{1}'

        dane = (self.dane).format('auth','getSession')
        authdata = self.getHmac(dane)

        self.client_id = ADDON.getSetting('polsatgo_client_id')

        postData = {"id":1,"jsonrpc":"2.0","method":"getSession","params":{"userAgentData":{"portal":"pg","deviceType":"pc","application":"firefox","os":"windows","build":1,"osInfo":OSINFO},"ua":UAPG,"authData":{"sessionToken":authdata},"clientId":self.client_id}}

        data = self.getRequests(self.auth, data=postData, headers=self.headers)

        self.dane = self.sesja(data)
        return


    def getChannelStream(self, chann):
        try:
            stream = None
            
            licenseUrl = None
            licenseData = None

            id_ = self.channCid(chann.cid)
            cpid = 0

            self.sesstoken = ADDON.getSetting('polsatgo_sesstoken')
            self.sessexpir = ADDON.getSetting('polsatgo_sessexpir')

            dane = self.sesstoken+'|'+self.sessexpir+'|auth|getSession'

            headers = {
                'Host': 'b2c-www.redefine.pl',
                'User-Agent': OSINFO,
                'Accept': 'application/json',
                'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
                'Content-Type': 'application/json;charset=utf-8',
                'Origin': 'https://polsatgo.pl',
                'Referer': 'https://polsatgo.pl/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
            }

            authdata = self.getHmac(dane)

            data = {
                    "id": 1,
                    "jsonrpc": "2.0",
                    "method": "getSession",
                    "params": {
                        "ua": UAPG,
                        "deviceId": {
                            "type": "other",
                            "value": self.device_id
                        },
                        "userAgentData": {
                            "portal": "pg",
                            "deviceType": "pc",
                            "application": "firefox",
                            "player": "html",
                            "build": 1,
                            "os": "windows",
                            "osInfo": OSINFO
                        },
                        "authData": {
                            "sessionToken": authdata
                        },
                        "clientId": ""}}

            response = requests.post(self.auth, headers=headers, json=data, timeout=15, verify=False).json()

            session = response['result']['session']

            sesstoken = session['id']
            sessexpir = str(session['keyExpirationTime'])
            sesskey = session['key']

            ADDON.setSetting('polsatgo_sesstoken', self.sesstoken)
            ADDON.setSetting('polsatgo_sessexpir', str(self.sessexpir))
            ADDON.setSetting('polsatgo_sesskey', self.sesskey)

            response = requests.post(self.auth, headers=headers, json=data,timeout=15, verify=False).json()
            session = response['result']['session']

            sesstoken = session['id']
            sessexpir = str(session['keyExpirationTime'])
            sesskey = session['key']

            ADDON.setSetting('polsatgo_sesstoken', self.sesstoken)
            ADDON.setSetting('polsatgo_sessexpir', str(self.sessexpir))
            ADDON.setSetting('polsatgo_sesskey', self.sesskey)

            self.sesstoken = ADDON.getSetting('polsatgo_sesstoken')
            self.sessexpir = ADDON.getSetting('polsatgo_sessexpir')

            dane = self.sesstoken+'|'+self.sessexpir+'|navigation|prePlayData'
            authdata = self.getHmac(dane)

            data = {
                "jsonrpc":"2.0",
                "id":1,
                "method":"prePlayData",
                "params": {
                    "ua": WIDEVINE,
                    "userAgentData": {
                        "deviceType":"pc",
                        "application":"firefox",
                        "os":"windows",
                        "build":2161400,
                        "portal":"pg",
                        "player":"html",
                        "widevine":True
                    },
                    "cpid":cpid,
                    "mediaId":id_,
                    "authData":{
                        "sessionToken":authdata},
                        "clientId":self.client_id}}

            response = requests.post(self.navigate, headers=headers, json=data, timeout=15, verify=False).json()

            playback = response['result']['mediaItem']['playback']
            mediaid = playback['mediaId']['id']
            mediaSources = playback['mediaSources'][0]
            keyid = mediaSources['keyId']
            sourceid = mediaSources['id']

            licenseUrl = 'https://b2c-www.redefine.pl/rpc/drm/'

            try:
                cc = mediaSources['authorizationServices']['pseudo']
                dane = self.sesstoken+'|'+self.sessexpir+'|drm|getPseudoLicense'
                authdata = self.getHmac(dane)
                devcid = self.device_id.replace('-','')

                licenseData = {"jsonrpc":"2.0","id":1,"method":"getPseudoLicense","params":{"ua":"cpgo_www_html5/2","cpid":1,"mediaId":mediaid,"sourceId":sourceid,"deviceId":{"type":"other","value":devcid},"authData":{"sessionToken":authdata}}}
                response = requests.post('https://b2c-www.redefine.pl/rpc/drm/', headers=headers, json=data, timeout=15, verify=False).json()
                stream_url = response['result']['url']

                stream = stream_url
            except:

                stream_url = mediaSources['url']

                dane = self.sesstoken+'|'+self.sessexpir+'|drm|getWidevineLicense'
                authdata = self.getHmac(dane)
                devcid = self.device_id.replace('-','')

                licenseData = quote('{"jsonrpc":"2.0","id":1,"method":"getWidevineLicense","params":{"userAgentData":{"deviceType":"pc","application":"firefox","os":"windows","build":2161400,"portal":"pg","player":"html","widevine":true},"cpid":%d,"mediaId":"'%cpid+mediaid+'","sourceId":"'+sourceid+'","keyId":"'+keyid+'","object":"b{SSM}","deviceId":{"type":"other","value":"'+self.device_id+'"},"ua":"pg_pc_windows_firefox_html/2161400","authData":{"sessionToken":"'+authdata+'"},"clientId":"'+self.client_id+'"}}')

                stream = stream_url

            if stream is not None and stream != "":
                chann.strm = stream
                chann.lic = licenseUrl, licenseData
                
                self.log('getChannelStream found matching channel: cid: {}, name: {}, rtmp:{}'.format(chann.cid, chann.name, chann.strm))
                return chann
            else:
                self.log('getChannelStream error getting channel stream2, result: {}'.format(str(stream)))
                return None

        except Exception as e:
            self.log('getChannelStream exception while looping: {}\n Data: {}'.format(getExceptionString(), str(stream)))
        return None