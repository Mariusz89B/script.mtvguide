#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2020 Mariusz89B
#   Copyright (c) 2017 Nils Emil Svensson

#   Some implementations are modified and taken from "plugin.video.cmore" - thank you very much emilsvennesson!

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

if PY3:
    import urllib.request, urllib.parse, urllib.error
else:
    import urllib

import re, os
import requests
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, xbmcvfs
import inputstreamhelper

import json
import calendar
import time
from collections import OrderedDict
from datetime import datetime, timedelta

import requests
import iso8601

import string

from strings import *
from serviceLib import *

serviceName         = 'C More'

base_url = 'https://cmore-mobile-bff.b17g.services'

timeouts = (30, 60)

class CmoreUpdater(baseServiceUpdater):
    def __init__(self):
        self.serviceName        = serviceName
        self.localMapFile       = 'basemap.xml'
        if ADDON.getSetting('cmore_locale') == 'cmore.se':
            self.localMapFile = 'basemap_se.xml'
            locale = 'sv_SE'
        elif ADDON.getSetting('cmore_locale') == 'cmore.dk':
            self.localMapFile = 'basemap_dk.xml'
            locale = 'da_DK'
        elif ADDON.getSetting('cmore_locale') == 'cmore.no':
            self.localMapFile = 'basemap_no.xml'
            locale = 'nb_NO'
        else:
            locale = ''

        baseServiceUpdater.__init__(self)
        self.serviceEnabled     = ADDON.getSetting('cmore_enabled')
        self.servicePriority    = int(ADDON.getSetting('priority_cmore'))
        self.addDuplicatesToList = True
        self.locale = locale
        self.locale_suffix = self.locale.partition('_')[2].lower()
        self.http_session = requests.Session()
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
                
        self.config_path = os.path.join(self.profilePath, 'cmore.cookie')
        self.config_version = '3.14.1'
        if self.serviceEnabled == 'true':
            self.config = self.get_config()
        self.client = 'cmore-kodi'

    class CMoreError(Exception):
        pass

    def get_addon(self):
        """Returns a fresh addon instance."""
        return Addon()

    def get_setting(self, setting_id):
        setting = ADDON.getSetting(setting_id)
        if setting == 'true':
            return True
        elif setting == 'false':
            return False
        else:
            return setting

    def set_setting(self, key, value):
        return ADDON.setSetting(key, value)

    def dialog(self, dialog_type, heading, message=None, options=None, nolabel=None, yeslabel=None):
        dialog = xbmcgui.Dialog()
        if dialog_type == 'ok':
            dialog.ok(heading, message)
        elif dialog_type == 'yesno':
            return dialog.yesno(heading, message, nolabel=nolabel, yeslabel=yeslabel)
        elif dialog_type == 'select':
            ret = dialog.select(heading, options)
            if ret > -1:
                return ret
            else:
                return None

    def get_user_input(self, heading, hidden=False):
        keyboard = xbmc.Keyboard('', heading, hidden)
        keyboard.doModal()
        if keyboard.isConfirmed():
            query = keyboard.getText()
            deb('User input string: {}'.format(query))
        else:
            query = None

        if query and len(query) > 0:
            return query
        else:
            return None

    def get_numeric_input(self, heading):
        dialog = xbmcgui.Dialog()
        numeric_input = dialog.numeric(0, heading)

        if len(numeric_input) > 0:
            return str(numeric_input)
        else:
            return None

    def make_request(self, url, method, params=None, payload=None, headers=None):
        """Make an HTTP request. Return the response."""
        #deb('Request URL: {}'.format(url))
        #deb('Method: {}'.format(method))
        #if params:
            #deb('Params: {}'.format(params))
        #if payload:
            #deb('Payload: {}'.format(payload))
        #if headers:
            #deb('Headers: {}'.format(headers))

        if method == 'get':
            req = self.http_session.get(url, params=params, headers=headers, timeout=timeouts)
        elif method == 'put':
            req = self.http_session.put(url, params=params, data=payload, headers=headers, timeout=timeouts)
        else:  # post
            req = self.http_session.post(url, params=params, data=payload, headers=headers, timeout=timeouts)
        deb('Response code: {}'.format(req.status_code))
        deb('Response: {}'.format(req.content))

        if b'UNAUTHORIZED' in req.content:
            self.noPremiumMessage()

        if b'ASSET_PLAYBACK_PROXY_BLOCKED' in req.content:
            self.proxyErrorMessage()

        return self.parse_response(req.content)

    def parse_response(self, response):
        """Try to load JSON data into dict and raise potential API errors."""
        try:
            response = json.loads(response)
            if 'error' in response:
                error_keys = ['message', 'description', 'code']
                for error in error_keys:
                    if error in response['error']:
                        raise self.CMoreError(response['error'][error])
            elif 'errors' in response:
                raise self.CMoreError(response['errors'][0]['message'])
            elif 'errorCode' in response:
                raise self.CMoreError(response['message'])

        except ValueError:  # when response is not in json
            pass

        return response

    def get_config(self):
        """Return the config in a dict. Re-download if the config version doesn't match self.config_version."""
        try:
            config = json.load(open(self.config_path))['data']
        except IOError:
            self.download_config()
            config = json.load(open(self.config_path))['data']

        config_version = int(str(config['settings']['currentAppVersion']).replace('.', ''))
        version_to_use = int(str(self.config_version).replace('.', ''))
        config_lang = config['bootstrap']['suggested_site']['locale']
        if version_to_use > config_version or config_lang != self.locale:
            self.download_config()
            config = json.load(open(self.config_path))['data']

        try:
            os.remove(self.config_path)
        except:
            None

        return config

    def download_config(self):
        """Download the C More app configuration."""
        url = base_url + '/configuration'
        params = {
            'device': 'android_tab',
            'locale': self.locale
        }
        config_data = self.make_request(url, 'get', params=params)
        try:
            with open(self.config_path, 'w') as fh_config:
                fh_config.write(json.dumps(config_data))
        except:
            None

    def get_operators(self):
        """Return a list of TV operators supported by the C More login system."""
        url = self.config['links']['tveAPI'] + 'country/{0}/operator'.format(self.locale_suffix)
        params = {'client': self.client}
        data = self.make_request(url, 'get', params=params)

        telia = {'country_code': 'se', 'forgot_password_url': 'https://www.telia.se/privat/mitt-telia/', 'homepage': 'https://www.telia.se/', 'id': 2, 'login': 'Ange användarnamn och lösenord för att logga in.[CR]Mer information hittar du på vår hemsida https://www.telia.se/.', 'login_credentials': 'email', 'logo_url': None, 'name': 'telia', 'password': 'Lösenord', 'phone': None, 'support_information': '', 'title': 'Telia', 'username': 'Kundnummer'}
        data['data']['operators'].append(dict(telia))
        data['data']['operators'] = sorted(data['data']['operators'], key=lambda k: k['title']) 

        return data['data']['operators']

    def loginService(self):
        try:
            username = ADDON.getSetting('cmore_username').strip()
            password = ADDON.getSetting('cmore_password').strip()

            if ADDON.getSetting('cmore_tv_provider_login') == 'true':
                operator = self.get_operator(ADDON.getSetting('cmore_operator'))
                if not operator:
                    self.loginErrorMessage() 
                    return False
            else:
                operator = None
                self.set_setting('cmore_operator_title', '')
                self.set_setting('cmore_operator', '')

            if not username or not password:
                if operator:
                    return self.set_tv_provider_credentials()
                else:
                    self.loginErrorMessage() 
                    return False
            else:
                return True
        except:
            self.log('getChannelList exception: {}'.format(getExceptionString()))
            self.connErrorMessage()
        return False

    def loginC(self, username=None, password=None, operator=None):
        """Complete login process for C More."""
        if operator:
            url = self.config['links']['accountJune']
        else:
            url = self.config['links']['accountDelta']
        params = {'client': self.client}
        headers = {'content-type': 'application/json'}

        method = 'post'
        payload = {
            'query': 'mutation($username: String!, $password: String, $site: String) {\n  login(credentials: {username: $username, password: $password}, site: $site) {\n    user {\n      ...UserFields\n    }\n    session {\n      token\n      vimondToken\n    }\n  }\n}\nfragment UserFields on User {\n    acceptedCmoreTerms\n    acceptedPlayTerms\n    countryCode\n    email\n    firstName\n    genericAds\n    lastName\n    tv4UserDataComplete\n    userId\n    username\n    yearOfBirth\n    zipCode\n}\n',
            'variables': {
            'username': username,
            'password': password,
            'site': 'CMORE_{locale_suffix}'.format(locale_suffix=self.locale_suffix.upper())
                }
            }
        if operator:
            payload['query'] = '\n    mutation loginTve($operatorName: String!, $username: String!, $password: String, $countryCode: String!) {\n      login(tveCredentials: {\n        operator: $operatorName,\n        username: $username,\n        password: $password,\n        countryCode: $countryCode\n      }) {\n        session{\n          token\n        }\n      }\n    }'
            payload['variables']['countryCode'] = self.locale_suffix
            payload['variables']['operatorName'] = operator

        credentials = self.make_request(url, method, params=params, payload=json.dumps(payload), headers=headers)
        deb('credentials: {}'.format(credentials))
        return credentials

    def get_channels(self):
        url = self.config['links']['graphqlAPI']
        params = {'country': self.locale_suffix}
        payload = {
            'operationName': 'EpgQuery',
            'variables': {
                'date': datetime.datetime.now().strftime('%Y-%m-%d')
            },
            'query': 'query EpgQuery($date: String!) {\n  epg(date: $date) {\n    days {\n      channels {\n        asset {\n          id\n          __typename\n        }\n        channelId\n        name\n        title\n        schedules {\n          scheduleId\n          assetId\n          asset {\n            title\n            urlToCDP\n            type\n            __typename\n          }\n          nextStart\n          calendarDate\n          isPremiere\n          isLive\n          program {\n            programId\n            title\n            seasonNumber\n            episodeNumber\n            duration\n            category\n            shortSynopsis\n            imageId\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n'
        }

        headers = {'content-type': 'application/json'}
        data = self.make_request(url, 'post', params=params, payload=json.dumps(payload), headers=headers)['data']
        return data['epg']['days'][0]['channels']

    def image_proxy(self, image_url):
        """Request the image from C More's image proxy. Can be extended to resize/add image effects automatically.
        See https://imageproxy.b17g.services/docs for more information."""
        if image_url:
            return '{0}?source={1}'.format(self.config['links']['imageProxy'], image_url)
        else:
            return None

    def parse_datetime(self, event_date, localize=True):
        """Parse date string to datetime object."""
        if 'Z' in event_date:
            datetime_obj = iso8601.parse_date(event_date)
            if localize:
                datetime_obj = self.utc_to_local(datetime_obj)
        else:
            date_time_format = '%Y-%m-%dT%H:%M:%S+' + event_date.split('+')[1]  # summer/winter time changes format
            datetime_obj = datetime(*(time.strptime(event_date, date_time_format)[0:6]))
        return datetime_obj

    def utc_to_local(self, utc_dt):
        # get integer timestamp to avoid precision lost
        timestamp = calendar.timegm(utc_dt.timetuple())
        local_dt = datetime.datetime.fromtimestamp(timestamp)
        assert utc_dt.resolution >= timedelta(microseconds=1)
        return local_dt.replace(microsecond=utc_dt.microsecond)

    def getChannelList(self, silent):
        result = list()

        if not self.loginService():
            return result

        self.log('\n\n')
        self.log('[UPD] Downloading list of available {} channels from {}'.format(self.serviceName, self.url))
        self.log('[UPD] -------------------------------------------------------------------------------------')
        self.log('[UPD] %-10s %-35s %-15s %-20s %-35s' % ( '-CID-', '-NAME-', '-GEOBLOCK-', '-ACCESS STATUS-', '-IMG-'))

        try: 
            channels = self.get_channels()
            for channel in channels:
                programs = [x for x in channel['schedules'] if datetime.datetime.now() >= self.parse_datetime(x['calendarDate'])]
                if programs:
                    current_program = programs[-1]['program']
                else:
                    continue  # no current live program

                cid = channel['asset']['id'] 
                name = channel['title']

                if self.locale == 'sv_SE':
                    title = channel['title']+' SE'
                elif self.locale == 'da_DK':
                    title = channel['title']+' DK'
                elif self.locale == 'nb_NO':
                    title = channel['title']+' NO'
                else:
                    title = ''

                img = current_program['imageId']

                program = TvCid(cid=cid, name=name, title=title, img=img)
                result.append(program)

            if len(result) <= 0:
                self.log('Error while parsing service {}, returned data is: {}'.format(self.serviceName, str(response)))
        except:
            self.log('getChannelList exception: {}'.format(getExceptionString()))
        return result 

    def set_login_credentials(self):
        username = ADDON.getSetting('cmore_username').strip()
        password = ADDON.getSetting('cmore_password').strip()

        if ADDON.getSetting('cmore_tv_provider_login') == 'true':
            operator = self.get_operator(ADDON.getSetting('cmore_operator'))
            if not operator:
                return False
        else:
            operator = None
            self.set_setting('cmore_operator_title', '')
            self.set_setting('cmore_operator', '')

        if not username or not password:
            if operator:
                return self.set_tv_provider_credentials()
            else:
                self.loginErrorMessage()
                return False
        else:
            return True

    def get_token(self):
        if not ADDON.getSetting('cmore_username') or not ADDON.getSetting('cmore_password'):
            self.set_login_credentials()
        username = ADDON.getSetting('cmore_username').strip()
        password = ADDON.getSetting('cmore_password').strip()
        operator = ADDON.getSetting('cmore_operator').strip()
        login_data = self.loginC(username, password, operator)
        if 'data' in str(login_data) and 'login' in login_data['data']:
            self.set_setting('cmore_login_token', login_data['data']['login']['session']['token'])
            return login_data['data']['login']['session']['token']
        else:
            return ''

    def set_tv_provider_credentials(self):
        operator = ADDON.getSetting('cmore_operator')
        operators = self.get_operators()
        for i in operators:
            if operator == i['name']:
                username_type = i['username']
                password_type = i['password']
                info_message = re.sub('<[^<]+?>', '', i['login'])  # strip html tags
                break
        self.dialog('ok', ADDON.getSetting('cmore_operator_title'), message=info_message)
        username = self.get_user_input(strings(59952) + ' (C More)')
        password = self.get_user_input(strings(59953) + ' (C More)', hidden=True)

        if username and password:
            self.set_setting('cmore_username', username)
            self.set_setting('cmore_password', password)
            return True
        else:
            return False

    def set_locale(self, locale=None):
        countries = ['sv_SE', 'da_DK', 'nb_NO']
        if not locale:
            options = ['cmore.se', 'cmore.dk', 'cmore.no']
            selected_locale = self.dialog('select', strings(30368), options=options)
            if selected_locale is None:
                selected_locale = 0  # default to .se
            self.set_setting('cmore_locale_title', options[selected_locale])
            self.set_setting('cmore_locale', countries[selected_locale])
            self.set_setting('cmore_login_token', '')  # reset token when locale is changed

        return True

    def get_operator(self, operator=None):
        if not operator:
            self.set_setting('cmore_tv_provider_login', 'true')
            operators = self.get_operators()
            options = [x['title'] for x in operators]

            selected_operator = self.dialog('select', strings(30370), options=options)
            if selected_operator is not None:
                operator = operators[selected_operator]['name']
                operator_title = operators[selected_operator]['title']
                self.set_setting('cmore_operator', operator)
                self.set_setting('cmore_operator_title', operator_title)

        return ADDON.getSetting('cmore_operator')

    def get_stream(self, chann, login_token):
        """Return stream data in a dict for a specified video ID."""
        init_data = self.get_playback_init()
        asset = self.get_playback_asset(chann, init_data)
        url = '{playback_api}{media_uri}'.format(playback_api=init_data['envPlaybackApi'], media_uri=asset['mediaUri'])
        headers = {'x-jwt': 'Bearer {login_token}'.format(login_token=login_token)}
        stream = self.make_request(url, 'get', headers=headers)['playbackItem']

        return stream

    def get_playback_init(self):
        """Get playback init data (API URL:s and request variables etc)"""
        deb('Getting playback init.')
        url = 'https://bonnier-player-android-prod.b17g.net/init'
        params = {
            'domain': 'cmore.{locale_suffix}'.format(locale_suffix=self.locale_suffix)
        }
        data = self.make_request(url, 'get', params=params)['config']
        return data

    def get_playback_asset(self, chann, init_data):
        """Get playback metadata needed to complete the stream request."""
        deb('Getting playback asset for video id {chann}'.format(chann=chann))
        url = '{playback_api}/asset/{chann}'.format(playback_api=init_data['envPlaybackApi'], chann=chann)
        params = {
            'service': 'cmore.{locale_suffix}'.format(locale_suffix=self.locale_suffix),
            'device': init_data['envPlaybackDevice'],
            'protocol': init_data['envPlaybackProtocol'],
            'drm': init_data['envPlaybackDrm']
        }
        asset = self.make_request(url, 'get', params=params)
        return asset

    def channCid(self, cid):
        try:
            r = re.compile('^(.*?)_TS_.*$', re.IGNORECASE)
            cid = r.findall(cid)[0]
        except:
            cid 

        return cid
        
    def getChannelStream(self, chann):
        data = None

        cid = self.channCid(chann.cid)

        try:
            login_token = ADDON.getSetting('cmore_login_token')
            if not login_token:
                login_token = self.get_token()

            try:
                data = self.get_stream(cid, login_token=login_token)
            except self.CMoreError as error:
                if str(error) == 'User is not authenticated':
                    login_token = self.get_token()
                    try:
                        data = self.get_stream(cid, login_token)
                    except:
                        data = None
                        self.noPremiumMessage()
        
            if data is not None and data != "":
                chann.strm = data['manifestUrl']
                chann.lic = data

                try:
                    self.log('getChannelStream found matching channel: cid: {}, name: {}, rtmp:{}'.format(cid, chann.name, chann.strm))
                except:
                    self.log('getChannelStream found matching channel: cid: {}, name: {}, rtmp:{}'.format(str(cid), str(chann.name), str(chann.strm)))
                return chann
            else:
                self.log('getChannelStream error getting channel stream2, result: {}'.format(str(data)))
                return None

        except Exception as e:
            self.log('getChannelStream exception while looping: {}\n Data: {}'.format(getExceptionString(), str(data)))
        return None