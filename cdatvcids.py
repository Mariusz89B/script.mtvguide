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
#   This add-on is unoffical and is not endorsed or supported by WIRTUALNA POLSKA MEDIA S.A. in any way. Any trademarks used belong to their owning companies and organisations.

from __future__ import unicode_literals

import sys

import os, copy, re
import xbmc, xbmcvfs
import requests

import hashlib
import hmac
import base64

if sys.version_info[0] > 2:
    PY3 = True
else:
    PY3 = False

if PY3:
    from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
else:
    from requests import HTTPError, ConnectionError, Timeout, RequestException

from strings import *
from serviceLib import *

serviceName = 'CDA TV'

url = 'https://api.cda.pl'

class CdaTvUpdater(baseServiceUpdater):
    def __init__(self):
        self.serviceName        = serviceName
        self.localMapFile       = 'basemap.xml'
        baseServiceUpdater.__init__(self)
        self.serviceEnabled     = ADDON.getSetting('cdatv_enabled')
        self.login              = ADDON.getSetting('cdatv_username').strip()
        self.password           = ADDON.getSetting('cdatv_password').strip()
        self.servicePriority    = int(ADDON.getSetting('priority_cdatv'))
        self.token              = ADDON.getSetting('cdatv_token')

    def loginService(self):
        try:
            login = self.login
            password = self.password

            if PY3:
                password = password.encode('utf-8')
            ab = hashlib.md5(password).hexdigest()
            
            secret = "s01m1Oer5IANoyBXQETzSOLWXgWs01m1Oer5bMg5xrTMMxRZ9Pi4fIPeFgIVRZ9PeXL8mPfXQETZGUAN5StRZ9P"
            if PY3:
                secret = secret.encode('utf-8')
                ab = ab.encode('utf-8')

            hashedpassword = base64.b64encode(hmac.new(secret, ab, digestmod=hashlib.sha256).digest())
            if PY3:
                hashedpassword = hashedpassword.decode('utf-8')

            hashedpassword = hashedpassword.replace("/","_").replace("+","-").replace("=","")

            headers = {
              'User-Agent': 'pl.cda 1.0 (version 1.2.115 build 16083; Android 9; Samsung SM-J330F)',
                'Accept': 'application/vnd.cda.public+json',
                'Authorization': 'Basic YzU3YzBlZDUtYTIzOC00MWQwLWI2NjQtNmZmMWMxY2Y2YzVlOklBTm95QlhRRVR6U09MV1hnV3MwMW0xT2VyNWJNZzV4clRNTXhpNGZJUGVGZ0lWUlo5UGVYTDhtUGZaR1U1U3Q',
                'Host': 'api.cda.pl',
            }

            params = (
                ('grant_type', 'password'),
                ('login', login),
                ('password', hashedpassword),
            )

            response = requests.post(url + '/oauth/token', headers=headers, params=params, verify=False)
            try:
                response = response.json()

                self.token = response.get('access_token', '')
                ADDON.setSetting('cdatv_token', str(self.token))
                if self.token != '':
                    return True
                else:
                    self.loginErrorMessage() 
                    return False

            except:
                self.loginErrorMessage() 
                return False
            
        except:
            self.log('loginService exception: {}'.format(getExceptionString()))
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
                'User-Agent': 'pl.cda 1.0 (version 1.2.115 build 16083; Android 9; Samsung SM-J330F)',
                'Accept': 'application/vnd.cda.public+json',
                'Authorization': 'Bearer '+ str(self.token),
                'Host': 'api.cda.pl',
            }

            response = requests.get(url + '/tv/channels', headers=headers, verify=False).json()

            channels = response['channels']
            for id in channels:
                if id['manifest_dash'] != '' or id['manifest_hls'] != '':
                    name = id['title']
                    title = id['title'] + ' PL'
                    cid = id['id']
                    img = id['logo_light']

                    name = name.replace('\t', '')
                    title = title.replace('\t', '')

                    program = TvCid(cid=cid, name=name, title=title, img=img)
                    result.append(program)
            
            if len(result) <= 0:
                self.log('Error while parsing service {}, returned data is: {}'.format(self.serviceName, str(response)))

        except:
            self.log('getChannelList exception: {}'.format(getExceptionString()))
        return result

    def getChannelStream(self, chann):
        data = None

        try:
            headers = {
                'User-Agent': 'pl.cda 1.0 (version 1.2.115 build 16083; Android 9; Samsung SM-J330F)',
                'Accept': 'application/vnd.cda.public+json',
                'Authorization': 'Bearer '+ str(self.token),
                'Host': 'api.cda.pl',
            }

            response = requests.get(url + '/tv/channels', headers=headers, verify=False).json()

            channels = response['channels']
            for id in channels:
                if id['id'] == chann.cid:
                    if id['manifest_dash']:
                        stream = id['manifest_dash']
                    else:
                        stream = id['manifest_hls']

                    license = id['drm_widevine']
                    headr = id['drm_header_value']
                        
                    hea = 'Content-Type=&x-dt-custom-data=' + headr                    

            data = stream

            if data is not None and data != "": 
                chann.lic = license, hea
                chann.strm = data
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