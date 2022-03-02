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
    PY3 = True
else:
    PY3 = False

import requests
import urllib3

if PY3:
    from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
    import urllib.request as Request
    from urllib.error import HTTPError, URLError
else:
    from requests import HTTPError, ConnectionError, Timeout, RequestException
    import urllib2 as Request
    from urllib2 import HTTPError, URLError

try:
    from urllib.parse import urlencode, quote_plus, quote, unquote
except ImportError:
    from urllib import urlencode, quote_plus, quote, unquote

import copy, re
import xbmc, xbmcgui, xbmcvfs, xbmcaddon
from xml.etree import ElementTree
from strings import *
from groups import *
from serviceLib import *
import cloudscraper 

from contextlib import contextmanager
from unidecode import unidecode
from collections import OrderedDict

import codecs

sess = cloudscraper.create_scraper()
scraper = cloudscraper.CloudScraper()

UA = xbmc.getUserAgent()

CC_DICT = ccDict()

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

        if int(instance_number) <= int(ADDON.getSetting('nr_of_playlists')):
            self.serviceEnabled  = ADDON.getSetting('{}_enabled'.format(self.serviceName))
        else:
            self.serviceEnabled = 'false'

        if self.source == '0':
            self.url = ADDON.getSetting('{}_url'.format(self.serviceName))
        else:
            if PY3:
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

        if ADDON.getSetting('{}_refr'.format(self.serviceName)) == 'true':
            self.refr = True
        else:
            self.refr = False

        if ADDON.getSetting('archive_support') == 'true':
            self.catchup = True
        else:
            self.catchup = False

        if ADDON.getSetting('tvg_id') == 'true':
            self.tvg = True
        else:
            self.tvg = False

        if ADDON.getSetting('show_group_channels') == 'true':
            self.filtered = True
        else:
            self.filtered = False

        if ADDON.getSetting('VOD_EPG') == 'true':
            self.vod = True
        else:
            self.vod = False

        if ADDON.getSetting('XXX_EPG') == 'true':
            self.xxx = True
        else:
            self.xxx = False

    def requestUrl(self, path):
        headers = { 'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36' }
        headers['Keep-Alive'] = 'timeout=5'
        headers['Connection'] = 'Keep-Alive'
        headers['ContentType'] = 'application/x-www-form-urlencoded'
        headers['Accept-Encoding'] = 'gzip'

        try:
            content = requests.get(path, headers=headers, allow_redirects=False, verify=False, timeout=5).content.decode('utf-8')

        except Exception as ex:
            deb('requestUrl urlib3 Exception: {}'.format(ex))
            try:
                content = scraper.get(path, headers=headers, allow_redirects=False, verify=False, timeout=5).content.decode('utf-8')

            except Exception as ex:
                deb('requestUrl requests Exception: {}'.format(ex))
                try:
                    content = self.sl.getJsonFromExtendedAPI(path).decode('utf-8')
                except Exception as ex:
                    deb('requestUrl json Exception: {}'.format(ex))
                    content = ''
        
        return content.splitlines()

    def cachePlaylist(self, upath):
        n = datetime.datetime.now()
        d = datetime.timedelta(days=int(ADDON.getSetting('{playlist}_refr_days'.format(playlist=self.serviceName))))

        if PY3:
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
            if PY3:
                with open(urlpath, 'r', encoding='utf-8') as f:
                    url = [line.strip() for line in f][0]
            else:
                with codecs.open(urlpath, 'r', encoding='utf-8') as f:
                    url = [line.strip() for line in f][0]

        else:
            url = url_setting

        cachedate = int(timestamp) + int(tdel)

        if int(tnow) >= int(cachedate) or (not os.path.exists(filepath) or os.stat(filepath).st_size <= 0 or url != url_setting):
            deb('[UPD] Cache playlist: Write, expiration date: {}'.format(datetime.datetime.fromtimestamp(int(cachedate))))
            content = self.requestUrl(upath)
            if content:
                for f in os.listdir(path):
                    if not f.endswith(".m3u") or not f.endswith(".url"):
                        continue
                    filename = os.path.basename(filepath)
                    if self.serviceName in filename:
                        os.remove(os.path.join(path, f))

                if PY3:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write("\n".join(content))
                else:
                    with codecs.open(filepath, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(content))

                if PY3:
                    with open(urlpath, 'w', encoding='utf-8') as f2:
                        f2.write(url_setting)
                else:
                    with codecs.open(urlpath, 'w', encoding='utf-8') as f2:
                        f2.write(url_setting)

        else:
            deb('[UPD] Cache playlist: Read')
            try:  
                if PY3:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = [line.strip() for line in f]
                else:
                    try:
                        with codecs.open(filepath, 'r', encoding='utf-8') as f:
                            content = [line.strip() for line in f]
                    except:
                        with codecs.open(filepath.decode('utf-8'), 'r', encoding='utf-8') as f:
                            content = [line.strip() for line in f]
                
                if not content:
                    raise Exception

            except:
                self.log('getPlaylistContent opening normally Error %s, type: %s, url: %s' % (getExceptionString(), urlpath, path) )
                self.log('getPlaylistContent trying to open file using xbmcvfs')
                lf = xbmcvfs.File(filepath)
                content = lf.read().splitlines()
                lf.close()
                if not content:
                    raise Exception

        return content

    def downloadPlaylist(self, path):
        content = None
        start_time = datetime.datetime.now()

        while not content and (datetime.datetime.now() - start_time).seconds < 10:
            try:
                if self.refr:
                    content = self.cachePlaylist(path)
                else:
                    content = self.requestUrl(path)

            except Exception as ex:
                self.log('downloadPlaylist Error {}'.format(getExceptionString()))

            if not content and (datetime.datetime.now() - start_time).seconds < 10:
                self.log('downloadPlaylist Failed, sleeping')
                time.sleep(0.5)

        return content


    def getPlaylistContent(self, path, urltype):
        content = ''

        try:
            self.log('getPlaylistContent opening playlist: %s, urltype: %s' % (path, urltype))
            if urltype == '0':
                tmpcontent = self.downloadPlaylist(path)

                if not tmpcontent:
                    raise Exception
            else:
                try:
                    if PY3:
                        with open(path, 'r', encoding='utf-8') as f:
                            tmpcontent = [line.strip() for line in f]
                    else:
                        try:
                            with codecs.open(path, 'r', encoding='utf-8') as f:
                                tmpcontent = [line.strip() for line in f]
                        except:
                            with codecs.open(path.decode('utf-8'), 'r', encoding='utf-8') as f:
                                tmpcontent = [line.strip() for line in f]
                    
                    if not tmpcontent:
                        raise Exception
                        
                except:
                    self.log('getPlaylistContent opening normally Error %s, type: %s, url: %s' % (getExceptionString(), urltype, path) )
                    self.log('getPlaylistContent trying to open file using xbmcvfs')
                    lf = xbmcvfs.File(path)
                    tmpcontent = lf.read().splitlines()
                    lf.close()
                    if not tmpcontent:
                        raise Exception
                
            content = tmpcontent

        except:
            self.log('getPlaylistContent opening Error {}, type: {}, url: {}'.format(getExceptionString(), urltype, path) )
            if PY3:
                xbmcgui.Dialog().notification(strings(59905), strings(57049) + ' ' + self.serviceName + ' (' + self.getDisplayName() + ') ' + strings(57050), time=10000, sound=False)
            else:
                xbmcgui.Dialog().notification(strings(59905).encode('utf-8'), strings(57049).encode('utf-8') + ' ' + self.serviceName + ' (' + self.getDisplayName() + ') ' + strings(57050).encode('utf-8'), time=10000, sound=False)
        return content

    def getChannelList(self, silent):
        result = []
        try:
            regexReplaceList = []

            ccList = []
            a3List = []
            langList = []
            nativeList = []
            dotList = []

            sdList = []
            hdList = []
            uhdList = []

            cleanup_regex = re.compile("\[COLOR\s*\w*\]|\[/COLOR\]|\[B\]|\[/B\]|\[I\]|\[/I\]|^\s*|\s*$", re.IGNORECASE)

            #regexReplaceList.append( re.compile('[^A-Za-z0-9+/:]+', re.IGNORECASE) )
            regexReplaceList.append( re.compile('[^A-Za-zÀ-ȕ0-9+\/:\.]+', re.IGNORECASE) )

            regexReplaceList.append( re.compile('\sL\s', re.IGNORECASE) )
            regexReplaceList.append( re.compile('(\s|^)(FEED|FPS60|EUROPE|NORDIC|SCANDINAVIA|ADULT:|EXTRA:|VIP:|VIP|AUDIO|L1|B|BACKUP|MULTI|SUB|SUBTITLE(S)?|NAPISY|VIASAT:|XXX|XXX:|\d{1,2}\s*FPS|LIVE\s*DURING\s*EVENTS\s*ONLY)(?=\s|$)', re.IGNORECASE) )
            regexReplaceList.append( re.compile('(\s|^)(FULL|SD|LQ|HQ|RAW|LOW|HIGH|QUALITY)(?=\s|$)', re.IGNORECASE) )

            defReplaceList = []
            langReplaceList = []
            prefixList = []
            regexRemoveList = []
            regexAddList = []

            regexRemoveList.append( re.compile('(\s|\W|^)(L\s*)?(24\/7:?:?|19\d\d|20\d\d|S\s*\d{1,3}\s*E\s*\d{1,4})(?=\s|$)', re.IGNORECASE) )

            settings_file = os.path.join(self.profilePath, 'settings.xml')

            with open(settings_file, 'rb') as f:
                tree = ElementTree.parse(f)
            root = tree.getroot()

            cc_settings = [i.attrib['id'].replace('country_code_', '') for i in root if 'country_code_' in i.attrib['id'] and i.text == 'true']

            APPEND = ADDON.getSetting('{}_append_country_code'.format(self.serviceName))

            PATTERN = -1

            if ADDON.getSetting('{}_pattern'.format(self.serviceName)) == '0':
                PATTERN = 0

            elif ADDON.getSetting('{}_pattern'.format(self.serviceName)) == '1':
                PATTERN = 1

            elif ADDON.getSetting('{}_pattern'.format(self.serviceName)) == '2':
                PATTERN = 2

            elif ADDON.getSetting('{}_pattern'.format(self.serviceName)) == '3':
                PATTERN = 3

            elif ADDON.getSetting('{}_pattern'.format(self.serviceName)) == '4':
                PATTERN = 4

            elif ADDON.getSetting('{}_pattern'.format(self.serviceName)) == '5':
                PATTERN = 5

            for cc, value in CC_DICT.items():
                cc_pattern = cc.upper()
                cc_pattern_regex = cc_pattern

                if PATTERN == 0:
                    cc_pattern_regex = cc.upper() + ':?|' + value['alpha-3'] + ':?|' + re.escape('.' + cc.lower()) + ':?|' + value['language']

                # Alpha-2
                elif PATTERN == 1:
                    cc_pattern = cc.upper()

                # Alpha-3
                elif PATTERN == 2:
                    cc_pattern = value['alpha-3']
                    
                # ccTLD
                elif PATTERN == 3:
                    cc_pattern = '.' + cc.lower()
                    cc_pattern_regex = re.escape(cc_pattern)

                # Lang
                elif PATTERN == 4:
                    cc_pattern = value['language']

                # Remove all
                elif PATTERN == 5:
                    cc_pattern_regex = cc.upper() + ':?|' + value['alpha-3'] + ':?|' + re.escape('.' + cc.lower()) + ':?|' + value['language']

                if cc in cc_settings:
                    alpha_1 = value['native']
                    alpha_2 = value['language']
                    alpha_3 = value['alpha-3']
                    alpha_4 = value.get('alpha-4', value['alpha-3'])

                    ccList.append(cc.upper())
                    a3List.append(alpha_3.upper())
                    langList.append(alpha_2)
                    nativeList.append(alpha_1)
                    dotList.append('.' + cc.lower())

                    langA = '|'.join(ccList)
                    langB = '|'.join(a3List)
                    langC = '|'.join(langList)
                    langD = '|'.join(nativeList)
                    langE = '|'.join(dotList)

                    try:
                        langReplaceList.append({ 'regex' : re.compile('(\s|^)(\s*'+cc.upper()+'$|'+alpha_4+':?|'+alpha_3+':?|'+alpha_2+':?|'+alpha_1+':?)(?=\s|$)|^('+alpha_4+':|'+alpha_3+':|'+alpha_2+':|'+alpha_1+':)', re.IGNORECASE), 'lang' : cc_pattern})
                    except:
                        langReplaceList.append({ 'regex' : re.compile('(\s|^)(\s*'+cc.upper()+'$|'+alpha_4+':?|'+alpha_3+':?|'+alpha_2+':?|'+alpha_1.encode('utf-8')+':?)(?=\s|$)|^('+alpha_4+':|'+alpha_3+':|'+alpha_2+':|'+alpha_1.encode('utf-8')+':)', re.IGNORECASE), 'lang' : cc_pattern})

                    langReplaceList.append({ 'regex' : re.compile('(\s|^)('+cc.upper()+':?)(?=\s|$)|^('+cc.upper()+':?)'), 'lang' : cc_pattern})
                    prefixList.append(cc_pattern_regex + ':?')

                elif not self.filtered:
                    alpha_1 = value['native']
                    alpha_2 = value['language']
                    alpha_3 = value['alpha-3']
                    alpha_4 = value.get('alpha-4', value['alpha-3'])

                    ccList.append(cc.upper())
                    a3List.append(alpha_3.upper())
                    langList.append(alpha_2)
                    nativeList.append(alpha_1)
                    dotList.append('.' + cc.lower())

                    langA = '|'.join(ccList)
                    langB = '|'.join(a3List)
                    langC = '|'.join(langList)
                    langD = '|'.join(nativeList)
                    langE = '|'.join(dotList)

            if not prefixList:
                prefixList.append(' ')

            prefix = '|'.join(map(str, prefixList))
            if PATTERN == 0:
                regexAddList.append( re.compile('(\S|\s|^)(L\s*)?({prefix})(?=\S|\s|$)'.format(prefix=prefix)) )
            elif PATTERN == 3:
                regexAddList.append( re.compile('(\S|^)(L\s*)?({prefix})(?=\S|$)'.format(prefix=prefix)) )
            else:
                regexAddList.append( re.compile('(\s|^)(L\s*)?({prefix})(?=\s|$)'.format(prefix=prefix)) )

            regexHD = re.compile('(\s|^)(720p|720|FHD|1080p|1080|HD\sHD|HD)(?=\s|$)', re.IGNORECASE)
            regexUHD = re.compile('(\s|^)(4K|UHD)(?=\s|$)', re.IGNORECASE)

            defReplaceList.append({ 'regex' : re.compile('(\s|^)(SD:?|480:?|480p:?|576:?|576i:?|576p:?)(?=\s|$)|^(SD:?|480:?|480p:?|576:?|576i:?|576p:?)'), 'def' : 'SD'})
            if 'SD' not in defReplaceList:
                defReplaceList.append({ 'regex' : re.compile('(\s|^)(HD:?|720:?|720p:?|1080:?|1080i:?|1080p:?)(?=\s|$)|^(HD:?|720:?|720p:?|1080:?|1080i:?|1080p:?)'), 'def' : 'HD'})
            if 'HD' not in defReplaceList:
                defReplaceList.append({ 'regex' : re.compile('(\s|^)(UHD:?|UHDTV:?|4K:?|2160p:?)(?=\s|$)|^(UHD:?|UHDTV:?|4K:?|2160p:?)'), 'def' : 'UHD'})

            regex_chann_name   =     re.compile('tvg-id="[^"]*"', re.IGNORECASE)

            if self.vod:
                regexCorrectStream = re.compile('^(plugin|http|rtmp)(?!.*?[.]((\.)(mp4|mkv|avi|mov|wma)))', re.IGNORECASE)
                regexRemoveList.append( re.compile('(\s|^)?(L\s*)?((?i)Vod|VOD|On\sDemand)(?=\s|$)', re.IGNORECASE) )
            else:
                regexCorrectStream = re.compile('^plugin|http|^rtmp', re.IGNORECASE)

            if self.xxx:
                regexRemoveList.append( re.compile('(\s|^)?(L\s*)?((?i)Adult|XXX)(?=\s|$)', re.IGNORECASE) )

            title = None
            tvg_title = None
            
            nextFreeCid = 0
            
            try:
                channelsArray = self.getPlaylistContent(self.url.strip(), self.source)
            except Exception as ex:
                deb('channelsArray Exception: {}'.format(ex))
                channelsArray = self.getPlaylistContent(self.url.decode('utf-8').strip(), self.source)

            self.log('\n\n')
            self.log('[UPD] Downloading a list of available channels for {}'.format(self.serviceName))
            self.log('-------------------------------------------------------------------------------------')
            self.log('[UPD]     %-40s %-12s %-35s' % ( '-ORIG NAME-', '-CID-', '-STRM-'))

            if channelsArray and len(channelsArray) > 0:
                for line in channelsArray:
                    line = cleanup_regex.sub('', line)
                    stripLine = line.strip()

                    if '#EXTINF:' in stripLine:
                        tmpTitle = ''
                        name = ''
                        title = ''
                        tvg_title = ''

                        splitedLine = stripLine.split(',')

                        catchup_regex = re.compile('^.*catchup-source="http[s]?.*$', re.IGNORECASE)

                        if catchup_regex.match(stripLine) and self.catchup:
                            catchup_source_regex = re.compile('catchup-source="(.*?)"')
                            
                            r = catchup_source_regex.search(stripLine)
                            catchupLine = r.group(1) if r else ''

                        else:
                            catchupLine = ''

                        if len(splitedLine) > 1:
                            try:
                                tmpTitle = unidecode(splitedLine[len(splitedLine) - 1].strip())
                            except:
                                tmpTitle = unidecode(splitedLine[len(splitedLine) - 1].strip().decode('utf-8'))

                        tvg_id = False

                        match = regex_chann_name.findall(stripLine)
                        if len(match) > 0 and self.tvg:
                            tvg_title = match[0].replace("tvg-id=","").replace('"','').strip()
                            tvg_id = True


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

                            title = ' '.join(OrderedDict((w,w) for w in title.split()).keys())

                            name = title

                            if PATTERN == 0:
                                lang = langA + '|' + langB + '|' + langC + '|' + langD + '|' + langE 
                                
                            elif PATTERN == 1:
                                lang = langA
                                
                            elif PATTERN == 2:
                                lang = langB

                            elif PATTERN == 3:
                                lang = langE

                            elif PATTERN == 4:
                                lang = langC + '|' + langD

                            else:
                                lang = ''

                            if PATTERN <= 2:
                                try:
                                    regex_match = re.compile('(^|(\s))(L\s*)?((?i){lang})((:|\s)|$)'.format(lang=lang.upper()))
                                except:
                                    regex_match = re.compile('(^|(\s))(L\s*)?((?i){lang})((:|\s)|$)'.format(lang=lang.upper().encode('utf-8')))

                            elif PATTERN == 3:
                                try:
                                    regex_match = re.compile('((?i){lang})'.format(lang=lang.lower()))
                                except:
                                    regex_match = re.compile('((?i){lang})'.format(lang=lang.lower().encode('utf-8')))
                            
                            elif PATTERN > 4: 
                                try:
                                    regex_match = re.compile('(^|(\s))(L\s*)?({lang})((:|\s)|$)'.format(lang=lang), re.IGNORECASE)
                                except:
                                    regex_match = re.compile('(^|(\s))(L\s*)?({lang})((:|\s)|$)'.format(lang=lang.encode('utf-8')), re.IGNORECASE)

                            
                            if APPEND != '' and self.serviceEnabled == 'true':
                                match = regex_match.match(title)
                                if match is None:
                                    title = title + ' ' + APPEND

                            elif self.serviceEnabled == 'true':
                                match = regex_match.match(title)
                                if match is None:
                                    ccListInt = len(ccList)

                                    non_escaped = langA + '|' + langB + '|' + langC + '|' + langD
                                    escaped = re.sub(r'\.', r'\\.', langE)

                                    try:
                                        pattern = re.compile('((?:^|[^a-zA-Z])({n})(?:[^a-zA-Z]|$)|({e}))'.format(n=non_escaped, e=escaped))
                                    except:
                                        pattern = re.compile('((?:^|[^a-zA-Z])({n})(?:[^a-zA-Z]|$)|({e}))'.format(n=non_escaped.encode('utf-8'), e=escaped))

                                    if PY3:
                                        r = pattern.search(str(splitedLine[0]))
                                        group = r.group(1).strip() if r else ''

                                    else:
                                        r = pattern.search(str(splitedLine[0].encode('utf-8')))
                                        group = r.group(1).strip() if r else ''

                                    if group:
                                        ccCh = ''
                                        for item in range(ccListInt):
                                            if group == ccList[item].upper():
                                                subsLangA = {ccList[item]: ccList[item]}
                                                ccCh = ccList[subsLangA.get(item, item)]

                                            elif group == a3List[item].upper():  
                                                subsLangB = {a3List[item]: ccList[item]}
                                                ccCh = ccList[subsLangB.get(item, item)]
                                            
                                            elif group.upper() == langList[item].upper():
                                                subsLangC = {langList[item]: ccList[item]}
                                                ccCh = ccList[subsLangC.get(item, item)]

                                            elif group.upper() == nativeList[item].upper():
                                                subsLangD = {nativeList[item]: ccList[item]}
                                                ccCh = ccList[subsLangD.get(item, item)]

                                            elif group.lower() == dotList[item]:
                                                subsLangE = {dotList[item]: ccList[item]}
                                                ccCh = ccList[subsLangE.get(item, item)]

                                        if ccCh:
                                            string = ' ' + ccCh.upper()
                                            title = re.sub('$', string, title)

                            for regexRemove in regexRemoveList:
                                if( regexRemove.findall(title) ):
                                    title = ''
                                if tvg_id:
                                    if( regexRemove.findall(tvg_title) ):
                                        tvg_title = ''

                            for defReplaceMap in defReplaceList:
                                title, match = defReplaceMap['regex'].subn('', title)
                                if match > 0:
                                    title += ' ' + defReplaceMap['def']
                                    title = ' '.join(OrderedDict((w,w) for w in title.split()).keys())
                                    if PATTERN == 5:
                                        title = re.sub(defReplaceMap['def'], '', title)

                            for langReplaceMap in langReplaceList:
                                title, match = langReplaceMap['regex'].subn('', title)
                                if match > 0:
                                    if PATTERN == 3:
                                        title += '' + langReplaceMap['lang']
                                    elif PATTERN == 5:
                                        title = re.sub(langReplaceMap['lang'], '', title)
                                    else:
                                        title += ' ' + langReplaceMap['lang']

                            if self.filtered and PATTERN != 5:
                                for regexAdd in regexAddList:
                                    if not ( regexAdd.findall(title) ):
                                        title = '' 
                                    if tvg_id:
                                        if not ( regexAdd.findall(tvg_title) ):
                                            tvg_title = ''       

                            title = re.sub('  ', ' ', title).strip()

                            if PATTERN == 0 and self.filtered and title != '':
                                title = name

                            if tvg_id:
                                if tvg_title == title:
                                    tvg_title = ''              

                    elif (title is not None or tvg_title is not None) and regexCorrectStream.match(stripLine):
                        removeStream = True
                        if not self.vod: 
                            regexRemoveStream = re.compile('^(?!.*(\.)(mkv|avi|mov|wma)).*$')
                            try:
                                match = regexRemoveStream.match(stripLine)
                            except:
                                match = True

                        if (title != '' or tvg_title != '') and match:
                            channelCid = ''

                            catchupDaysList = ['catchup-days=', 'timeshift=']

                            if any(x in splitedLine[0] for x in catchupDaysList) and self.catchup:
                                pdays = re.compile('.*(timeshift=|catchup-days=)"(.*?)".*')
                                
                                days = pdays.search(splitedLine[0]).group(2)
                            else:
                                days = '1'

                            catchupList = ['catchup', 'timeshift']

                            if any(x in splitedLine[0] for x in catchupList) and self.catchup:
                                channelCid = str(nextFreeCid) + '_AR' + '_' + days
                            else:
                                channelCid = str(nextFreeCid)

                            if UHDStream:
                                channelCid = channelCid + '_UHD'
                                uhdList.append(TvCid(cid=channelCid, name=name, title=title, strm=stripLine, catchup=catchupLine))
                                if tvg_id and tvg_title != '':
                                    uhdList.append(TvCid(cid=channelCid, name=tvg_title, title=tvg_title, strm=stripLine, catchup=catchupLine))
                            elif HDStream:
                                channelCid = channelCid + '_HD'
                                hdList.append(TvCid(cid=channelCid, name=name, title=title, strm=stripLine, catchup=catchupLine))
                                if tvg_id and tvg_title != '':
                                    hdList.append(TvCid(cid=channelCid, name=tvg_title, title=tvg_title, strm=stripLine, catchup=catchupLine))
                            else:
                                sdList.append(TvCid(cid=channelCid, name=name, title=title, strm=stripLine, catchup=catchupLine))
                                if tvg_id and tvg_title != '':
                                    sdList.append(TvCid(cid=channelCid, name=tvg_title, title=tvg_title, strm=stripLine, catchup=catchupLine))

                            self.log('[UPD]     %-40s %-12s %-35s' % (title, channelCid, stripLine))
                            if tvg_id and tvg_title != '':
                                self.log('[TVG]     %-40s %-12s %-35s' % (tvg_title, channelCid, stripLine))
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

            self.log('-------------------------------------------------------------------------------------')

        except Exception as ex:
            self.log('getChannelList Error %s' % getExceptionString())
        return result

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