#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2020 mbebe
#   Copyright (C) 2019 Mariusz89B

#   Some implementations are modified and taken from "plugin.video.ncplusgo" - thank you very much mbebe!

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
#   This add-on is unoffical and is not endorsed or supported by ITI Neovision S.A in any way. Any trademarks used belong to their owning companies and organisations.

from __future__ import unicode_literals

import sys

if sys.version_info[0] > 2:
    from cmf3 import parseDOM
    from cmf3 import replaceHTMLCodes
    import urllib.parse
else:
    from cmf2 import parseDOM
    from cmf2 import replaceHTMLCodes
    import urlparse

import os, copy, re
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, xbmcvfs
import json
import requests
import string
from strings import *
from serviceLib import *

serviceName         = 'nc+ GO'
ncplusgoUrl         = 'https://api-ncplusgo.ncplus.pl/v1/'

nctoken = ADDON.getSetting('ncplusgo_ncToken')
if not nctoken:
    ADDON.setSetting('ncplusgo_ncToken','')

#sess = requests.Session()
import cloudscraper
sess = cloudscraper.create_scraper(interpreter='native', browser={'custom': 'Dalvik/2.1.0 (Linux; U; Android 9.0; SM-G850F Build/LRX22G)'})

imei = '35'

headers = {
    'Content-Type': 'application/json; charset=UTF-8',
    'Accept': 'application/json',
    'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 9.0; SM-G850F Build/LRX22G)',
    'Host': 'api-ncplusgo.ncplus.pl',
}

timeouts = (15, 30)

class NcPlusGoUpdater(baseServiceUpdater):
    def __init__(self):
        self.serviceName        = serviceName
        self.localMapFile       = 'basemap_pl.xml'
        baseServiceUpdater.__init__(self)
        self.serviceEnabled     = ADDON.getSetting('ncplusgo_enabled')
        self.login              = ADDON.getSetting('ncplusgo_username').strip()
        self.password           = ADDON.getSetting('ncplusgo_password').strip()
        self.servicePriority    = int(ADDON.getSetting('priority_ncplusgo'))
        self.devicekey          = ADDON.getSetting('ncplusgo_imei')
        self.url                = ncplusgoUrl
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

    def IMEI(self):
        import random  
        def luhn_residue(digits):
            return sum(sum(divmod(int(d)*(1 + i%2), 10))for i, d in enumerate(digits[::-1])) % 10

        part = ''.join(str(random.randrange(0,9)) for _ in range(14))
        res = luhn_residue('{}{}'.format(part, 0))
        imIE = '{}{}'.format(part, -res%10)
        ADDON.setSetting('ncplusgo_imei', (imIE))
        return imIE

    def Time():
        import datetime 
        now = datetime.datetime.now()
        ftime = now.strftime('%Y-%m-%dT%H:%M:%SZ')
        from datetime import datetime
        import time
        try:
            format_date = datetime.strptime(ftime, '%Y-%m-%dT%H:%M:%SZ')
        except TypeError:
            format_date = datetime(*(time.strptime(ftime, '%Y-%m-%dT%H:%M:%SZ')[0:6]))
        tstampnow= int('{:0}'.format(int(time.mktime(format_date.timetuple()))))
        return tstampnow

    ADDON.setSetting('ncplusgo_ftimenow', str(Time()))
    try:
        ftimenow = int(ADDON.getSetting('ncplusgo_ftimenow'))
    except:
        None

    def IMEI(self):
        import random
        def luhn_residue(digits):
            return sum(sum(divmod(int(d)*(1 + i%2), 10))for i, d in enumerate(digits[::-1])) % 10

        part = ''.join(str(random.randrange(0,9)) for _ in range(14))
        res = luhn_residue('{}{}'.format(part, 0))
        imIE= '{}{}'.format(part, -res % 10)
        ADDON.setSetting('ncplusgo_imei',(imIE))
        return imIE

    def Change(self, response):
        from datetime import datetime
        out = []
        cc = response["DevicesToReplace"]
        for c in cc:
            tyt1 = c["Name"]
            tyt2 = c["Type"]
            dat = c["CreateDate"]
            keyid = c["Key"]
            dat = dat/1000
            dat = (datetime.utcfromtimestamp(dat+3600).strftime('%Y-%m-%d %H:%M'))
            tytok = '{} ({}) - dodano: {}'.format(tyt1, tyt2, dat)
            out.append({'keyid':keyid,'label':tytok}) 
        return out

    def Search(self, response):
        cc = response["DevicesToReplace"]
        devkey = ''
        for c in cc:
            keyid = c["Key"]
            if keyid:
                devkey = keyid
                break
        return devkey

    def loginService(self, wymiana = False, dodawanie = False, resp = False):
        try:
            self.devicekey = self.IMEI()
            email = self.login
            pwd = self.password 

            if email and pwd:
                if wymiana:
                    self.devicekey = ADDON.getSetting('ncplusgo_imei')
                    dev2repl = ADDON.getSetting('ncplusgo_dev2repl')
                    data = {"DeviceTypeId":14454, "AddDevice":True, "Email":email,"Password":pwd,"DeviceName":"GT-I8200", "Token":"", "DeviceKey":self.devicekey, "PlatformCodename":"android", "DeviceToReplaceKey":dev2repl, "IsHomeNetwork":False,"ServiceType":"1"}
                    ADDON.setSetting('ncplusgo_dev2repl','')
                elif dodawanie:
                    #data = {"DeviceTypeId":14454, "AddDevice":True, "Email":email,"Password":pwd,"DeviceName":"GT-I8200", "Token":"", "DeviceKey":self.devicekey, "PlatformCodename":"android", "IsHomeNetwork":False, "ServiceType":"1"}
                    self.devicekey = self.Search(resp)
                    #ADDON.setSetting('dev2repl','')
                    ADDON.setSetting('ncplusgo_imei', self.devicekey)
                    data = {"DeviceTypeId":14454, "AddDevice":False,"Email":email, "Password":pwd, "DeviceName":"GT-I8200", "Token":"", "DeviceKey":self.devicekey, "PlatformCodename":"android", "IsHomeNetwork":False, "ServiceType":"1"}

                else:
                    devicekey = imei
                    data = {"DeviceTypeId":14454, "AddDevice":False, "Email":email, "Password":pwd, "DeviceName":"GT-I8200", "Token":"", "DeviceKey":self.devicekey, "PlatformCodename":"android", "IsHomeNetwork":False, "ServiceType":"1"}
                response = sess.post(ncplusgoUrl+'NcAccount/Login', headers = headers, json = data, timeout=timeouts).json()

                if response['Result']['Success']:
                    token = response['Token']
                    tokenexpir = response['TokenExpirationTime']
                    ADDON.setSetting('ncplusgo_tokenexpir', str(tokenexpir/1000))
                    ADDON.setSetting('ncplusgo_ncToken', token)
                    ab = True
                    response = {}
                    return ab
                else:
                    ab = False
                    msg = response['Result']["DisplayMessage"]
                    if response['Result']["MessageCodename"]=="devices_limit_exceeded_specify_device_to_remove":
                        xbmcgui.Dialog().notification(strings(30353), msg,xbmcgui.NOTIFICATION_INFO, 8000) 

                        yes = xbmcgui.Dialog().yesno(strings(30353), strings(30996))
                        if yes:
                            outs = self.Change(response)
                            label = [x.get('label') for x in outs]
                            sel = xbmcgui.Dialog().select(strings(30997), label)
                            keyid = outs[sel].get('keyid') if sel>-1 else ''
                            
                            if keyid:
                                ADDON.setSetting('ncplusgo_dev2repl', keyid)
                                self.loginService(wymiana = True)   
                    elif response['Result']["MessageCodename"]=="device_not_registered":
                        #xbmcgui.Dialog().notification(strings(30353), msg,xbmcgui.NOTIFICATION_INFO, 8000)
                        self.loginService(wymiana = False, dodawanie = True, resp = response)
                        ab = True
                    elif response['Result']["MessageCodename"]=="wsi_error_13":
                        xbmcgui.Dialog().notification(strings(30353), msg,xbmcgui.NOTIFICATION_INFO, 8000)
                        ab = False
                    else:
                        xbmcgui.Dialog().notification(strings(30353), msg,xbmcgui.NOTIFICATION_INFO, 8000)
                        ab = False
                    return ab

            else:
                self.loginErrorMessage() 
                ab = False
                return ab

        except:
            self.log('Exception while trying to log in: {}'.format(getExceptionString()))
            self.connErrorMessage()
        return False

    def getJson(self, url,params):
        email = self.login
        pwd = self.password 
        self.devicekey = ADDON.getSetting('ncplusgo_imei')
        response = sess.get(ncplusgoUrl+url, headers = headers, params = params, timeout=timeouts).json()
        try:
            if response['Result']['MessageCodename']=='token_is_not_valid':
                data = {"DeviceTypeId":14454, "AddDevice":False, "Email":email, "Password":pwd, "DeviceName":"GT-I8200","Token":"", "DeviceKey":self.devicekey, "PlatformCodename":"android", "IsHomeNetwork":False, "ServiceType":"1"}
                response = sess.post(ncplusgoUrl+'NcAccount/Login', headers=headers, json=data, timeout=timeouts).json()
                token = response['Token']
                tokenexpir = response['TokenExpirationTime']
                ADDON.setSetting('ncplusgo_tokenexpir', str(tokenexpir/1000))
                ADDON.setSetting('ncplusgo_ncToken', token)
                response = sess.get(ncplusgoUrl+url, headers = headers, params = params, timeout=timeouts).json()
            elif response['Result']['MessageCodename']=="wsi_error_10":
                data = {"DeviceTypeId":14454, "AddDevice":False, "Email":email, "Password":pwd, "DeviceName":"GT-I8200","Token":"", "DeviceKey":self.devicekey, "PlatformCodename":"android", "IsHomeNetwork":False, "ServiceType":"1"}
                response = requests.post(ncplusgoUrl+'NcAccount/Login', headers = headers, json = data, timeout=timeouts).json()
                token = response['Token']
                tokenexpir = response['TokenExpirationTime']
                ADDON.setSetting('ncplusgo_tokenexpir', str(tokenexpir/1000))
                ADDON.setSetting('ncplusgo_ncToken', token)
                response = requests.get(ncplusgoUrl+url, headers = headers, params = params, timeout=timeouts).json()
        except:
            pass
        return response

    def getChannelList(self, silent):
        result = list()

        if not self.loginService():
            return result

        self.log('\n\n')
        self.log('[UPD] Downloading list of available {} channels from {}'.format(self.serviceName, self.url))
        self.log('[UPD] -------------------------------------------------------------------------------------')
        self.log('[UPD] %-10s %-35s %-15s %-20s %-35s' % ( '-CID-', '-NAME-', '-GEOBLOCK-', '-ACCESS STATUS-', '-IMG-'))

        try:
            nctoken = ADDON.getSetting('ncplusgo_ncToken')

            params = (
                ('PlatformCodename', 'android'),
                ('token', nctoken),
                ('sortOrder', '0'),
                ('limit', '9999'),
                ('zoneCategory', ''),
                ('page', '1'),
                ('channelCodename', ''),
            )

            url = 'NcContent/GetNowOnTv'
            response = self.getJson(url,params)
            from datetime import datetime
            items=response["Contents"]
            
            for item in items:  
                if item['IsActive']:
                    name = item['Channel']['Title']
                    title = item['Channel']['Title'] + ' PL'
                    cid = item['Channel']['Codename'] + '_TS_3H'
                    img = item['IconUrl']

                    program = TvCid(cid=cid, name=name, title=title, img=img)
                    result.append(program)

            if len(result) <= 0:
                self.log('Error while parsing service {}, returned data is: {}'.format(self.serviceName, str(html)))
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
        url = ncplusgoUrl
        codename = self.channCid(chann.cid)

        try:
            nctoken = ADDON.getSetting('ncplusgo_ncToken')
            self.devicekey = ADDON.getSetting('ncplusgo_imei')
            params = (
                ('PlatformCodename', 'android'),
                ('token', nctoken),
                ('deviceKey', self.devicekey),
                ('codename', codename),
            )

            url = 'NcContent/AcquireContent2'
            response = self.getJson(url,params)
            licserv = ''
            licenseUrl = ''
            str_url = ''

            if not "DrmInfo" in response:
                data={"DeviceTypeId":14454, "AddDevice":False, "Email":self.login, "Password":self.password, "DeviceName":"GT-I8200", "Token":nctoken, "DeviceKey":self.devicekey, "PlatformCodename":"android", "IsHomeNetwork":False, "ServiceType":"1"}
                response = sess.post(ncplusgoUrl + 'NcAccount/Login', headers=headers, json=data, verify=False, timeout=timeouts).json()
                if response['Result']['Success']:
                    token = response['Token']
                    tokenexpir = response['TokenExpirationTime']
                    ADDON.setSetting('ncplusgo_tokenexpir', str(tokenexpir/1000))
                    ADDON.setSetting('ncplusgo_ncToken', token)
                    nctoken2 = ADDON.getSetting('ncplusgo_ncToken')
                    params = (
                        ('PlatformCodename', 'android'),
                        ('token', nctoken2),
                        ('deviceKey', self.devicekey),
                        ('codename', codename),
                    )
                
                    url = 'NcContent/AcquireContent2'
                    response = self.getJson(url, params)
                
            
            items = response["DrmInfo"]
            for item in items:  
                if item["DrmSystem"]=='Widevine':
                    licserv = item["LicenseServerUrl"]
                    licenseUrl = item["DrmChallengeCustomData"]
                    break

            items = response["MediaFiles"][0]['Formats']       
            for item in items:
                if item['Protection']==4:
                    str_url = item['Url']
                    str_url = requests.get(str_url, allow_redirects = False)
                    str_url = str_url.headers['Location']
                    try:
                        if 'opl-' not in str_url:
                            xx = re.findall('(\.cdn\-ncplus.pl\/.+?)$', str_url)
                            if xx:
                                str_url = 'https://opl-n02'+xx[0]
                        else:
                            str_url = str_url
                    except:
                        pass
                
            data = str_url + '|auth=SSL/TLS&verifypeer=false'
        
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