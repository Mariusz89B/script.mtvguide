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

import re, os
import xbmc, xbmcvfs
import requests
from strings import *
from serviceLib import *

serviceName         = 'Ipla'

kukz = ''

UAIPLA = "www_iplatv/12345 (Mozilla/5.0 Windows NT 6.1; Win64; x64; rv:84.0 Gecko/20100101 Firefox/84.0)"
OSINFO = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0"

try:
    if PY3:
        COOKIEFILE = os.path.join(xbmcvfs.translatePath(ADDON.getAddonInfo('profile')), 'ipla.cookie')
    else:
        COOKIEFILE = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('profile')), 'ipla.cookie')
except:
    if PY3:
        COOKIEFILE = os.path.join(xbmcvfs.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8'), 'ipla.cookie')
    else:
        COOKIEFILE = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8'), 'ipla.cookie')

sess = requests.Session()
if PY3:
    sess.cookies = http.cookiejar.LWPCookieJar(COOKIEFILE)
else:
    sess.cookies = cookielib.LWPCookieJar(COOKIEFILE)

timeouts = (15, 30)

class IplaUpdater(baseServiceUpdater):
    def __init__(self):
        self.serviceName        = serviceName
        self.localMapFile       = 'basemap_pl.xml'
        baseServiceUpdater.__init__(self)
        self.serviceEnabled     = ADDON.getSetting('ipla_enabled')
        self.login              = ADDON.getSetting('ipla_username').strip()
        self.password           = ADDON.getSetting('ipla_password').strip()
        self.api_base           = 'https://b2c-mobile.redefine.pl/rpc/'

        self.navigate           = self.api_base+'navigation/'   
        
        self.auth               = self.api_base+'auth/'

        self.headersx           = {'Accept-Charset': 'UTF-8',
                        'Content-Type': 'application/json',
                        'User-Agent': 'mipla_a/136 (Linux; U; Android 9.0; SAMSUNG; widevine=TRUE)',
                        'Host': 'b2c-mobile.redefine.pl',}

        self.headers            = {
            'Host': 'b2c-www.redefine.pl',
            'User-Agent': OSINFO,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
            'Content-Type': 'application/json;charset=utf-8',
            'Origin': 'https://www.ipla.tv',
            'DNT': '1',
            'Referer': 'https://www.ipla.tv/'}

        self.device_id = ADDON.getSetting('ipla_device_id')
        self.client_id = ADDON.getSetting('ipla_client_id')
        self.id_ = ADDON.getSetting('ipla_id_')

        self.sesstoken = ADDON.getSetting('ipla_sesstoken')
        self.sessexpir = ADDON.getSetting('ipla_sessexpir')
        self.sesskey= ADDON.getSetting('ipla_sesskey')
        
        self.myperms = ADDON.getSetting('ipla_myperm')
        self.myperms2 = None

        self.servicePriority    = int(ADDON.getSetting('priority_ipla'))
        self.addDuplicatesToList = True

        self.client = ADDON.getSetting('ipla_client')

        self.dane = self.sesstoken+'|'+self.sessexpir+'|{0}|{1}'
        
        if PY3:
            try:
                self.profilePath  = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
            except:
                self.profilePath  = xbmcvfs.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')
        else:
            try:
                self.profilePath  = xbmc.translatePath(ADDON.getAddonInfo('profile'))
            except:
                self.profilePath  = xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')

    def getRequests(self, url, data={}, headers={}, params ={}):
        if data:
            content = sess.post(url, headers=headers, json=data, params=params, verify=False, timeout=timeouts).json()
        else:
            content = sess.get(url, headers=headers, params=params, verify=False, timeout=timeouts).json()
        return content

    def loginService(self):
        try:
            if self.device_id == '' or self.client_id == '' or self.id_ == '':
                self.createDatas()

            if self.login and self.password:
                self.device_id = ADDON.getSetting('ipla_device_id')
                self.client_id = ADDON.getSetting('ipla_client_id')
                self.client = ADDON.getSetting('ipla_client')
                
                if self.client == 'Ipla':
                    post = {"id":1,"jsonrpc":"2.0","method":"login","params":{"userAgentData":{"portal":"ipla","deviceType":"pc","application":"firefox","os":"windows","build":1,"osInfo":OSINFO},"ua":UAIPLA,"authData":{"login":self.login,"password":self.password,"deviceId":{"type":"other","value":self.device_id}},"clientId":self.client_id}}
                else:
                    post = {"id":1,"jsonrpc":"2.0","method":"login","params":{"userAgentData":{"portal":"ipla","deviceType":"pc","application":"firefox","os":"windows","build":1,"osInfo":OSINFO},"ua":UAIPLA,"authData":{"loginICOK":self.login,"passwordICOK":self.password,"deviceIdICOK":{"type":"other","value":self.device_id}},"clientId":self.client_id}}
                
                data = self.getRequests(self.auth, data = post, headers=self.headers)

                if data.get('error', None):
                    msg = data['error']['data']['userMessage']
                    ADDON.setSetting('ipla_sesstoken', '')
                    ADDON.setSetting('ipla_sessexpir', '')
                    ADDON.setSetting('ipla_sesskey', '')
                    ADDON.setSetting('ipla_myperm', '')
                    ADDON.setSetting('ipla_device_id', '')
                    ADDON.setSetting('ipla_client_id', '')

                    self.loginErrorMessage() 
                    return False

                else:
                    myper = []
                    for i in data["result"]["accessGroups"]:
                        if 'sc:' in i:
                            myper.append(str(i))
                        if 'oth:' in i:
                            myper.append(str(i))

                    ADDON.setSetting('ipla_myperm', str(myper))

                    sesja = data['result']['session']
            
                    self.sesstoken = sesja['id']
                    self.sessexpir = str(sesja['keyExpirationTime'])
                    self.sesskey = sesja['key']
                    
                    ADDON.setSetting('ipla_sesstoken', self.sesstoken)
                    ADDON.setSetting('ipla_sessexpir', str(self.sessexpir))
                    ADDON.setSetting('ipla_sesskey', self.sesskey)
                    
                return True
                
        except:
            self.log('getChannelList exception: {}'.format(getExceptionString()))
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
        
            if ADDON.getSetting('ipla_device_id'):
                device_id = ADDON.getSetting('ipla_device_id')
            else:
                device_id = getSystemId(10)
            ADDON.setSetting('ipla_device_id', device_id)
            return device_id
            
        def client_id():
            client_id = ''
        
            if ADDON.getSetting('ipla_client_id'):
                client_id = ADDON.getSetting('ipla_client_id')
            else:
                client_id = getSystemId(10)
            ADDON.setSetting('ipla_client_id', client_id)
            return client_id
            
        def id_():
            id_ = ''
        
            if ADDON.getSetting('ipla_id_'):
                id_ = ADDON.getSetting('ipla_id_')
            else:
                id_ = str(int(''.join([str(random.randint(0,9)) for _ in range(4)])))
            ADDON.setSetting('ipla_id_', id_)
            return id_

        self.device_id = uniq_id()
        self.client_id = client_id()
        self.id_ = id_()

        ADDON.setSetting('ipla_logged', 'true')

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

        ADDON.setSetting('ipla_sesstoken', self.sesstoken)
        ADDON.setSetting('ipla_sessexpir', str(self.sessexpir))
        ADDON.setSetting('ipla_sesskey', self.sesskey)
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

            self.sesstoken = ADDON.getSetting('ipla_sesstoken')
            self.sessexpir = ADDON.getSetting('ipla_sessexpir')

            self.dane = self.sesstoken+'|'+self.sessexpir+'|{0}|{1}'

            dane = (self.dane).format('navigation','getTvChannels')

            authdata = self.getHmac(dane)

            self.client_id = ADDON.getSetting('ipla_client_id')

            postData = {"id":1,"jsonrpc":"2.0","method":"getTvChannels","params":{"userAgentData":{"portal":"ipla","deviceType":"pc","application":"firefox","os":"windows","build":1,"osInfo":OSINFO},"ua":UAIPLA,"authData":{"sessionToken":authdata},"clientId":self.client_id}}

            data = self.getRequests(self.navigate, data=postData, headers=self.headers)

            myper=[]

            self.myperms = ADDON.getSetting('ipla_myperm')
            for i in eval(self.myperms):
                if 'sc:' in i:

                    myper.append(str(i))
                if 'oth:' in i:
                    myper.append(str(i))

            for i in data['result']['results']:
                item = {}
                channelperms = i['grantExpression'].split('*')
                channelperms = [w.replace('+plat:all', '') for w in channelperms]
                for j in myper:
                    if j in channelperms or i['title']=='Polsat' or i['title']=='TV4':
                        img = i['thumbnails'][-1]['src']
                        cid = i['id']
                        name = i['title'].upper() 
                        title = i['title'].upper() + ' PL'

                        name = name.replace(' SD', '')
                        title = title.replace(' SD', '')

                        program = TvCid(cid=cid, name=name, title=title, img=img)
                        result.append(program)

                        self.log('[UPD] %-12s %-35s %-35s' % (cid, name, title))

            if len(result) <= 0:
                self.log('Error while parsing service %s' % (self.serviceName))

            self.log('-------------------------------------------------------------------------------------')

        except Exception as e:
            self.log('getChannelList exception: %s' % getExceptionString())
        return result

    def channCid(self, cid):
        try:
            r = re.compile('^(.*?)_TS_.*$', re.IGNORECASE)
            cid = r.findall(cid)[0]
        except:
            cid 

        return cid

    def getSesja(self):
        self.sesstoken = ADDON.getSetting('ipla_sesstoken')
        self.sessexpir = ADDON.getSetting('ipla_sessexpir')

        self.dane = self.sesstoken+'|'+self.sessexpir+'|{0}|{1}'

        dane = (self.dane).format('auth','getSession') #'|auth|getSession'
        authdata = self.getHmac(dane)

        self.client_id = ADDON.getSetting('ipla_client_id')

        postData = {"id":1,"jsonrpc":"2.0","method":"getSession","params":{"userAgentData":{"portal":"ipla","deviceType":"pc","application":"firefox","os":"windows","build":1,"osInfo":OSINFO},"ua":UAIPLA,"authData":{"sessionToken":authdata},"clientId":self.client_id}}

        data = self.getRequests(self.auth, data=postData, headers=self.headers)

        self.dane = self.sesja(data)
        return

    def checkAccess(self, chann):
        id_ = self.channCid(chann.cid)
        acc = False

        self.sesstoken = ADDON.getSetting('ipla_sesstoken')
        self.sessexpir = ADDON.getSetting('ipla_sessexpir')

        self.dane = self.sesstoken+'|'+self.sessexpir+'|{0}|{1}'

        dane = self.dane.format('drm','checkProductAccess')
        authdata = self.getHmac(dane)
        postData = {"id":1,"jsonrpc":"2.0","method":"checkProductAccess","params":{"userAgentData":{"portal":"ipla","deviceType":"pc","application":"firefox","os":"windows","build":1,"osInfo":OSINFO},"ua":UAIPLA,"product":{"id":id_,"type":"media","subType":"movie"},"authData":{"sessionToken":authdata},"clientId":self.client_id}}

        if 'HBOacc' in id_:

            postData = {"id":1,"jsonrpc":"2.0","method":"checkProductAccess","params":{"userAgentData":{"portal":"ipla","deviceType":"pc","application":"firefox","os":"windows","build":1,"osInfo":OSINFO},"ua":UAIPLA,"product":{"id":"hbo","type":"multiple","subType":"packet"},"authData":{"sessionToken":authdata},"clientId":self.client_id}}   
        elif 'HBOtv' in id_:
                id_=id_.split('|')[0]
                postData = {"id":1,"jsonrpc":"2.0","method":"checkProductAccess","params":{"userAgentData":{"portal":"ipla","deviceType":"pc","application":"firefox","os":"windows","build":1,"osInfo":OSINFO},"ua":UAIPLA,"product":{"id":id_,"type":"media","subType":"tv"},"authData":{"sessionToken":authdata},"clientId":self.client_id}}    
                
        data = self.getRequests('https://b2c-www.redefine.pl/rpc/drm/', data=postData, headers=self.headers)
        
        acc = True if data['result']["statusDescription"] == "has access" else False

    def getChannelStream(self, chann):
        data = None
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

                self.sesstoken = ADDON.getSetting('ipla_sesstoken')
                self.sessexpir = ADDON.getSetting('ipla_sessexpir')

                self.dane = self.sesstoken+'|'+self.sessexpir+'|{0}|{1}'

                dane = self.dane.format('navigation','prePlayData')
                
                authdata = self.getHmac(dane)
                
                postData = {"jsonrpc":"2.0","id":1,"method":"prePlayData","params":{"ua":"www_iplatv_html5/12345 (Windows 7; widevine=true)","userAgentData":{"deviceType":"pc","application":"firefox","os":"windows","build":1,"portal":"ipla","osInfo":OSINFO,"player":"html","widevine":True},"cpid":cpid,"mediaId":id_,"authData":{"sessionToken":authdata},"clientId":self.client_id}}

                data = self.getRequests(self.navigate, data=postData, headers=self.headers)

                playback = data['result']['mediaItem']['playback']
                mediaid = playback['mediaId']['id']
                mediaSources = playback['mediaSources'][0]
                keyid = mediaSources['keyId']
                sourceid = mediaSources['id']
                cc = mediaSources.get('authorizationServices', None).get('pseudo', None)
                if not cc:
                    hd = {'Accept-Charset': 'UTF-8','User-Agent': OSINFO,}
                    licenseUrl = mediaSources['authorizationServices']['widevine']['getWidevineLicenseUrl']
                    dane = self.dane.format('drm','getWidevineLicense')
                    authdata = self.getHmac(dane)
                    devcid = (self.device_id).replace('-','')
                    licenseData = quote('{"jsonrpc":"2.0","id":1,"method":"getWidevineLicense","params":{"userAgentData":{"deviceType":"pc","application":"firefox","os":"windows","build":1,"portal":"ipla","osInfo":"'+OSINFO+'","player":"html","widevine":true},"cpid":%s,"mediaId":"'%cpid+mediaid+'","sourceId":"'+sourceid+'","keyId":"'+keyid+'","object":"b{SSM}","deviceId":{"type":"other","value":"'+devcid+'"},"ua":"ipla_pc_windows_firefox_html/1 (Mozilla","authData":{"sessionToken":"'+authdata+'"},"clientId":"'+self.client_id+'"}}')
                    
                    data = mediaSources['url']
                else:
                    dane = self.dane.format('drm','getPseudoLicense')
                    authdata = self.getHmac(dane)
                    devcid = (self.device_id).replace('-','')

                    postData = {"jsonrpc":"2.0","id":1,"method":"getPseudoLicense","params":{"ua":"ipla_pc_windows_firefox_html/1 (Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:75.0) Gecko/20100101 Firefox/75.0)","userAgentData":{"deviceType":"pc","application":"firefox","os":"windows","build":1,"portal":"ipla","osInfo":OSINFO,"player":"html","widevine":True},"cpid":cpid,"mediaId":mediaid,"sourceId":sourceid,"deviceId":{"type":"other","value":devcid},"authData":{"sessionToken":authdata},"clientId":self.client_id}}

                    getData = self.getRequests('https://b2c-www.redefine.pl/rpc/drm/', data=postData, headers=self.headers)

                    data = getData['result']['url']

            if data is not None and data != "":
                chann.strm = data
                chann.lic = licenseUrl, licenseData
                
                self.log('getChannelStream found matching channel: cid: {}, name: {}, rtmp:{}'.format(chann.cid, chann.name, chann.strm))
                return chann
            else:
                self.log('getChannelStream error getting channel stream2, result: {}'.format(str(data)))
                return None

        except Exception as e:
            self.log('getChannelStream exception while looping: {}\n Data: {}'.format(getExceptionString(), str(data)))
        return None
