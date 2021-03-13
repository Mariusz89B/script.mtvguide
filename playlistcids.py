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

if sys.version_info[0] > 2:
    import urllib.request as Request
    from urllib.error import HTTPError, URLError
else:
    import urllib2 as Request
    from urllib2 import HTTPError, URLError

import requests

if sys.version_info[0] > 2:
    from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
else:
    from requests import HTTPError, ConnectionError, Timeout, RequestException


import copy, re
import xbmc, xbmcgui, xbmcvfs
from strings import *
from serviceLib import *
import cloudscraper 

scraper = cloudscraper.CloudScraper()
serviceName   = 'playlist'

class PlaylistUpdater(baseServiceUpdater):
    def __init__(self, instance_number):
        self.serviceName        = serviceName + "_%s" % instance_number
        self.instance_number    = str(instance_number)
        self.localMapFile       = 'playlistmap.xml'
        baseServiceUpdater.__init__(self)
        self.servicePriority    = int(ADDON.getSetting('%s_priority' % self.serviceName))
        self.serviceDisplayName = ADDON.getSetting('%s_display_name' % self.serviceName)
        self.source             = ADDON.getSetting('%s_source'       % self.serviceName)
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
            self.serviceEnabled  = ADDON.getSetting('%s_enabled'     % self.serviceName)
        else:
            self.serviceEnabled = 'false'

        if self.source == '0':
            self.url = ADDON.getSetting('%s_url' % self.serviceName)
        else:
            if sys.version_info[0] > 2:
                self.url = xbmcvfs.translatePath(ADDON.getSetting('%s_file' % self.serviceName))
            else:
                self.url = xbmc.translatePath(ADDON.getSetting('%s_file' % self.serviceName))

        if ADDON.getSetting('%s_high_prio_hd' % self.serviceName) == 'true':
            self.hdStreamFirst = True
        else:
            self.hdStreamFirst = False

        if ADDON.getSetting('%s_stop_when_starting' % self.serviceName) == 'true':
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

            content = scraper.get(path, headers=headers, allow_redirects=False, verify=False, timeout=20).content.decode('utf-8')

        except:
            content = self.sl.getJsonFromExtendedAPI(path).decode('utf-8')

        return content

    def cachePlaylist(self, upath):
        import shutil
        n = datetime.datetime.now()
        h = datetime.timedelta(days=int(ADDON.getSetting('{playlist}_refr_days'.format(playlist=self.serviceName))))

        if sys.version_info[0] > 2:
            tnow = datetime.datetime.timestamp(n)
        else:
            from time import time
            tnow = str(time()).split('.')[0]

        tdel = h.total_seconds()

        path = os.path.join(self.profilePath, 'playlists')
        filepath = os.path.join(self.profilePath, 'playlists', '{playlist}.m3u'.format(playlist=self.serviceName))
        
        try:
            filename = os.path.basename(filepath)
            timestamp = str(os.path.getctime(filepath)).split('.')[0]
        except:
            timestamp = tnow

        if not os.path.exists(path):
            os.makedirs(path)

        url_setting = ADDON.getSetting('{playlist}_url'.format(playlist=self.serviceName))
        
        urlpath = os.path.join(self.profilePath, 'playlists', '{playlist}.url'.format(playlist=self.serviceName))
        if os.path.exists(urlpath):
            try:
                url = open(urlpath, 'r').read()
            except:
                url = open(urlpath, 'r', encoding='utf-8').read()
        else:
            url = url_setting

        if (int(tnow) >= int(timestamp) + int(tdel)) or not os.path.exists(filepath) or os.stat(filepath).st_size <= 0 or url != url_setting:
            content = self.requestUrl(upath)
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
            try:
                content = open(filepath, 'r').read()
            except:
                content = open(filepath, 'r', encoding='utf-8').read()

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
                self.log('downloadPlaylist Error %s' % getExceptionString())

            if (content is None or content == '') and (datetime.datetime.now() - start_time).seconds < 10:
                self.log('downloadPlaylist Failed, sleeping')
                time.sleep(0.5)

        return content


    def getPlaylistContent(self, path, urltype):
        content = ''
        try:
            self.log('getPlaylistContent opening playlist: %s, urltype: %s' % (path, urltype))
            if urltype == '0':
                tmpcontent = self.downloadPlaylist(path)

                if tmpcontent is None or tmpcontent == '':
                    raise Exception
            else:
                try:
                    try:
                        tmpcontent = open(path, 'r').read()
                    except:
                        tmpcontent = open(path, 'r', encoding='utf-8').read()
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
            self.log('getPlaylistContent opening Error %s, type: %s, url: %s' % (getExceptionString(), urltype, path) )
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

            regexReplaceList.append( re.compile('[^A-Za-z0-9+/:]+',                                                re.IGNORECASE) )
            regexReplaceList.append( re.compile('\sL\s',                                                           re.IGNORECASE) )
            regexReplaceList.append( re.compile('(\s|^)(Feed|Europe|SD|FULL|ADULT:|EXTRA:|VIP:|VIP|Audio|Backup|Multi|Sub|VIASAT:|XXX|XXX:|\d{1,2}\s*fps)(?=\s|$)',  re.IGNORECASE) )

            langReplaceList = list()
            regexRemoveList = list()

            #langReplaceList.append({ 'regex' : re.compile('(\s|^)(pl/en|Polska|Poland|PL:?)(?=\s|$)|^(PL:)', re.IGNORECASE), 'lang' : 'PL'})
            regexRemoveList.append( re.compile('(\s|^)(L\s*)?(AE:?|AF:?|AFG:?|AFR:?|AL:?|ALB:?|AO:?|AU:?|AR:?|ARB:?|ARG:?|AT:?|AZ:?|BE:?|BD:?|BF:?|BG:?|BIH:?|BJ:?|BR:?|CAR:?|CG:?|CH:?|CM:?|CN:?|CY:?|DZ:?|EE:?|EG:?|EN:?|ES:?|EXYU:?|FI:?|GA:?|GH:?|GN:?|GR:?|HN:?|HU:?|ID:?|IL:?|IN:?|IQ:?|IR:?|IS:?|JO:?|JP:?|KE:?|KRD:?|KOR:?|KU:?|KW:?|LAM:?|LATINO:?|LB:?|LE:?|LT:?|LU:?|LY:?|MA:?|MK:?|ML:?|MN:?|MT:?|MY:?|MX:?|NG:?|OM:?|PH:?|PK:?|PT:?|QA:?|RO:?|RO/HU:?|RS:?|RU:?|RUS:?|SA:?|SAC:?|SC:?|SG:?|SI:?|SL:?|SN:?|SO:?|SY:?|TD:?|TH:?|TN:?|TR:?|UA:?|VN:?|YE:?|ZA|24/7:?:?|S\d+\sE\d+|19\d\d|20\d\d|S\s*\d\d\s*E\s*\d\d)(?=\s|$)', re.IGNORECASE) )
            regexRemoveList.append( re.compile('(\s|^)(L\s*)?(Afghanistan:?|Africa:?|Albania:?|Algeria:?|America:?|Andorra:?|Angola:?|Antigua\sand\sBarbuda:?|Arab\sCountries:?|Argentina:?|Armenia:?|Asia:?|Australia:?|Austria:?|Azerbaijan:?|Bahamas:?|Bahrain:?|Bangladesh:?|Barbados:?|Belarus:?|Belize:?|Benin:?|Bhutan:?|Bolivia:?|Botswana:?|Brazil:?|Brunei:?|Bulgaria:?|Burkina\sFaso:?|Burma:?|Burundi:?|Cabo\sVerde:?|Cambodia:?|Cameroon:?|Canada:?|Central\sAfrican\sRepublic:?|Chad:?|Chile:?|China:?|Colombia:?|Comoros:?|Congo:?|Costa\sRica:?|Cote\sd\sIvoire:?|Cuba:?|Cyprus:?|Djibouti:?|Dominica:?|Dominican\sRepublic:?|Ecuador:?|Egypt:?|El\sSalvador:?|Equatorial\sGuinea:?|Eritrea:?|Estonia:?|Eswatini:?|Ethiopia:?|Fiji:?|Finland:?|Gabon:?|Gambia:?|Georgia:?|Ghana:?|Greece:?|Grenada:?|Guatemala:?|Guinea:?|Guinea-Bissau:?|Guyana:?|Haiti:?|Honduras:?|Hungary:?|Iceland:?|India:?|Indonesia:?|Iran:?|Iraq:?|Ireland:?|Israel:?|Jamaica:?|Japan:?|Jordan:?|Kazakhstan:?|Kenya:?|Kiribati:?|Korea:?|Kosovo:?|Kurdistan:?|Kuwait:?|Kyrgyzstan:?|Laos:?|Latvia:?|Lebanon:?|Lesotho:?|Liberia:?|Libya:?|Liechtenstein:?|Lithuania:?|Madagascar:?|Malawi:?|Malaysia:?|Maldives:?|Mali:?|Malta:?|Marshall\sIslands:?|Mauritania:?|Mauritius:?|Micronesia:?|Moldova:?|Monaco:?|Mongolia:?|Morocco:?|Mozambique:?|Myanmar:?|Namibia:?|Nauru:?|Nepal:?|New\sZealand:?|Nicaragua:?|Niger:?|Nigeria:?|North\sKorea:?|Oman:?|Pakistan:?|Palau:?|Palestine:?|Panama:?|Papua\sNew\sGuinea:?|Paraguay:?|Peru:?|Philippines:?|Portugal:?|Qatar:?|Romania:?|Russia:?|Rwanda:?|Saint\sKitts\sand\sNevis:?|Saint\sLucia:?|Saint\sVincent\sand\sthe\sGrenadines:?|Samoa:?|San\sMarino:?|Sao\sTome\sand\sPrincipe:?|Saudi\sArabia:?|Senegal:?|Seychelles:?|Sierra\sLeone:?|Singapore:?|Slovakia:?|Solomon\sIslands:?|Somalia:?|South\sAfrica:?|South\sKorea:?|South\sSudan:?|Spain:?|Sri\sLanka:?|Sudan:?|Suriname:?|Swaziland:?|Switzerland:?|Syria:?|Taiwan:?|Tajikistan:?|Tanzania:?|Thailand:?|Timor\sLeste:?|Togo:?|Tonga:?|Trinidad\sand\sTobago:?|Tunisia:?|Turkey:?|Turkmenistan:?|Tuvalu:?|Uganda:?|Ukraine:?|United\sArab\sEmirates:?|Uruguay:?|Uzbekistan:?|Vanuatu:?|Vatican\sCity:?|Venezuela:?|Vietnam:?|Viet\sNam:?|Yemen:?|Zambia:?|Zimbabwe)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_be') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(BE:?|NL:?|HEVC:?)(?=\s|$)|^(BE:|NL:)', re.IGNORECASE), 'lang' : 'BE'})
            else:
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(BE:?|NL:?|HEVC:?|Belgium:?|Netherland:?|Luxemburg:?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_cz') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(CZ:?)(?=\s|$)|^(CZ:)', re.IGNORECASE), 'lang' : 'CZ'})
            else:
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(CZ:?|Czech:?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_hr') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(CRO:?|HR:?|HRV:?|Yu:?)(?=\s|$)|^(CRO:|HR:|HRV:|Yu:)', re.IGNORECASE), 'lang' : 'HR'})
            else:
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(CRO:?|HR:?|HRV:?|Yu:?|Hrvatska:?|Slovenia:?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_dk') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(DK:?)(?=\s|$)|^(DK:)', re.IGNORECASE), 'lang' : 'DK'})
            else:
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(DK:?|Denmark:?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_uk') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(UK:?|ENG:?)(?=\s|$)|^(UK:|ENG:)', re.IGNORECASE), 'lang' : 'UK'})
            else:
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(UK:?|ENG:?|United\sKingdom:?|Great\sBritain:?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_fr') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(FR:?)(?=\s|$)|^(FR:)', re.IGNORECASE), 'lang' : 'FR'})
            else:
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(FR:?|France:?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_de') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(DE:?)(?=\s|$)|^(DE:)', re.IGNORECASE), 'lang' : 'DE'})
            else:
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(DE:?|Germany:?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_it') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(IT:?)(?=\s|$)|^(IT:)', re.IGNORECASE), 'lang' : 'IT'})
            else:
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(IT:?|Ital(y|ia):?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_pl') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(PL:?|pl/en|Polska|Poland)(?=\s|$)|^(PL:)', re.IGNORECASE), 'lang' : 'PL'})
            else:
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(PL:?|pl/en|Polska:?|Poland:?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_no') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(NO:?)(?=\s|$)|^(NO:)', re.IGNORECASE), 'lang' : 'NO'})
            else:
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(NO:?|Norway:?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_srb') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(BH:?|SRB:?|SLO:?|SR:?|Yu:?)(?=\s|$)|^(SRB:|SLO:|SR:|Yu:)', re.IGNORECASE), 'lang' : 'SRB'})
            else:
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(BH:?|SRB:?|SLO:?|SR:?|Yu:|Srbija:?|Crna\sGora:?|Macedonia:?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_se') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(SE:?|SW:?|Sweden:?)(?=\s|$)|^(SE:|SW:|Sweden:)', re.IGNORECASE), 'lang' : 'SE'})
            else:
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(SE:?|SW:?|Sweden:?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_us') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(Chicago:?|AM:?|CA:?|US:?|USA:?)(?=\s|$)|^(Chicago:?|AM:|CA:?|US:|USA:)', re.IGNORECASE), 'lang' : 'US'})
            else:
                regexRemoveList.append( re.compile('(\s|^)(L\s*)?(AM:?|CA:?|USA:?|US:?|(Latin\s)?America:?|United\sStates:?)(?=\s|$)', re.IGNORECASE) )

            if ADDON.getSetting('country_code_radio') == 'true':
                langReplaceList.append({ 'regex' : re.compile('(\s|^)(Radio:?)(?=\s|$)|^(Radio:)', re.IGNORECASE), 'lang' : 'Radio'})
            else:
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

            channelsArray = self.getPlaylistContent(self.url.strip(), self.source)

            if channelsArray is not None and channelsArray != "" and len(channelsArray) > 0:
                cleaned_playlist = cleanup_regex.sub('', channelsArray)
                
                for line in cleaned_playlist.splitlines():
                    stripLine = line.strip()

                    if '#EXTINF:' in stripLine:
                        tmpTitle = ''
                        title = ''
                        splitedLine = stripLine.split(',')

                        p = re.compile('^.*catchup-source=.*$', re.IGNORECASE)

                        if p.match(stripLine) and ADDON.getSetting('archive_support') == 'true':
                            catchup = re.compile('^.*catchup-source="(.*?)".*')
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
                            
                            title, match = regexHD.subn(' HD ', title, count=1)
                            if match > 0:
                                HDStream = True

                            title, match = regexUHD.subn(' UHD ', title, count=1)
                            if match > 0:
                                UHDStream = True

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
                                ccListInt = len(ccList)
                                
                                if any(ccExt not in title for ccExt in ccList):   
                                    try:
                                        if sys.version_info[0] > 2:
                                            groupList = re.findall('group-title=".*[^\w]({a}|{b}|{c})[^\w]?.*"'.format(a=langA, b=langB, c=langC), str(splitedLine[0]))
                                        else:
                                            groupList = re.findall('group-title=".*[^\w]({a}|{b}|{c})[^\w]?.*"'.format(a=langA, b=langB, c=langC), str(splitedLine[0].encode('utf-8')))

                                        if groupList:
                                            for item in range(ccListInt):
                                                if groupList[0] == langAList[item]:
                                                    subsLangA = {langAList[item]: ccList[item]}
                                                    cc = [subsLangA.get(item, item) for item in groupList]
                                                    ccCh = cc[0]

                                                elif groupList[0] == langBList[item]:         
                                                    subsLangB = {langBList[item]: ccList[item]}
                                                    cc = [subsLangB.get(item, item) for item in groupList]
                                                    ccCh = cc[0]

                                                elif groupList[0] == ccList[item]:         
                                                    subsLangC = {ccList[item]: ccList[item]}
                                                    cc = [subsLangC.get(item, item) for item in groupList]
                                                    ccCh = cc[0]

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

                            fd = re.compile('.*(timeshift=|catchup-days=).*')

                            if fd.match(splitedLine[0]) and ADDON.getSetting('archive_support') == 'true':
                                pdays = re.compile('.*(timeshift=|catchup-days=)"(.*?)".*')
                                
                                days = pdays.search(splitedLine[0]).group(2)
                            else:
                                days = '0'

                            fc = re.compile('.*(timeshift|catchup).*')

                            if fc.match(splitedLine[0]) and ADDON.getSetting('archive_support') == 'true':
                                channelCid = str(nextFreeCid) + '_TS' + '_' + days
                            else:
                                channelCid = str(nextFreeCid)

                            if UHDStream:
                                channelCid = channelCid + '_UHD'
                                uhdList.append(TvCid(channelCid, title, title, stripLine, catchupLine))
                            elif HDStream:
                                channelCid = channelCid + '_HD'
                                hdList.append(TvCid(channelCid, title, title, stripLine, catchupLine))
                            else:
                                sdList.append(TvCid(channelCid, title, title, stripLine, catchupLine))

                            
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

    def getChannelStream(self, chann):
        try:
            if self.stopPlaybackOnStart and xbmc.Player().isPlaying():
                xbmc.Player().stop()
                xbmc.sleep(500)
            self.log('getChannelStream: found matching channel: cid {}, name {}, stream {}'.format(chann.cid, chann.name, chann.strm))

            UA = ADDON.getSetting('{}_user_agent'.format(self.serviceName))

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0',
                'Keep-Alive': 'timeout=20',
                'ContentType': 'application/json',
                'Connection': 'Keep-Alive'
            }

            timeout = int(ADDON.getSetting('max_wait_for_playback')) / 10
            
            try:
                if UA and not '_TS' in chann.cid:         
                    headers.update({'User-Agent': UA})

                    response = scraper.get(chann.strm, headers=headers, allow_redirects=False, timeout=timeout)
                    chann.strm = response.headers.get('Location', None) if 'Location' in response.headers else chann.strm

                else:
                    response = scraper.get(chann.strm, headers=headers, allow_redirects=False, timeout=timeout)
                    chann.strm = response.url

            except HTTPError as e:
                #deb('getChannelStream HTTPError: {}'.format(str(e)))
                chann.strm

            except ConnectionError as e:
                #deb('getChannelStream ConnectionError: {}'.format(str(e)))
                chann.strm

            except Timeout as e:
                #deb('getChannelStream Timeout: {}'.format(str(e))) 
                chann.strm

            except RequestException as e:
                #deb('getChannelStream RequestException: {}'.format(str(e))) 
                chann.strm

            return chann

        except Exception as ex:
            self.log('getChannelStream Error {}'.format(getExceptionString()))
        return None

    def log(self, message):
        if self.thread is not None and self.thread.is_alive() and self.forcePrintintingLog == False:
            self.traceList.append(self.__class__.__name__ + '_' + self.instance_number + ' ' + message)
        else:
            deb(self.__class__.__name__ + '_' + self.instance_number + ' ' + message)