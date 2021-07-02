#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2018 Mariusz89B
#   Copyright (C) 2016 Andrzej Mleczko

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

import sys

import requests

if sys.version_info[0] > 2:
    from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
    import urllib.request as Request
    from urllib.error import HTTPError, URLError
else:
    from requests import HTTPError, ConnectionError, Timeout, RequestException
    import urllib2 as Request
    from urllib2 import HTTPError, URLError

import copy, re
import xbmc, xbmcgui, xbmcvfs
from strings import *
from serviceLib import *
import cloudscraper 

from contextlib import contextmanager

sess = cloudscraper.create_scraper()
scraper = cloudscraper.CloudScraper()

serviceName   = 'playlist'

playlists = ['playlist_1', 'playlist_2', 'playlist_3', 'playlist_4', 'playlist_5']

class PlaylistUpdater(baseServiceUpdater):
    def __init__(self, instance_number):
        self.serviceName        = serviceName + "_{}".format(instance_number)
        self.instance_number    = str(instance_number)
        self.localMapFile       = 'playlistmap.xml'
        baseServiceUpdater.__init__(self)
        self.servicePriority    = int(ADDON.getSetting('{}_priority'.format(self.serviceName)))
        self.serviceDisplayName = ADDON.getSetting('{}_display_name'.format(self.serviceName))
        self.source             = ADDON.getSetting('{}_source'.format(self.serviceName))
        self.addDuplicatesToList = True
        self.useOnlineMap       = False

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

        if int(instance_number) <= int(ADDON.getSetting('nr_of_playlists')):
            self.serviceEnabled  = ADDON.getSetting('{}_enabled'.format(self.serviceName))
        else:
            self.serviceEnabled = 'false'

        if self.source == '0':
            self.url = ADDON.getSetting('{}_url'.format(self.serviceName))
        else:
            if sys.version_info[0] > 2:
                self.url = xbmcvfs.translatePath(ADDON.getSetting('{}_file'.format(self.serviceName)))
            else:
                self.url = xbmc.translatePath(ADDON.getSetting('{}_file'.format(self.serviceName)))

        if ADDON.getSetting('{}_high_prio_hd'.format(self.serviceName)) == 'true':
            self.hdStreamFirst = True
        else:
            self.hdStreamFirst = False

        if ADDON.getSetting('{}_stop_when_starting'.format(self.serviceName)) == 'true':
            self.stopPlaybackOnStart = True
        else:
            self.stopPlaybackOnStart = False

    def requestUrl(self, path):
        content = None
        try:
            headers = { 'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0' }
            headers['Keep-Alive'] = 'timeout=60'
            headers['Connection'] = 'Keep-Alive'
            headers['ContentType'] = 'application/x-www-form-urlencoded'
            headers['Accept-Encoding'] = 'gzip'

            content = scraper.get(path, headers=headers, allow_redirects=False, verify=False, timeout=60).content.decode('utf-8')

        except:
            try:
                content = self.sl.getJsonFromExtendedAPI(path).decode('utf-8')
            except:
                pass

        return content

    def cachePlaylist(self, upath):
        n = datetime.datetime.now()
        d = datetime.timedelta(days=int(ADDON.getSetting('{playlist}_refr_days'.format(playlist=self.serviceName))))

        if sys.version_info[0] > 2:
            tnow = datetime.datetime.timestamp(n)
        else:
            from time import time
            tnow = str(time()).split('.')[0]

        tdel = d.total_seconds()

        path = os.path.join(self.profilePath, 'playlists')
        filepath = os.path.join(self.profilePath, 'playlists', '{playlist}.m3u'.format(playlist=self.serviceName))
        
        try:
            filename = os.path.basename(filepath)
            timestamp = str(os.path.getmtime(filepath)).split('.')[0]
        except:
            timestamp = tnow

        if not os.path.exists(path):
            os.makedirs(path)

        url_setting = ADDON.getSetting('{playlist}_url'.format(playlist=self.serviceName))
        
        urlpath = os.path.join(self.profilePath, 'playlists', '{playlist}.url'.format(playlist=self.serviceName))
        if os.path.exists(urlpath):
            if sys.version_info[0] > 2:
                url = open(urlpath, 'r', encoding='utf-8').read()
            else:
                url = open(urlpath, 'r').read()
        else:
            url = url_setting

        if (int(tnow) >= int(timestamp) + int(tdel)) or not os.path.exists(filepath) or os.stat(filepath).st_size <= 0 or url != url_setting:
            content = self.requestUrl(upath)
            if not '#EXTINF' in content:
                content = None
                
            for f in os.listdir(path):
                if not f.endswith(".m3u") or not f.endswith(".url"):
                    continue
                filename = os.path.basename(filepath)
                if self.serviceName in filename:
                    os.remove(os.path.join(path, f))

            if sys.version_info[0] > 2:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

                with open(urlpath, 'w', encoding='utf-8') as f2:
                    f2.write(url_setting)
                    
            else:
                with open(filepath, 'w') as f:
                    f.write(content.encode('utf-8'))

                with open(urlpath, 'w') as f2:
                    f2.write(url_setting.encode('utf-8'))

        else:
            if sys.version_info[0] > 2:
                content = open(filepath, 'r', encoding='utf-8').read()
            else:
                content = open(filepath, 'r').read()

        return content

    def downloadPlaylist(self, path):
        content = None
        start_time = datetime.datetime.now()

        while (content is None or content == '') and (datetime.datetime.now() - start_time).seconds < 10:
            try:
                if ADDON.getSetting('{}_refr'.format(self.serviceName)) == 'true':
                    content = self.cachePlaylist(path)
                else:
                    content = self.requestUrl(path)

            except Exception as ex:
                self.log('downloadPlaylist Error {}'.format(getExceptionString()))

            if (content is None or content == '') and (datetime.datetime.now() - start_time).seconds < 10:
                self.log('downloadPlaylist Failed, sleeping')
                time.sleep(0.5)

        return content


    def getPlaylistContent(self, path, urltype):
        content = ''

        fpath = os.path.join(self.profilePath, 'playlists')
        filepath = os.path.join(self.profilePath, 'playlists', '{playlist}.m3u'.format(playlist=self.serviceName))

        try:
            playlists.remove(self.serviceName)

            for f in os.listdir(fpath):
                for playlist in playlists:
                    try:
                        os.remove(os.path.join(fpath, '{playlist}.m3u'.format(playlist=playlist)))
                        os.remove(os.path.join(fpath, '{playlist}.url'.format(playlist=playlist)))
                    except:
                        pass
        except:
            pass

        try:
            self.log('getPlaylistContent opening playlist: %s, urltype: %s' % (path, urltype))
            if urltype == '0':
                tmpcontent = self.downloadPlaylist(path)

                if tmpcontent is None or tmpcontent == '':
                    raise Exception
            else:
                try:
                    p = re.compile('http[s]?:\/\/')
                    
                    if p.match(path):
                        if sys.version_info[0] > 2:
                        	lf = open(path, 'r', encoding='utf-8')
                        else:
                            lf = open(path, 'r')
                    else:
                        if sys.version_info[0] > 2:
                            lf = open(path, 'r', encoding='utf-8')
                        else:
                            lf = open(path, 'r')

                    tmpcontent = lf.read()
                    lf.close()
                    if tmpcontent is None or tmpcontent == "":
                        raise Exception
                except:
                    self.log('getPlaylistContent opening normally Error %s, type: %s, url: %s' % (getExceptionString(), urltype, path) )
                    self.log('getPlaylistContent trying to open file using xbmcvfs')
                    lf = xbmcvfs.File(path)
                    tmpcontent = lf.read()
                    lf.close()
                    if tmpcontent is None or tmpcontent == "":
                        raise Exception

            content = tmpcontent
        except:
            self.log('getPlaylistContent opening Error {}, type: {}, url: {}'.format(getExceptionString(), urltype, path) )
            if sys.version_info[0] > 2:
                xbmcgui.Dialog().notification(strings(59905), strings(57049) + ' ' + self.serviceName + ' (' + self.getDisplayName() + ') ' + strings(57050), time=10000, sound=False)
            else:
                xbmcgui.Dialog().notification(strings(59905).encode('utf-8'), strings(57049).encode('utf-8') + ' ' + self.serviceName + ' (' + self.getDisplayName() + ') ' + strings(57050).encode('utf-8'), time=10000, sound=False)
        return content

    def getChannelList(self, silent):
        result = list()
        try:
            regexReplaceList = list()

            sdList = list()
            hdList = list()
            uhdList = list()

            cleanup_regex      =     re.compile("\[COLOR\s*\w*\]|\[/COLOR\]|\[B\]|\[/B\]|\[I\]|\[/I\]|^\s*|\s*$",  re.IGNORECASE)

            #regexReplaceList.append( re.compile('[^A-Za-z0-9+/:]+',                                                re.IGNORECASE) )
            regexReplaceList.append( re.compile('[^A-Za-zÀ-ȕ0-9+/:]+',                                                re.IGNORECASE) )
            regexReplaceList.append( re.compile('\sL\s',                                                           re.IGNORECASE) )
            regexReplaceList.append( re.compile('(\s|^)(Feed|Europe|SD|FULL|ADULT:|EXTRA:|VIP:|VIP|Audio|Backup|Multi|Sub|VIASAT:|XXX|XXX:|\d{1,2}\s*fps|Live\s*During\s*Events\s*Only)(?=\s|$)',  re.IGNORECASE) )
            regexReplaceList.append( re.compile('(\s|^)(LQ|HQ|RAW|LOW|HIGH|QUALITY)(?=\s|$)',  re.IGNORECASE) )

            langReplaceList = list()
            regexRemoveList = list()

            #langReplaceList.append({ 'regex' : re.compile('(\s|^)(pl/en|Polska|Poland|PL:?)(?=\s|$)|^(PL:)', re.IGNORECASE), 'lang' : 'PL'})
            #if ADDON.getSetting('show_group_channels') == 'false':
            regexRemoveList.append( re.compile('(\s|^)(L\s*)?(AE:?|AF:?|AFG:?|AFR:?|AL:?|ALB:?|AO:?|AU:?|AR:?|ARB:?|ARG:?|AT:?|AZ:?|BE:?|BD:?|BF:?|BG:?|BIH:?|BJ:?|BR:?|CAR:?|CG:?|CH:?|CM:?|CN:?|CY:?|DZ:?|EE:?|EG:?|EN:?|ES:?|EXYU:?|FI:?|GA:?|GH:?|GN:?|GR:?|HN:?|HU:?|IL:?|IN:?|IQ:?|IR:?|IS:?|JO:?|JP:?|KE:?|KRD:?|KOR:?|KU:?|KW:?|LAM:?|LATINO:?|LB:?|LE:?|LT:?|LU:?|LY:?|MA:?|MK:?|ML:?|MN:?|MT:?|MY:?|MX:?|NG:?|OM:?|PH:?|PK:?|PT:?|QA:?|RO:?|RO/HU:?|RS:?|RU:?|RUS:?|SA:?|SAC:?|SC:?|SG:?|SI:?|SL:?|SN:?|SO:?|SY:?|TD:?|TH:?|TN:?|TR:?|UA:?|VN:?|YE:?|ZA|24/7:?:?|S\d+\sE\d+|19\d\d|20\d\d|S\s*\d\d\s*E\s*\d\d)(?=\s|$)', re.IGNORECASE) )
            regexRemoveList.append( re.compile('(\s|^)(L\s*)?(Afghanistan:?|Africa:?|Albania:?|Algeria:?|America:?|Andorra:?|Angola:?|Antigua\sand\sBarbuda:?|Arab\sCountries:?|Argentina:?|Armenia:?|Asia:?|Australia:?|Austria:?|Azerbaijan:?|Bahamas:?|Bahrain:?|Bangladesh:?|Barbados:?|Belarus:?|Belize:?|Benin:?|Bhutan:?|Bolivia:?|Botswana:?|Brazil:?|Brunei:?|Bulgaria:?|Burkina\sFaso:?|Burma:?|Burundi:?|Cabo\sVerde:?|Cambodia:?|Cameroon:?|Canada:?|Central\sAfrican\sRepublic:?|Chad:?|Chile:?|China:?|Colombia:?|Comoros:?|Congo:?|Costa\sRica:?|Cote\sd\sIvoire:?|Cuba:?|Cyprus:?|Djibouti:?|Dominica:?|Dominican\sRepublic:?|Ecuador:?|Egypt:?|El\sSalvador:?|Equatorial\sGuinea:?|Eritrea:?|Estonia:?|Eswatini:?|Ethiopia:?|Fiji:?|Finland:?|Gabon:?|Gambia:?|Georgia:?|Ghana:?|Greece:?|Grenada:?|Guatemala:?|Guinea:?|Guinea-Bissau:?|Guyana:?|Haiti:?|Honduras:?|Hungary:?|Iceland:?|India:?|Indonesia:?|Iran:?|Iraq:?|Ireland:?|Israel:?|Jamaica:?|Japan:?|Jordan:?|Kazakhstan:?|Kenya:?|Kiribati:?|Korea:?|Kosovo:?|Kurdistan:?|Kuwait:?|Kyrgyzstan:?|Laos:?|Latvia:?|Lebanon:?|Lesotho:?|Liberia:?|Libya:?|Liechtenstein:?|Lithuania:?|Madagascar:?|Malawi:?|Malaysia:?|Maldives:?|Mali:?|Malta:?|Marshall\sIslands:?|Mauritania:?|Mauritius:?|Micronesia:?|Moldova:?|Monaco:?|Mongolia:?|Morocco:?|Mozambique:?|Myanmar:?|Namibia:?|Nauru:?|Nepal:?|New\sZealand:?|Nicaragua:?|Niger:?|Nigeria:?|North\sKorea:?|Oman:?|Pakistan:?|Palau:?|Palestine:?|Panama:?|Papua\sNew\sGuinea:?|Paraguay:?|Peru:?|Philippines:?|Portugal:?|Qatar:?|Romania:?|Russia:?|Rwanda:?|Saint\sKitts\sand\sNevis:?|Saint\sLucia:?|Saint\sVincent\sand\sthe\sGrenadines:?|Samoa:?|San\sMarino:?|Sao\sTome\sand\sPrincipe:?|Saudi\sArabia:?|Senegal:?|Seychelles:?|Sierra\sLeone:?|Singapore:?|Slovakia:?|Solomon\sIslands:?|Somalia:?|South\sAfrica:?|South\sKorea:?|South\sSudan:?|Spain:?|Sri\sLanka:?|Sudan:?|Suriname:?|Swaziland:?|Switzerland:?|Syria:?|Taiwan:?|Tajikistan:?|Tanzania:?|Thailand:?|Timor\sLeste:?|Togo:?|Tonga:?|Trinidad\sand\sTobago:?|Tunisia:?|Turkey:?|Turkmenistan:?|Tuvalu:?|Uganda:?|Ukraine:?|United\sArab\sEmirates:?|Uruguay:?|Uzbekistan:?|Vanuatu:?|Vatican\sCity:?|Venezuela:?|Vietnam:?|Viet\sNam:?|Yemen:?|Zambia:?|Zimbabwe)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_be') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(BE:?|NL:?|HEVC:?)(?=\s|$)|^(BE:|NL:)', re.IGNORECASE), 'lang' : 'BE'})
            else:
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(BE:?|NL:?|HEVC:?|Belgium:?|Netherland:?|Luxemburg:?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_cz') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(CZ:?)(?=\s|$)|^(CZ:)', re.IGNORECASE), 'lang' : 'CZ'})
            if ADDON.getSetting('country_code_cz') == 'false':
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(CZ:?|Czech:?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_hr') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(CRO:?|HR:?|HRV:?|Yu:?)(?=\s|$)|^(CRO:|HR:|HRV:|Yu:)', re.IGNORECASE), 'lang' : 'HR'})
            if ADDON.getSetting('country_code_hr') == 'false':
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(CRO:?|HR:?|HRV:?|Yu:?|Hrvatska:?|Slovenia:?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_dk') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(DK:?)(?=\s|$)|^(DK:)', re.IGNORECASE), 'lang' : 'DK'})
            if ADDON.getSetting('country_code_dk') == 'false':
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(DK:?|Denmark:?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_uk') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(UK:?|ENG:?)(?=\s|$)|^(UK:|ENG:)', re.IGNORECASE), 'lang' : 'UK'})
            if ADDON.getSetting('country_code_uk') == 'false':
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(UK:?|ENG:?|United\sKingdom:?|Great\sBritain:?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_fr') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(FR:?)(?=\s|$)|^(FR:)', re.IGNORECASE), 'lang' : 'FR'})
            if ADDON.getSetting('country_code_fr') == 'false':
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(FR:?|France:?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_de') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(DE:?)(?=\s|$)|^(DE:)', re.IGNORECASE), 'lang' : 'DE'})
            if ADDON.getSetting('country_code_de') == 'false':
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(DE:?|Germany:?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_it') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(IT:?)(?=\s|$)|^(IT:)', re.IGNORECASE), 'lang' : 'IT'})
            if ADDON.getSetting('country_code_it') == 'false':
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(IT:?|Ital(y|ia):?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_pl') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(PL:?|pl/en|Polska|Poland)(?=\s|$)|^(PL:)', re.IGNORECASE), 'lang' : 'PL'})
            if ADDON.getSetting('country_code_pl') == 'false':
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(PL:?|pl/en|Polska:?|Poland:?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_no') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(NO:?)(?=\s|$)|^(NO:)', re.IGNORECASE), 'lang' : 'NO'})
            if ADDON.getSetting('country_code_no') == 'false':
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(NO:?|Norway:?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_srb') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(BH:?|SRB:?|SLO:?|SR:?|Yu:?)(?=\s|$)|^(SRB:|SLO:|SR:|Yu:)', re.IGNORECASE), 'lang' : 'SRB'})
            if ADDON.getSetting('country_code_srb') == 'false':
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(BH:?|SRB:?|SLO:?|SR:?|Yu:|Srbija:?|Crna\sGora:?|Macedonia:?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_se') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(SE:?|SW:?|Sweden:?|Sverige:?|Scandinavia:?|Nordic:?)(?=\s|$)|^(SE:|SW:|Sweden:|Sverige:|Scandinavia:|Nordic:)', re.IGNORECASE), 'lang' : 'SE'})
            if ADDON.getSetting('country_code_se') == 'false':
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(SE:?|SW:?|Sweden:?|Sverige:?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_us') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(Chicago:?|AM:?|CA:?|US:?|USA:?)(?=\s|$)|^(Chicago:?|AM:|CA:?|US:|USA:)', re.IGNORECASE), 'lang' : 'US'})
            if ADDON.getSetting('country_code_us') == 'false':
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(AM:?|CA:?|USA:?|US:?|(Latin\s)?America:?|United\sStates:?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_radio') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(Radio:?)(?=\s|$)|^(Radio:)', re.IGNORECASE), 'lang' : 'Radio'})
            if ADDON.getSetting('country_code_radio') == 'false':
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(Radio:?)(?=\s|$)', re.IGNORECASE) )


            regexHD            =     re.compile('(\s|^)(720p|720|FHD|1080p|1080|HD\sHD|HD)(?=\s|$)',                              re.IGNORECASE)
            regexUHD            =    re.compile('(\s|^)(4K|UHD)(?=\s|$)',                              re.IGNORECASE)

            regex_chann_name   =     re.compile('tvg-id="[^"]*"',                                                  re.IGNORECASE)
            if ADDON.getSetting('VOD_EPG') == "":
                regexCorrectStream =     re.compile('^(plugin|http|rtmp)(?!.*?[.](mp4|mkv|avi|mov|wma))',                 re.IGNORECASE)
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?((?i)VOD)(?=\s|$)', re.IGNORECASE) )
            else:
                regexCorrectStream =     re.compile('^plugin|http|^rtmp',                                                 re.IGNORECASE)

            if ADDON.getSetting('XXX_EPG') == "":
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?((?i)Adult)(?=\s|$)', re.IGNORECASE) )

            title = None
            nextFreeCid = 0
            self.log('\n\n')
            self.log('[UPD] Downloading a list of available channels for {}'.format(self.serviceName))
            self.log('[UPD] -------------------------------------------------------------------------------------')
            self.log('[UPD] %-10s %-35s %-35s' % ( '-CID-', '-NAME-', '-STREAM-'))

            channelsArray = self.getPlaylistContent(self.url.strip(), self.source).strip()

            if channelsArray is not None and channelsArray != "" and len(channelsArray) > 0:
                cleaned_playlist = cleanup_regex.sub('', channelsArray)
                
                for line in cleaned_playlist.splitlines():
                    stripLine = line.strip()

                    if '#EXTINF:' in stripLine:
                        tmpTitle = ''
                        title = ''
                        splitedLine = stripLine.split(',')

                        p = re.compile('^.*catchup-source="http[s]?.*$', re.IGNORECASE)

                        if p.match(stripLine) and ADDON.getSetting('archive_support') == 'true':
                            catchup = re.compile('catchup-source="(.*?)"')
                            catchupLine = catchup.search(stripLine).group(1)

                        if len(splitedLine) > 1:
                            tmpTitle = splitedLine[len(splitedLine) - 1].strip()

                        if tmpTitle == '':
                            match = regex_chann_name.findall(stripLine)
                            if len(match) > 0:
                                tmpTitle = match[0].replace("tvg-id=","").replace('"','').strip()

                        if tmpTitle is not None and tmpTitle != '':
                            title = tmpTitle
                            HDStream = False
                            UHDStream = False

                            for regexReplace in regexReplaceList:
                                title = regexReplace.sub(' ', title)
                            
                            title, match = regexHD.subn(' HD ', title)
                            if match > 0:
                                HDStream = True

                            title, match = regexUHD.subn(' UHD ', title)
                            if match > 0:
                                UHDStream = True

                            title = self.removeDuplicates(title)

                            for langReplaceMap in langReplaceList:
                                title, match = langReplaceMap['regex'].subn('', title)
                                if match > 0:
                                    title += ' ' + langReplaceMap['lang']

                            for regexRemove in regexRemoveList:
                                if( regexRemove.search(title) ):
                                    title = ''

                            title = title.replace('  ', ' ').strip()
                                

                    elif title is not None and regexCorrectStream.match(stripLine):
                        if title != '':
                            p = re.compile(r'.*\s[a-zA-Z]{2,3}$', re.DOTALL)

                            if not p.match(title):
                                langAList = ['Belgium', 'Czech', 'Germany', 'Danmark', 'France', 'Croatia', 'Italy', 'Norway', 'Poland', 'Sweden', 'EX-Yu', 'United Kingdom', 'USA'] 
                                langA = '|'.join(langAList)

                                langBList = ['Belgique', 'Cesko', 'Deutschland', 'Danmark', 'France', 'Hrvatska', 'Italia', 'Norge', 'Polska', 'Sverige', 'Serbia', 'Britain', 'America'] 
                                langB = '|'.join(langBList)

                                ccList = ['BE', 'CZ', 'DE', 'DK', 'FR', 'HR', 'IT', 'NO', 'PL', 'SE', 'SRB', 'UK', 'US']
                                langC = '|'.join(ccList)

                                langDList = ['BEL', 'CZE', 'GER', 'DEN', 'FRA', 'HRT', 'ITA', 'NOR', 'POL', 'SWE', 'SRB', 'ENG', 'AME']
                                langD = '|'.join(langDList)

                                ccListInt = len(ccList)
                                
                                if any(ccExt not in title for ccExt in ccList):

                                    p = re.compile('group-title=".*(L\s*)?({a}|{b}|{c}|{d})(?=\W|\s|$).*"'.format(a=langA, b=langB, c=langC, d=langD), re.IGNORECASE)
                                    try:
                                        if sys.version_info[0] > 2:
                                            group = p.search(str(splitedLine[0])).group(2)
                                        else:
                                            group = p.search(str(splitedLine[0]).encode('utf-8')).group(2)

                                        if group:
                                            for item in range(ccListInt):
                                                if group.upper() == langAList[item].upper():
                                                    subsLangA = {langAList[item]: ccList[item]}
                                                    cc = ccList[subsLangA.get(item, item)]
                                                    ccCh = cc

                                                elif group.upper() == langBList[item].upper():        
                                                    subsLangB = {langBList[item]: ccList[item]}
                                                    cc = ccList[subsLangB.get(item, item)]
                                                    ccCh = cc

                                                elif group.upper() == ccList[item].upper():
                                                    subsLangC = {ccList[item]: ccList[item]}
                                                    cc = ccList[subsLangC.get(item, item)]
                                                    ccCh = cc

                                                elif group.upper() == langDList[item].upper():
                                                    subsLangD = {langDList[item]: ccList[item]}
                                                    cc = ccList[subsLangD.get(item, item)]
                                                    ccCh = cc

                                                else:
                                                    ccCh = ''

                                                if ccCh not in title:
                                                    string = ' ' + ccCh
                                                    title = re.sub('$', string, title)

                                    except:
                                        pass

                            try:
                                catchupLine
                            except:
                                catchupLine = ''

                            channelCid = ''

                            catchupDaysList = ['catchup-days=', 'timeshift=']

                            if any(x in splitedLine[0] for x in catchupDaysList) and ADDON.getSetting('archive_support') == 'true':
                                pdays = re.compile('.*(timeshift=|catchup-days=)"(.*?)".*')
                                
                                days = pdays.search(splitedLine[0]).group(2)
                            else:
                                days = '1'

                            catchupList = ['catchup', 'timeshift']

                            if any(x in splitedLine[0] for x in catchupList) and ADDON.getSetting('archive_support') == 'true':
                                channelCid = str(nextFreeCid) + '_AR' + '_' + days
                            else:
                                channelCid = str(nextFreeCid)

                            if UHDStream:
                                channelCid = channelCid + '_UHD'
                                uhdList.append(TvCid(channelCid, title, title, stripLine, catchup=catchupLine))
                            elif HDStream:
                                channelCid = channelCid + '_HD'
                                hdList.append(TvCid(channelCid, title, title, stripLine, catchup=catchupLine))
                            else:
                                sdList.append(TvCid(channelCid, title, title, stripLine, catchup=catchupLine))

                            
                            self.log('[UPD] %-10s %-35s %-35s' % (channelCid, title, stripLine))
                            nextFreeCid = nextFreeCid + 1
                        #else:
                            #self.log('[UPD] %-10s %-35s %-35s' % ('-', 'No title!', stripLine))


            if self.hdStreamFirst:
                result = uhdList
                result.extend(hdList)
                result.extend(sdList)
            else:
                result = sdList
                result.extend(hdList)
                result.extend(uhdList)

        except Exception as ex:
            self.log('getChannelList Error %s' % getExceptionString())
        return result

    def removeDuplicates(self, s):
      p = r"\b(HD|UHD)(?:\W+\1\b)+"
      return re.sub(p, r"\1", s, flags=re.IGNORECASE)

    def getChannelStream(self, chann):
        try:
            if self.stopPlaybackOnStart and xbmc.Player().isPlaying():
                xbmc.Player().stop()
                xbmc.sleep(500)
            self.log('getChannelStream: found matching channel: cid {}, name {}, stream {}'.format(chann.cid, chann.name, chann.strm))

            return chann

        except Exception as ex:
            self.log('getChannelStream Error {}'.format(getExceptionString()))
        return None

    def log(self, message):
        if self.thread is not None and self.thread.is_alive() and self.forcePrintintingLog == False:
            self.traceList.append(self.__class__.__name__ + '_' + self.instance_number + ' ' + message)
        else:
            deb(self.__class__.__name__ + '_' + self.instance_number + ' ' + message)