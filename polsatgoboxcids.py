#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2020 mbebe
#   Copyright (C) 2020 Mariusz89B
#   Copyright (C) 2016 Andrzej Mleczko

#   Some implementations are modified and taken from "MrKnow" - thank you very much MrKnow!

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

serviceName = 'Polsat GO Box'

OSINFO = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0"
UAIPLA = "pg_pc_windows_firefox_html/1 (Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0)"

try:
    if PY3:
        COOKIEFILE = os.path.join(xbmcvfs.translatePath(ADDON.getAddonInfo('profile')), 'pgobox.cookie')
    else:
        COOKIEFILE = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('profile')), 'pgobox.cookie')
except:
    if PY3:
        COOKIEFILE = os.path.join(xbmcvfs.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8'), 'pgobox.cookie')
    else:
        COOKIEFILE = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8'), 'pgobox.cookie')

sess = requests.Session()
if PY3:
    sess.cookies = http.cookiejar.LWPCookieJar(COOKIEFILE)
else:
    sess.cookies = cookielib.LWPCookieJar(COOKIEFILE)

timeouts = (15, 30)

class PolsatGoBoxUpdater(baseServiceUpdater):
    def __init__(self):
        self.serviceName        = serviceName
        self.localMapFile       = 'basemap_pl.xml'
        baseServiceUpdater.__init__(self)
        self.serviceEnabled     = ADDON.getSetting('pgobox_enabled')
        self.login              = ADDON.getSetting('pgobox_username').strip()
        self.password           = ADDON.getSetting('pgobox_password').strip()
        self.api_base           = 'https://b2c-www.redefine.pl/rpc/'

        self.navigate           = self.api_base+'navigation/'   
        
        self.auth               = self.api_base+'auth/'

        self.headers = {
            'Host': 'b2c-www.redefine.pl',
            'User-Agent': OSINFO,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
            'Content-Type': 'application/json;charset=utf-8',
            'Origin': 'https://polsatboxgo.pl/',
            'DNT': '1',
            'Referer': 'https://polsatboxgo.pl/'
        }

        self.device_id = ADDON.getSetting('pgobox_device_id')
        self.client_id = ADDON.getSetting('pgobox_client_id')
        self.id_ = ADDON.getSetting('pgobox_id_')

        self.sesstoken = ADDON.getSetting('pgobox_sesstoken')
        self.sessexpir = ADDON.getSetting('pgobox_sessexpir')
        self.sesskey= ADDON.getSetting('pgobox_sesskey')
        
        self.myperms = ADDON.getSetting('pgobox_myperm')

        self.servicePriority    = int(ADDON.getSetting('priority_pgobox'))
        self.addDuplicatesToList = True

        self.client = ADDON.getSetting('pgobox_client')

        self.dane = self.sesstoken+'|'+self.sessexpir+'|{0}|{1}'
    

    def getRequests(self, url, data={}, headers={}, params ={}):
        if data:
            content = sess.post(url, headers=headers, json=data, params=params, verify=False, timeout=timeouts).json()
        else:
            content = sess.get(url, headers=headers, params=params, verify=False, timeout=timeouts).json()
        return content

    def loginService(self):
        try:
            self.client_id = ADDON.getSetting('pgobox_client_id')
            self.device_id = ADDON.getSetting('pgobox_device_id')
            self.id_ = ADDON.getSetting('pgobox_id_')

            if self.device_id == '' or self.client_id == '' or self.id_ == '':
                self.createDatas()

            if self.login and self.password:
                self.client = ADDON.getSetting('pgobox_client')
                
                if self.client == 'ICOK':
                    postData = {"id":1,"jsonrpc":"2.0","method":"login","params":{"ua":"pbg_mobile_android_chrome_html/1 (Mozilla/5.0 (Linux; Android 10; Redmi Note 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.62 Mobile Safari/537.36)","deviceId":{"type":"other","value":self.device_id},"userAgentData":{"portal":"pbg","deviceType":"mobile","application":"chrome","player":"html","build":1,"os":"android","osInfo":"Mozilla/5.0 (Linux; Android 10; Redmi Note 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.62 Mobile Safari/537.36"},"clientId":self.client_id,"authData":{"authProvider":"icok","login":self.login,"password":self.password,"deviceId":{"type":"other","value":self.device_id}}}}
                else:
                    postData = {"id":1,"jsonrpc":"2.0","method":"login","params":{"ua":UAIPLA,"deviceId":{"type":"other","value":self.device_id},"userAgentData":{"portal":"pbg","deviceType":"pc","application":"firefox","player":"html","build":1,"os":"windows","osInfo":OSINFO},"clientId":self.client_id,"authData":{"login":self.login,"password":self.password,"deviceId":{"type":"other","value":self.device_id}}}}

                data = self.getRequests(self.auth, data=postData, headers=self.headers)

                try:
                    if data['error']['data']["type"] == "RulesException":
                        postData = {"id":1,"jsonrpc":"2.0","method":"acceptRules","params":{"ua":"pbg_mobile_android_chrome_html/1 (Mozilla/5.0 (Linux; Android 10; Redmi Note 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.62 Mobile Safari/537.36)","deviceId":{"type":"other","value":self.device_id},"userAgentData":{"portal":"pbg","deviceType":"mobile","application":"chrome","player":"html","build":1,"os":"android","osInfo":"Mozilla/5.0 (Linux; Android 10; Redmi Note 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.62 Mobile Safari/537.36"},"clientId":self.client_id,"rulesIds":[105],"authData":{"authProvider":"icok","login":self.login,"password":self.password,"deviceId":{"type":"other","value":self.device_id}}}}
                        data = getRequests(self.auth, data=postData, headers=self.headers)
                except:
                    pass

                if data.get('error', None):
                    msg = data['error']['data']['userMessage']
                    xbmcgui.Dialog().notification(serviceName, strings(70139))
                    return False

                else:
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

                    ADDON.setSetting('pgobox_myperm', str(w_myperm))
                    self.myperms = myper

                    sesja = data['result']['session']
            
                    self.sesstoken = sesja['id']
                    self.sessexpir = str(sesja['keyExpirationTime'])
                    self.sesskey = sesja['key']
                    
                    ADDON.setSetting('pgobox_sesstoken', self.sesstoken)
                    ADDON.setSetting('pgobox_sessexpir', str(self.sessexpir))
                    ADDON.setSetting('pgobox_sesskey', self.sesskey)
                    
                return True
            
        except:
            self.log('getLogin exception: {}'.format(getExceptionString()))
            self.connErrorMessage()  
        return False

    def createDatas(self):
        import random
        def getSystemId(il):
            def gen_hex_code(myrange=6):
                return ''.join([random.choice('0123456789ABCDEF') for x in range(myrange)])
        
            systemid = gen_hex_code(il) + '-' + gen_hex_code(4) + '-' + gen_hex_code(4) + '-' + gen_hex_code(4) + '-' + gen_hex_code(12)
            systemid = systemid.strip()

            return systemid

        def uniq_id():
            device_id = ''
        
            if ADDON.getSetting('pgobox_device_id'):
                device_id = ADDON.getSetting('pgobox_device_id')
            else:
                device_id = getSystemId(10)
            ADDON.setSetting('pgobox_device_id', device_id)
            return device_id
            
        def client_id():
            client_id = ''
        
            if ADDON.getSetting('pgobox_client_id'):
                client_id = ADDON.getSetting('pgobox_client_id')
            else:
                client_id = getSystemId(10)
            ADDON.setSetting('pgobox_client_id', client_id)
            return client_id
            
        def id_():
            id_ = ''
        
            if ADDON.getSetting('pgobox_id_'):
                id_ = ADDON.getSetting('pgobox_id_')
            else:
                id_ = str(int(''.join([str(random.randint(0,9)) for _ in range(4)])))
            ADDON.setSetting('pgobox_id_', id_)
            return id_

        self.device_id = uniq_id()
        self.client_id = client_id()
        self.id_ = id_()

    def getHmac(self, dane):
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

        secretAccessKey = base64_decode(self.sesskey.replace('-','+').replace('_','/'))
        
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
        
        ADDON.setSetting('pgobox_sesstoken', self.sesstoken)
        ADDON.setSetting('pgobox_sessexpir', str(self.sessexpir))
        ADDON.setSetting('pgobox_sesskey', self.sesskey)
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

            self.sesstoken = ADDON.getSetting('pgobox_sesstoken')
            self.sessexpir = ADDON.getSetting('pgobox_sessexpir')

            self.dane = self.sesstoken+'|'+self.sessexpir+'|{0}|{1}'

            dane = (self.dane).format('navigation','getTvChannels')

            authdata = self.getHmac(dane)

            self.client_id = ADDON.getSetting('pgobox_client_id')
            self.device_id = ADDON.getSetting('pgobox_device_id')

            postData = {
                "id":1,
                "jsonrpc":"2.0",
                "method":"getTvChannels",
                "params": {
                    "filters":[],
                    "ua": UAIPLA,
                    "deviceId": {
                        "type":"other",
                        "value":self.device_id
                        },

                    "userAgentData": {
                        "portal":"pbg",
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

            self.myperms = ADDON.getSetting('pgobox_myperm')

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
        self.sesstoken = ADDON.getSetting('pgobox_sesstoken')
        self.sessexpir = ADDON.getSetting('pgobox_sessexpir')

        self.dane = self.sesstoken+'|'+self.sessexpir+'|{0}|{1}'

        dane = (self.dane).format('auth','getSession') #'|auth|getSession'
        authdata = self.getHmac(dane)

        self.client_id = ADDON.getSetting('pgobox_client_id')

        postData = {"id":1,"jsonrpc":"2.0","method":"getSession","params":{"userAgentData":{"portal":"pbg","deviceType":"pc","application":"firefox","os":"windows","build":1,"osInfo":OSINFO},"ua":UAIPLA,"authData":{"sessionToken":authdata},"clientId":self.client_id}}

        data = self.getRequests(self.auth, data=postData, headers=self.headers)

        self.dane = self.sesja(data)
        return

    def checkAccess(self, chann):
        id_ = self.channCid(chann.cid)
        acc = False

        self.sesstoken = ADDON.getSetting('pgobox_sesstoken')
        self.sessexpir = ADDON.getSetting('pgobox_sessexpir')

        self.dane = self.sesstoken+'|'+self.sessexpir+'|{0}|{1}'

        dane = self.dane.format('drm','checkProductAccess')
        authdata = self.getHmac(dane)
        postData = {"id":1,"jsonrpc":"2.0","method":"checkProductAccess","params":{"userAgentData":{"portal":"pbg","deviceType":"pc","application":"firefox","os":"windows","build":1,"osInfo":OSINFO},"ua": UAIPLA,"product":{"id":id_,"type":"media","subType":"movie"},"authData":{"sessionToken":authdata},"clientId":self.client_id}}

        if 'HBOacc' in id_:
            postData = {"id":1,"jsonrpc":"2.0","method":"checkProductAccess","params":{"userAgentData":{"portal":"pbg","deviceType":"pc","application":"firefox","os":"windows","build":1,"osInfo":OSINFO},"ua": UAIPLA,"product":{"id":"hbo","type":"multiple","subType":"packet"},"authData":{"sessionToken":authdata},"clientId":self.client_id}}   
        
        elif 'HBOtv' in id_:
                id_=id_.split('|')[0]
                postData = {"id":1,"jsonrpc":"2.0","method":"checkProductAccess","params":{"userAgentData":{"portal":"pbg","deviceType":"pc","application":"firefox","os":"windows","build":1,"osInfo":OSINFO},"ua": UAIPLA,"product":{"id":id_,"type":"media","subType":"tv"},"authData":{"sessionToken":authdata},"clientId":self.client_id}}    
                
        data = self.getRequests('https://b2c-www.redefine.pl/rpc/drm/', data=postData, headers=self.headers)
        
        acc = True if data['result']["statusDescription"] == "has access" else False

    def getChannelStream(self, chann):
        stream = None

        licenseUrl = None
        licenseData = None

        id_ = self.channCid(chann.cid)
        cpid = 0

        try:
            self.getSesja()
            acc = True
            if '|' in id_ :
                cpid = 1
                if not 'HBOtv' in id_:
                    id_ = id_.split('|')[0]
                    #cpid= 0
                else:   
                    id_ = id_#.split('|')[0]
                acc = self.checkAccess(id_)
            if acc:
                if 'HBOtv' in id_:
                    id_ = id_.split('|')[0]
                    cpid = 0

                self.sesstoken = ADDON.getSetting('pgobox_sesstoken')
                self.sessexpir = ADDON.getSetting('pgobox_sessexpir')
                self.device_id = ADDON.getSetting('pgobox_device_id')
                self.client_id = ADDON.getSetting('pgobox_client_id')

                self.dane = self.sesstoken+'|'+self.sessexpir+'|{0}|{1}'

                dane = self.dane.format('navigation','prePlayData')
                
                authdata = self.getHmac(dane)
                
                postData = {"jsonrpc":"2.0","id":1,"method":"prePlayData","params":{"ua":"pbg_pc_windows_firefox_html/1 (Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0) (Windows 7; widevine=True)","userAgentData":{"deviceType":"pc","application":"firefox","os":"windows","build":2160500,"portal":"pbg","player":"html","widevine":True},"cpid":cpid,"mediaId":id_,"authData":{"sessionToken":authdata},"clientId":self.client_id}}
            
                data = self.getRequests(self.navigate, data=postData, headers=self.headers)

                playback = data['result']['mediaItem']['playback']
                mediaid = playback['mediaId']['id']
                mediaSources = playback['mediaSources'][0]
                keyid = mediaSources['keyId']
                sourceid = mediaSources['id']
                cc = mediaSources.get('authorizationServices', None).get('pseudo', None)
                if not cc:
                    UAcp=  'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'
                    hd = {'Accept-Charset': 'UTF-8','User-Agent': UAcp,}
                    licenseUrl = mediaSources['authorizationServices']['widevine']['getWidevineLicenseUrl']
                    dane = self.dane.format('drm','getWidevineLicense')
                    authdata = self.getHmac(dane)
                    devcid = (self.device_id).replace('-','')
                    licenseData = quote('{"jsonrpc":"2.0","id":1,"method":"getWidevineLicense","params":{"userAgentData":{"deviceType":"pc","application":"firefox","os":"windows","build":2160500,"portal":"pbg","player":"html","widevine":true},"cpid":%s'%cpid+',"mediaId":"'+mediaid+'","sourceId":"'+sourceid+'","keyId":"'+keyid+'","object":"b{SSM}","deviceId":{"type":"other","value":"'+devcid+'"},"ua":"pbg_pc_windows_firefox_html/2160500","authData":{"sessionToken":"'+authdata+'"},"clientId":"'+self.client_id+'"}}')
                
                    stream = mediaSources['url']
                else:
                    dane = self.dane.format('drm','getPseudoLicense')
                    authdata = self.getHmac(dane)
                    devcid = (self.device_id).replace('-','')

                    postData = {"jsonrpc":"2.0","id":1,"method":"getPseudoLicense","params":{"ua": UAIPLA,"userAgentData":{"deviceType":"pc","application":"firefox","os":"windows","build":1,"portal":"pbg","osInfo":OSINFO,"player":"html","widevine":True},"cpid":cpid,"mediaId":mediaid,"sourceId":sourceid,"deviceId":{"type":"other","value":devcid},"authData":{"sessionToken":authdata},"clientId":self.client_id}}

                    getData = self.getRequests('https://b2c-www.redefine.pl/rpc/drm/', data=postData, headers=self.headers)

                    stream = getData['result']['url']

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
