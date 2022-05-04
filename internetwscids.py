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

#   Some implementations are modified and taken from "plugin.video.internetws" - thank you very much mbebe!

import sys

if sys.version_info[0] > 2:
    PY3 = True
else:
    PY3 = False

try:
    from urllib.parse import parse_qsl, quote, urlencode
    import http.cookiejar as cookielib
    from cmf3 import parseDOM
    from cmf3 import replaceHTMLCodes
except ImportError:
    from urlparse import parse_qsl
    import cookielib
    from urllib import quote, urlencode
    from cmf2 import parseDOM
    from cmf2 import replaceHTMLCodes

import requests
import xbmcgui, xbmcvfs
import xbmcplugin
import xbmcaddon
import xbmc
import base64
import string

import json

import xml.etree.ElementTree as ET

import internetwskb as kb
from strings import *
from serviceLib import *

serviceName         = 'Internetowa TV'
internetwsUrl       = 'https://internetowa.tv/'

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

if not os.path.exists(profilePath):
        os.makedirs(profilePath)
COOKIEFILE = os.path.join(profilePath,'intws.cookie')

sess = requests.Session()
sess.cookies = cookielib.LWPCookieJar(COOKIEFILE)

UA = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0'

class InternetwsUpdater(baseServiceUpdater):
    def __init__(self):
        self.serviceName        = serviceName
        self.localMapFile       = 'internetwsmap.xml'
        baseServiceUpdater.__init__(self)
        self.serviceEnabled     = ADDON.getSetting('internetws_enabled')
        self.login              = ADDON.getSetting('internetws_username').strip()
        self.password           = ADDON.getSetting('internetws_password').strip()
        self.servicePriority    = int(ADDON.getSetting('priority_internetws'))
        self.url                = internetwsUrl
        self.addDuplicatesToList = True

    def loginService(self):
        try:       
            username = self.login
            password = self.password 
            lastl = ADDON.getSetting('internetws_username')
            lastp = ADDON.getSetting('internetws_password')
            
            if username and password:
                sess.headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:61.0) Gecko/20100101 Firefox/66.0',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
                    'Referer': 'https://internetowa.tv/logowanie/',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',}  
                if lastl == username and lastp == password:
                    if os.path.isfile(COOKIEFILE):
                        sess.cookies.load()
                else:
                    sess.cookies.clear()
                html = sess.get('https://internetowa.tv/logowanie/', headers=sess.headers, cookies=sess.cookies)#.content
                if PY3:     
                    html_content = (html.content).decode(encoding='utf-8', errors='strict')
                else:
                    html_content = html.content
                captcha = re.search('https://internetowa.tv/captcha/',html_content)
                if captcha:
                    headers = {
                        'Host': 'internetowa.tv',
                        'user-agent': UA,
                        'accept': 'image/webp,*/*',
                        'accept-language': 'pl,en-US;q=0.7,en;q=0.3',
                        'referer': 'https://internetowa.tv/logowanie/',
                        'dnt': '1',
                        'te': 'trailers',
                    }
                    
                    response = sess.get('https://internetowa.tv/captcha/', cookies=html.cookies, headers=headers, verify=False)

                    search_term = kb.Keyboard(response.content)
                    data = {'email': username,'password': password,'captcha':search_term}
                else:
                    data = {'email': username,'password': password}
                response = sess.post('https://internetowa.tv/logowanie/#', headers=sess.headers, data=data, allow_redirects=False)

                if response.cookies.get('login') is not None:
                    sess.cookies.save()   
                    ADDON.setSetting("lastl", username)
                    ADDON.setSetting("lastp", password)
                #if os.path.isfile(COOKIEFILE):
                    sess.cookies.load()        
                #sess.cookies.load()
                html = sess.get('https://internetowa.tv/konto/',cookies=sess.cookies).content
                if PY3:
                    html = html.decode(encoding='utf-8', errors='strict')
                premium = re.findall('Konto premium, wa.+?ne do (.+?). Masz', html)

                free = re.findall('Brak konta premium', html)
                
                if premium:
                    info = premium[0]                          
                    return True
                elif free:
                    return True
                else:
                    self.log('Error when trying to login in internetowa.ws!, result: %s' % str(response))
                    self.loginErrorMessage()
                    sess.cookies.clear()
                    sess.cookies.save()
                    return False              
            else:
                self.log('Error when trying to login in internetowa.ws!, result: %s' % str(response))
                self.loginErrorMessage()
                sess.cookies.clear()
                sess.cookies.save()
                return False 

        except:
            self.log('Exception while trying to log in: %s' % getExceptionString())
            self.connErrorMessage()
        return False

    def getChannelList(self, silent):
        result = list()

        if not self.loginService():
            return result

        self.log('\n\n')
        self.log('[UPD] Pobieram liste dostepnych kanalow %s z %s' % (self.serviceName, self.url))
        self.log('[UPD] -------------------------------------------------------------------------------------')
        self.log('[UPD] %-10s %-35s %-15s %-20s %-35s' % ( '-CID-', '-NAME-', '-GEOBLOCK-', '-ACCESS STATUS-', '-IMG-'))
        
        try:
            sess.cookies.load() 
            html = sess.get('https://internetowa.tv/', cookies=sess.cookies).text        
            parse_result = parseDOM(html,'div', attrs={'id': "allhome"})[0] 

            items = parseDOM(parse_result,'div', attrs={'class': "channelb"})#[0] 

            html = sess.get('https://internetowa.tv/program-tv/').content
            if PY3:     
                html = html.decode(encoding='utf-8', errors='strict')
            parse_result = parseDOM(html,'div', attrs={'id': "epgBig"})[0] 
            subset = parseDOM(result,'tr')        
            for item in items:
                cid = parseDOM(item, 'a', ret='href')[0]
                name = parseDOM(item, 'a', ret='title')[0]
                title = parseDOM(item, 'a', ret='title')[0] + ' PL'
                img = parseDOM(item, 'img', ret='src')[0]

                program = TvCid(cid=cid, name=name, title=title, img=img)
                result.append(program)


            if len(result) <= 0:
                self.log('Error while parsing service %s, returned data is: %s' % (self.serviceName, str(html)))
                self.loginErrorMessage()

        except:
            self.log('getChannelList exception: %s' % getExceptionString())
        return result

    def getChannelStream(self, chann):
        data = None

        head = {
            'User-Agent': UA,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
            'Connection': 'keep-alive',
            'Referer': 'https://internetowa.tv/',
            'Upgrade-Insecure-Requests': '1',
            'TE': 'Trailers',
        }

        if 'm3u8' in chann.cid:
            stream_url = chann.cid
            hea = '&'.join(['%s=%s' % (name, value) for (name, value) in head.items()])
            data = stream_url
        else:
            try:
                if os.path.isfile(COOKIEFILE):
                    sess.cookies.load()
                html = sess.get(chann.cid, headers=head, verify=False).content
                if PY3:    
                    html = html.decode(encoding='utf-8', errors='strict')

                hlsToken = re.findall("""hlsToken\s*=\s*['"](.+?)['"]""",html)
                chromecastUrl = re.findall("""chromecastUrl\s*=\s*['"](.+?)['"]""",html)
                if chromecastUrl and hlsToken:
                    stream_url = chromecastUrl[0]+urllib.quote(hlsToken[0])#+'|Referer='+urllib.quote(chann.cid)
                    head.update({'Referer': chann.cid})
                    hea = '&'.join(['%s=%s' % (name, value) for (name, value) in head.items()])
                    html2 = sess.get(stream_url, headers=head, verify=False).content
                    if PY3:     
                        html2 = html2.decode(encoding='utf-8', errors='strict')

                    if 'error' in html2:
                        trick = re.findall('vid1.src([^<]+)<',html)
                        if trick:
                            stream_url = re.findall("""src: ['"]([^'"]+)['"]""",trick[0].replace("\'",'"'))[0]
                            band = sess.get(stream_url, headers=head, verify=False).content   
                            band = band.decode(encoding='utf-8', errors='strict')
                            stream_url = re.findall("(http.+?)\\r", band, re.MULTILINE)[0]
                            head.update({'Referer': chann.cid})
                            hea = '&'.join(['%s=%s' % (name, value) for (name, value) in head.items()])
                            #stream_url+='|Referer='+chann.cid     
                        else:
                            iframe = parseDOM(html, 'iframe', ret='src')[0]
                            head.update({'Referer': chann.cid})
                            html = (sess.get(iframe,headers=head,verify=False).content)
                            if PY3:    
                                html = html.decode(encoding='utf-8', errors='strict')
                            html = html.replace("\'",'"')
                            head.update({'Referer': iframe})
                            hea = '&'.join(['%s=%s' % (name, value) for (name, value) in head.items()])
                            if 'js/hls.js' in html:
                                stream_u = re.findall("""hls.loadSource\(['"](.+?)['"]\)""",html)[0]
                            else:
                                stream_u = re.findall('src="(.+?m3u8.+?)"',html)[0]
                            stream_url = stream_u #+'|Referer='+iframe  

                else:
                    trick = re.findall('vid1.src([^<]+)<', html)
                    if trick:
                        stream_url = re.findall("""src: ['"]([^'"]+)['"]""",trick[0].replace("\'",'"'))[0]
                        band = sess.get(stream_url,headers=head,verify=False).text
                        if PY3:
                            band = band.decode(encoding='utf-8', errors='strict')
                        stream_url = re.findall("(http.+?)\\r", band.decode('utf-8'), re.MULTILINE)[0]
                        stream_url += '|Referer=' + chann.cid   
                    else:
                        try:
                            iframe = parseDOM(html, 'iframe', ret='src')[0]
                        except:
                            self.noPremiumMessage()
                        head.update({'Referer': chann.cid})
                        html = (sess.get(iframe,headers=head,verify=False).text).replace("\'",'"')
                        if PY3:
                            html = html.decode(encoding='utf-8', errors='strict')
                        html = html.replace("\'",'"')
                        head.update({'Referer': iframe})
                        hea = '&'.join(['%s=%s' % (name, value) for (name, value) in head.items()])
                        if 'js/hls.js' in html:
                            stream_u = re.findall("""hls.loadSource\(['"](.+?)['"]\)""",html)[0]
                        else:
                            stream_u = re.findall('src="(.+?m3u8.+?)"',html)[0]
                        stream_url = stream_u #+'|Referer='+iframe

                data = stream_url +'|'+ hea

                if data is not None and data != "":
                    chann.strm = data
                    chann.lic = hea
                    self.log('getChannelStream found matching channel: cid: %s, name: %s, rtmp: %s' % (chann.cid, chann.name, chann.strm))
                    return chann
                else:
                    self.log('getChannelStream error getting channel stream2, result: %s' % str(data))
                    return None
            except Exception as e:
                self.log('getChannelStream exception while looping: %s\n Data: %s' % (getExceptionString(), str(data)))
            return None
        

