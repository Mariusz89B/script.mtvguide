#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2022 Mariusz89B

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
#   This add-on is unoffical and is not endorsed or supported by C More Entertainment in any way. Any trademarks used belong to their owning companies and organisations.

import sys

if sys.version_info[0] > 2:
    PY3 = True
else:
    PY3 = False

import xbmc

if PY3:
    import urllib.request, urllib.parse, urllib.error
    from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
else:
    import urllib
    from requests import HTTPError, ConnectionError, Timeout, RequestException

import os, copy, re

from strings import *
from serviceLib import *
import requests
import json
import iso8601
from datetime import timedelta
import time
import pytz
import threading
import textwrap
import uuid
import six

serviceName = 'C More'

base = ['https://cmore.dk', 'https://cmore.no', 'https://www.cmore.se']
referer = ['https://cmore.dk/', 'https://cmore.no/', 'https://www.cmore.se/']
host = ['www.cmore.dk', 'www.cmore.no', 'www.cmore.se']
cc = ['dk', 'no', 'se']
ca = ['DK', 'NO', 'SE']

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

sess = requests.Session()
timeouts = (5, 5)

class Threading(object):
    def __init__(self):
        self.thread = threading.Thread(target=self.run, args=())
        self.thread.daemon = True
        self.thread.start()

    def run(self):
        while not xbmc.Monitor().abortRequested():
            ab = CmoreUpdater().checkRefresh()
            if ab:
                result = CmoreUpdater().checkLogin()
                if result:
                    validTo, beartoken, refrtoken, cookies = result

                    ADDON.setSetting('cmore_validTo', str(validTo))
                    ADDON.setSetting('cmore_beartoken', str(beartoken))
                    ADDON.setSetting('cmore_refrtoken', str(refrtoken))
                    ADDON.setSetting('cmore_cookies', str(cookies))

            if xbmc.Monitor().waitForAbort(1):
                break

            time.sleep(60)

class CmoreUpdater(baseServiceUpdater):
    def __init__(self):
        self.serviceName        = serviceName
        self.localMapFile       = 'basemap.xml'
        if ADDON.getSetting('cmore_locale') == '0':
            self.localMapFile = 'basemap_dk.xml'
        elif ADDON.getSetting('cmore_locale') == '1':
            self.localMapFile = 'basemap_no.xml'
        elif ADDON.getSetting('cmore_locale') == '2':
            self.localMapFile = 'basemap_se.xml'

        baseServiceUpdater.__init__(self)
        self.serviceEnabled     = ADDON.getSetting('cmore_enabled') 
        self.login              = ADDON.getSetting('cmore_username').strip()
        self.password           = ADDON.getSetting('cmore_password').strip()
        self.servicePriority    = int(ADDON.getSetting('priority_cmore'))

        try:
            self.country            = int(ADDON.getSetting('cmore_locale'))
        except:
            self.country            = 0

        self.dashjs             = ADDON.getSetting('cmore_devush')
        self.sessionid          = ADDON.getSetting('cmore_sess_id')
        self.tv_client_boot_id  = ADDON.getSetting('cmore_tv_client_boot_id')
        self.timestamp          = ADDON.getSetting('cmore_timestamp')
        self.validTo            = ADDON.getSetting('cmore_validTo')
        self.beartoken          = ADDON.getSetting('cmore_beartoken')
        self.refrtoken          = ADDON.getSetting('cmore_refrtoken')
        self.cookies            = ADDON.getSetting('cmore_cookies')
        self.usern              = ADDON.getSetting('cmore_usern')
        self.subtoken           = ADDON.getSetting('cmore_subtoken')


    def sendRequest(self, url, post=False, json=None, headers=None, data=None, params=None, cookies=None, verify=True, allow_redirects=False, timeout=None):
        try:
            if post:
                response = sess.post(url, headers=headers, json=json, data=data, params=params, cookies=cookies, verify=verify, allow_redirects=allow_redirects, timeout=timeout)
            else:
                response = sess.get(url, headers=headers, json=json, data=data, params=params, cookies=cookies, verify=verify, allow_redirects=allow_redirects, timeout=timeout)

        except HTTPError as e:
            deb('HTTPError: {}'.format(str(e)))
            response = False

        except ConnectionError as e:
            deb('ConnectionError: {}'.format(str(e)))
            response = False

        except Timeout as e:
            deb('Timeout: {}'.format(str(e))) 
            response = False

        except RequestException as e:
            deb('RequestException: {}'.format(str(e))) 
            response = False

        except:
            self.connErrorMessage()
            response = False

        return response


    def createData(self):
        self.dashjs = str(uuid.uuid4())
        ADDON.setSetting('cmore_devush', str(self.dashjs))

        self.tv_client_boot_id = str(uuid.uuid4())
        ADDON.setSetting('cmore_tv_client_boot_id', str(self.tv_client_boot_id))

        self.timestamp = int(time.time())*1000
        ADDON.setSetting('cmore_timestamp', str(self.timestamp))

        self.sessionid = six.text_type(uuid.uuid4())
        ADDON.setSetting('cmore_sess_id', str(self.sessionid))


    def loginData(self, reconnect, retry=0):
        try:
            url = 'https://log.tvoip.telia.com:6003/logstash'

            headers = {
                'accept': '*/*',
                'accept-language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6,fr;q=0.5',
                'connection': 'keep-alive',
                'content-type': 'text/plain;charset=UTF-8',
                'DNT': '1',
                'origin': 'https://login.cmore.{cc}'.format(cc=cc[self.country]),
                'referer': 'https://login.cmore.{cc}/'.format(cc=cc[self.country]),
                'user-agent': UA,
            }

            data = {
                'bootId': self.tv_client_boot_id,
                'networkType': 'UNKNOWN',
                'deviceId': self.dashjs,
                'deviceType': 'WEB',
                'model': 'unknown_model',
                'productName': 'Microsoft Edge 101.0.1210.32',
                'platformName': 'Windows',
                'platformVersion': 'NT 10.0',
                'nativeVersion': 'unknown_platformVersion',
                'uiName': 'one-web-login',
                'client': 'WEB',
                'uiVersion': '1.35.0',
                'environment': 'PROD',
                'country': ca[self.country],
                'brand': 'CMORE',
                'logType': 'STATISTICS_HTTP',
                'payloads': [{
                    'sequence': 1,
                    'timestamp': self.timestamp,
                    'level': 'ERROR',
                    'loggerId': 'telia-data-backend/System',
                    'message': 'Failed to get service status due to timeout after 1000 ms'
                    }]
                }

            response = self.sendRequest(url, post=True, headers=headers, json=data, verify=True, timeout=timeouts)

            url = 'https://logingateway-cmore.clientapi-prod.live.tv.telia.net/logingateway/rest/v1/authenticate?redirectUri=https%3A%2F%2Fwww.cmore.{cc}%2F'.format(cc=cc[self.country])

            headers = {
                'authority': 'logingateway-cmore.t6a.net',
                'accept': '*/*',
                'accept-language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6,fr;q=0.5',
                'dnt': '1',
                'origin': 'https://login.cmore.{cc}'.format(cc=cc[self.country]),
                'referer': 'https://login.cmore.{cc}/'.format(cc=cc[self.country]),
                'user-agent': UA,
                'x-country': ca[self.country],
            }

            params = {
                'redirectUri': 'https://www.cmore.{cc}/'.format(cc=cc[self.country]),
            }

            data = {
                'deviceId': self.dashjs,
                'deviceType': 'WEB',
                'password': self.password,
                'username': self.login,
                'whiteLabelBrand': 'CMORE',
            }

            response = self.sendRequest(url, post=True, params=params, headers=headers, json=data, verify=True, timeout=timeouts)

            code = ''

            if response:
                j_response = response.json()
                code = j_response['redirectUri'].replace('https://www.cmore.{cc}/,https://www.cmore.{cc}/?code='.format(cc=cc[self.country]), '')

            url = 'https://logingateway.cmore.{cc}/logingateway/rest/v1/oauth/token'.format(cc=cc[self.country])

            headers = {
                'authority': 'logingateway.cmore.{cc}'.format(cc=cc[self.country]),
                'accept': 'application/json',
                'accept-language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6,fr;q=0.5',
                'dnt': '1',
                'origin': 'https://www.cmore.{cc}'.format(cc=cc[self.country]),
                'referer': 'https://www.cmore.{cc}/'.format(cc=cc[self.country]),
                'tv-client-boot-id': self.tv_client_boot_id,
                'tv-client-name': 'web',
                'user-agent': UA,
                'x-country': ca[self.country],
            }

            params = {
                'code': code,
            }

            response = self.sendRequest(url, post=True, params=params, headers=headers, timeout=timeouts)

            if not response:
                if reconnect and retry < 3:
                    retry += 1
                    self.loginService(reconnect=True, retry=retry)
                else:
                    self.connErrorMessage()
                    return False

            j_response = response.json()

            try:
                if 'Username/password was incorrect' in j_response['errorMessage']:
                    self.loginErrorMessage()
                    return False
            except:
                pass

            self.validTo = j_response.get('validTo', '')
            ADDON.setSetting('cmore_validTo', str(self.validTo))

            self.beartoken = j_response.get('accessToken', '')
            ADDON.setSetting('cmore_beartoken', str(self.beartoken))

            self.refrtoken = j_response.get('refreshToken', '')
            ADDON.setSetting('cmore_refrtoken', str(self.refrtoken))

            url = 'https://ottapi.prod.telia.net/web/{cc}/tvclientgateway/rest/secure/v1/provision'.format(cc=cc[self.country])

            headers = {
                'Accept': '*/*',
                'Accept-Language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6,fr;q=0.5',
                'Authorization': 'Bearer ' + self.beartoken,
                'Cache-Control': 'no-cache',
                'DNT': '1',
                'Origin': 'https://www.cmore.{cc}'.format(cc=cc[self.country]),
                'Referer': 'https://www.cmore.{cc}/'.format(cc=cc[self.country]),
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
                'User-Agent': UA,
                'tv-client-boot-id': self.tv_client_boot_id,
            }

            data = {
                'deviceId': self.dashjs,
                'drmType': 'WIDEVINE',
                'uiName': 'one-web',
                'uiVersion': '1.43.0',
                'nativeVersion': 'NT 10.0',
                'model': 'windows_desktop',
                'networkType': 'unknown',
                'productName': 'Microsoft Edge 101.0.1210.32',
                'platformName': 'Windows',
                'platformVersion': 'NT 10.0',
            }

            response = self.sendRequest(url, post=True, headers=headers, json=data, verify=True, timeout=timeouts)

            try:
                response = response.json()
                if response['errorCode'] == 61004:
                    deb('errorCode 61004')
                    self.maxDeviceIdMessage()
                    ADDON.setSetting('cmore_sess_id', '')
                    ADDON.setSetting('cmore_devush', '')
                    if reconnect and retry < 1:
                        retry += 1
                        self.loginService(reconnect=True, retry=retry)
                    else:
                        return False
                elif response['errorCode'] == 9030:
                    deb('errorCode 9030')
                    if not reconnect:
                        self.connErrorMessage() 
                    ADDON.setSetting('cmore_sess_id', '')
                    ADDON.setSetting('cmore_devush', '')
                    if reconnect and retry < 1:
                        retry += 1
                        self.loginService(reconnect=True, retry=retry)
                    else:
                        self.connErrorMessage()
                        return False

                elif response['errorCode'] == 61002:
                    deb('errorCode 61002')
                    self.tv_client_boot_id = str(uuid.uuid4())
                    ADDON.setSetting('cmore_tv_client_boot_id', str(self.tv_client_boot_id))
                    if reconnect and retry < 1:
                        retry += 1
                        self.loginService(reconnect=True, retry=retry)
                    else:
                        self.connErrorMessage()
                        return False

            except:
                pass

            cookies = {}

            self.cookies = sess.cookies
            ADDON.setSetting('cmore_cookies', str(self.cookies))

            url = 'https://tvclientgateway-cmore.clientapi-prod.live.tv.telia.net/tvclientgateway/rest/secure/v1/pubsub'

            headers = {
                'Accept': '*/*',
                'Accept-Language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6,fr;q=0.5',
                'Authorization': 'Bearer ' + self.beartoken,
                'Origin': 'https://www.cmore.{cc}'.format(cc=cc[self.country]),
                'Referer': 'https://www.cmore.{cc}/'.format(cc=cc[self.country]),
                'User-Agent': UA,
                'tv-client-boot-id': self.tv_client_boot_id,
            }

            response = self.sendRequest(url, headers=headers, cookies=sess.cookies, allow_redirects=False, timeout=timeouts)

            if not response:
                if reconnect and retry < 3:
                    retry += 1
                    self.loginService(reconnect=True, retry=retry)
                else:
                    return False

            response = response.json()

            self.usern = response['channels']['engagement']
            ADDON.setSetting('cmore_usern', str(self.usern))

            self.subtoken = response['config']['subscriberToken']
            ADDON.setSetting('cmore_subtoken', str(self.subtoken))

            return True

        except:
            self.log('loginData exception: {}'.format(getExceptionString()))
            self.connErrorMessage()
        return False

    def operatorLogin(self, operator, login, password):
        url = 'https://tve.cmore.se/country/se/operator/{operator}/user/{login}/exists'.format(operator=operator, login=login)

        headers = {
            'authority': 'tve.cmore.{cc}'.format(cc=cc[self.country]),
            'accept': '*/*',
            'accept-language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6,fr;q=0.5',
            'dnt': '1',
            'origin': 'https://login.cmore.{cc}'.format(cc=cc[self.country]),
            'referer': 'https://login.cmore.{cc}/'.format(cc=cc[self.country]),
            'user-agent': UA,
        }

        params = {
            'client': 'login-web',
        }

        data = {
            'password': password,
        }

        response = self.sendRequest(url, post=True, params=params, headers=headers, json=data, verify=True, timeout=timeouts)
        if response:
            return True
        else:
            return False

    def loginService(self, reconnect, retry=0):

        if ADDON.getSetting('cmore_tv_provider_login') == 'true':
            operator, operator_title = self.getOperator(ADDON.getSetting('cmore_operator'))
        else:
            operator = None
            ADDON.setSetting('cmore_operator_title', '')
            ADDON.setSetting('cmore_operator', '')

        if operator:
            operator_, login, password = self.setProviderCredentials(operator, operator_title)
            response = self.operatorLogin(operator_, login, password)
            if not response:
                self.loginErrorMessage() 
                return False

        else:
            if not self.login and self.password:
                self.loginErrorMessage() 
                return False

        self.dashjs = ADDON.getSetting('cmore_devush')
        self.validTo = ADDON.getSetting('cmore_validTo')

        try:
            if (self.dashjs == '' or self.validTo == ''):
                try:
                    msg = 'Hos oss på C More kan du titta som mest på två enheter samtidigt, med en begränsning på en ström för varje enskild sportsändning. Du kan se två olika matcher/livesportsändningar samtidigt men du kan inte se samma match på två olika enheter.'
                    if PY3:
                        xbmcgui.Dialog().ok('C More', str(msg))
                    else:
                        xbmcgui.Dialog().ok('C More', str(msg.encode('utf-8')))
                except:
                    pass

                self.createData()
                login = self.loginData(reconnect, retry)

            else:
                login = True

            if login:
                run = Threading()

            return login

        except:
            self.log('loginService exception: {}'.format(getExceptionString()))
            self.connErrorMessage()
        return False

    def UserInput(self, heading, hidden=False):
        keyboard = xbmc.Keyboard('', heading, hidden)
        keyboard.doModal()
        if keyboard.isConfirmed():
            query = keyboard.getText()
        else:
            query = None

        if query and len(query) > 0:
            return query
        else:
            return None

    def setProviderCredentials(self, operator, operator_title):
        operator_ = None

        operators = self.getOperators()
        for i in operators:
            if operator == i['name']:
                username_type = i['username']
                login_type = i['login']
                password_type = i['password']
                operator_ = i['name']
                title = i['title']

                info_message = re.sub('<[^<]+?>', '', i['login'])
                break

        if operator_:
            xbmcgui.Dialog().ok(title, info_message)
            login = self.UserInput(login_type + ' ' + title)
            password = self.UserInput(password_type + ' ' + title, hidden=True)

            ADDON.setSetting('cmore_operator', operator)
            ADDON.setSetting('cmore_operator_title', operator_title)

            return operator_, login, password
        else:
            self.loginErrorMessage()

    def getOperator(self, operator=None):
        if not operator:
            ADDON.setSetting('cmore_tv_provider_login', 'true')
            operators = self.getOperators()
            options = [x['title'] for x in operators]

            selected_operator = xbmcgui.Dialog().select(strings(30370), options)
            if selected_operator is not None:
                operator = operators[selected_operator]['name']
                operator_title = operators[selected_operator]['title']

        return operator, operator_title

    def getOperators(self):
        """Return a list of TV operators supported by the C More login system."""
        url = 'https://tve.cmore.se/country/se/operator'

        headers = {
            'authority': 'tve.cmore.{cc}'.format(cc=cc[self.country]),
            'accept': '*/*',
            'accept-language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6,fr;q=0.5',
            'cache-control': 'no-cache',
            'dnt': '1',
            'origin': 'https://login.cmore.{cc}'.format(cc=cc[self.country]),
            'referer': 'https://login.cmore.{cc}/'.format(cc=cc[self.country]),
            'user-agent': UA,
        }

        params = {
            'client': 'test',
        }

        response = self.sendRequest(url, params=params, headers=headers, verify=True, timeout=timeouts)
        if response:
            j_response = response.json()

            j_response['data']['operators'] = sorted(j_response['data']['operators'], key=lambda k: k['title']) 

            return j_response['data']['operators']


    def checkLogin(self):
        result = None

        refreshTimeDelta = self.refreshTimeDelta()

        if not self.validTo:
            self.validTo = datetime.datetime.now() + timedelta(days=1)

        if (not self.beartoken or refreshTimeDelta < timedelta(minutes=1)):
            login = self.loginService(reconnect=False)
            if login:
                result = self.validTo, self.beartoken, self.refrtoken, self.cookies

        return result

    def refreshTimeDelta(self):
        result = None

        if 'Z' in str(self.validTo):
            validTo = iso8601.parse_date(self.validTo)
        elif self.validTo:
            if 'T' in str(self.validTo):
                try:
                    date_time_format = '%Y-%m-%dT%H:%M:%S.%f+' + self.validTo.split('+')[1]
                except:
                    date_time_format = '%Y-%m-%dT%H:%M:%S.%f+' + self.validTo.split('+')[0]

                validTo = datetime.datetime(*(time.strptime(self.validTo, date_time_format)[0:6]))
                timestamp = int(time.mktime(validTo.timetuple()))
                tokenValidTo = datetime.datetime.fromtimestamp(int(timestamp))
            else:
                tokenValidTo = self.validTo
        else:
            tokenValidTo = datetime.datetime.now()

        result = tokenValidTo - datetime.datetime.now()

        return result

    def checkRefresh(self):
        refreshTimeDelta = self.refreshTimeDelta()

        if not self.validTo:
            self.validTo = datetime.datetime.now() + timedelta(days=1)

        if refreshTimeDelta is not None:
            refr = True if (not self.beartoken or refreshTimeDelta < timedelta(minutes=1)) else False
        else:
            refr = False

        return refr

    def getChannelList(self, silent):
        result = list()

        if not self.loginService(reconnect=False):
            return result

        self.checkLogin()

        self.log('\n\n')
        self.log('[UPD] Downloading list of available {} channels from {}'.format(self.serviceName, self.country))
        self.log('[UPD] -------------------------------------------------------------------------------------')
        self.log('[UPD] %-12s %-35s %-35s' % ( '-CID-', '-NAME-', '-TITLE-'))

        try:
            url = 'https://engagementgateway-cmore.clientapi-prod.live.tv.telia.net/engagementgateway/rest/secure/v2/engagementinfo'

            headers = {
                "User-Agent": UA,
                "Accept": "*/*",
                "Accept-Language": "sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6",
                "Authorization": "Bearer " + self.beartoken,
            }

            headers = {
                'authority': 'engagementgateway-cmore.clientapi-prod.live.tv.telia.net',
                'accept': '*/*',
                'accept-language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6,fr;q=0.5',
                'authorization': 'Bearer ' + self.beartoken,
                'dnt': '1',
                'origin': 'https://settings.cmore.{cc}'.format(cc=cc[self.country]),
                'referer': 'https://settings.cmore.{cc}/'.format(cc=cc[self.country]),
                'tv-client-boot-id': self.tv_client_boot_id,
                'user-agent': UA,
                'x-country': ca[self.country],
            }

            engagementjson = self.sendRequest(url, headers=headers, verify=True)
            if not engagementjson:
                return result

            engagementjson = engagementjson.json()

            try:
                self.engagementLiveChannels = engagementjson['channelIds']
                deb(self.engagementLiveChannels)
            except KeyError as k:
                self.engagementLiveChannels = []
                deb('errorMessage: {k}'.format(k=str(k)))

            self.engagementPlayChannels = []

            try:
               for channel in engagementjson['stores']:
                   self.engagementPlayChannels.append(channel['id'])

            except KeyError as k:
                deb('errorMessage: {k}'.format(k=str(k)))

            url = 'https://ottapi.prod.telia.net/web/{cc}/contentsourcegateway/rest/v1/channels'.format(cc=cc[self.country])

            headers = {
                'Host': host[self.country],
                'User-Agent': UA,
                'Accept': '*/*',
                'Accept-Language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6,da;q=0.5,no;q=0.4',
                'Origin': base[self.country],

            }

            j_response = self.sendRequest(url, headers=headers, verify=True) 
            if not j_response:
                return result

            j_response_2 = j_response.json()

            headers = {
                'authority': 'graphql-cmore.t6a.net',
                'accept': '*/*',
                'accept-language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6,fr;q=0.5',
                'authorization': 'Bearer ' + self.beartoken,
                'content-type': 'application/json',
                'dnt': '1',
                'origin': 'https://www.cmore.{cc}'.format(cc=cc[self.country]),
                'referer': 'https://www.cmore.{cc}/'.format(cc=cc[self.country]),
                'tv-client-boot-id': self.tv_client_boot_id,
                'tv-client-browser': 'Microsoft Edge',
                'tv-client-browser-version': '101.0.1210.32',
                'tv-client-name': 'web',
                'tv-client-os-name': 'Windows',
                'tv-client-os-version': 'NT 10.0',
                'tv-client-tz': 'Europe/Stockholm',
                'tv-client-version': '1.43.2',
                'user-agent': UA,
                'x-country': ca[self.country],
            }

            params = (
                ('operationName', 'getTvChannels'),
                ('variables', '{"limit":500,"offset":0}'),
                ('query', "\n    query getTvChannels($limit: Int!, $offset: Int!) {\n  channels(limit: $limit, offset: $offset) {\n    pageInfo {\n      totalCount\n      hasNextPage\n    }\n    channelItems {\n      id\n      name\n      \nicons {dark\n{source\n}}   }\n  }\n}\n    \n")
            )

            response = requests.get('https://graphql-cmore.t6a.net/graphql', headers=headers, params=params, verify=False)

            if not response:
                return result

            j_response = response.json()
            channels = j_response['data']['channels']['channelItems'] + j_response_2

            for channel in channels:
                if channel['id'] in self.engagementLiveChannels:
                    cid = channel["id"] + '_TS_3'
                    name = channel["name"]

                    try:
                        res = channel["resolutions"]

                        p = re.compile('\d+')
                        res_int = p.search(res[0]).group(0)

                    except:
                        res_int = 0

                    p = re.compile(r'(\s{0}$)'.format(ca[self.country]))

                    r = p.search(name)
                    match = r.group(1) if r else None

                    if match:
                        ccCh = ''
                    else:
                        ccCh = ca[self.country]

                    if int(res_int) > 576 and ' HD' not in name:
                        title = channel["name"] + ' HD ' + ccCh
                    else:
                        title = channel["name"] + ' ' + ccCh
                    img = channel["id"]

                    program = TvCid(cid=cid, name=name, title=title, img=img) 
                    result.append(program)

                    self.log('[UPD] %-12s %-35s %-35s' % (cid, name, title))

            if len(result) <= 0:
                self.log('Error while parsing service {}'.format(self.serviceName))

            self.log('-------------------------------------------------------------------------------------')

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

        self.checkLogin()

        try:
            try:
                from urllib.parse import urlencode, quote_plus, quote, unquote
            except ImportError:
                from urllib import urlencode, quote_plus, quote, unquote

            cid = self.channCid(chann.cid)

            self.sessionid = six.text_type(uuid.uuid4())
            ADDON.setSetting('cmore_sess_id', str(self.sessionid))

            streamType = 'CHANNEL'

            url = 'https://streaminggateway-telia.clientapi-prod.live.tv.telia.net/streaminggateway/rest/secure/v2/streamingticket/{type}/{cid}?country={cc}'.format(type=streamType, cid=(str(cid)), cc=cc[self.country].upper())

            headers = {
                'Connection': 'keep-alive',
                'tv-client-boot-id': self.tv_client_boot_id,
                'DNT': '1',
                'Authorization': 'Bearer '+ self.beartoken,
                'tv-client-tz': 'Europe/Stockholm',
                'X-Country': cc[self.country],
                'User-Agent': UA,
                'content-type': 'application/json',
                'Accept': '*/*',
                'Origin': base[self.country],
                'Referer': base[self.country]+'/',
                'Accept-Language': 'sv,en;q=0.9,en-GB;q=0.8,en-US;q=0.7,pl;q=0.6',
            }

            params = (
                ('country', cc[self.country].upper()),
            )

            data = {
                "sessionId": self.sessionid,
                "whiteLabelBrand":"CMORE",
                "watchMode":"LIVE",
                "accessControl":"SUBSCRIPTION",
                "device": {
                    "deviceId": self.tv_client_boot_id,
                    "category":"desktop_windows",
                    "packagings":["DASH_MP4_CTR"],
                    "drmType":"WIDEVINE",
                    "capabilities":[],
                    "screen": {
                        "height":1080,
                        "width":1920
                        },
                        "os":"Windows",
                        "model":"windows_desktop"
                        },
                        "preferences": {
                            "audioLanguage":["undefined"],
                            "accessibility":[]}
                }

            response = self.sendRequest(url, post=True, headers=headers, json=data, params=params, cookies=sess.cookies, verify=True, timeout=timeouts)
            if not response:
                self.connErrorMessage()
                return None 

            response = response.json()

            hea = ''

            LICENSE_URL = response.get('streams', '')[0].get('drm', '').get('licenseUrl', '')
            stream_url = response.get('streams', '')[0].get('url', '')
            headr = response.get('streams', '')[0].get('drm', '').get('headers', '')

            if 'X-AxDRM-Message' in headr:
                hea = 'Content-Type=&X-AxDRM-Message=' + self.dashjs

            elif 'x-dt-auth-token' in headr:
                hea = 'Content-Type=&x-dt-auth-token=' + headr.get('x-dt-auth-token', self.dashjs)

            else:
                if PY3:
                    hea = urllib.parse.urlencode(headr)
                else:
                    hea = urllib.urlencode(headr)

                if 'Content-Type=&' not in hea:
                    hea = 'Content-Type=&' + hea

            license_url = LICENSE_URL + '|' + hea + '|R{SSM}|'

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

        except Exception:
            self.log('getChannelStream exception while looping: {}\n Data: {}'.format(getExceptionString(), str(data)))
        return None
