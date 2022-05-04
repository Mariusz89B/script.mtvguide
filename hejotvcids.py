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

#   Some implementations are modified and taken from "plugin.video.hejotv" - thank you very much mbebe!

import sys

if sys.version_info[0] > 2:
    PY3 = True
else:
    PY3 = False

if PY3:
    from urllib.parse import parse_qsl, quote, urlencode
    import http.cookiejar
    from cmf3 import parseDOM
    from cmf3 import replaceHTMLCodes

else:
    from urlparse import parse_qsl
    import  cookielib
    from urllib import unquote, quote, urlencode
    from cmf2 import parseDOM
    from cmf2 import replaceHTMLCodes

import os, copy, re
import xbmc, xbmcaddon, xbmcgui, xbmcplugin, xbmcvfs
import requests
import base64
import string
import jsunpack
import cloudflare3x
from strings import *
from serviceLib import *

serviceName         = 'Hejo TV'
hejotvUrl           = 'https://hejo.tv'
homeUrl             = 'https://hejo.tv/home'

if PY3:
    COOKIEFILE = os.path.join(xbmcvfs.translatePath(ADDON.getAddonInfo('profile')), 'hejotv.cookie')
else:
    COOKIEFILE = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('profile')), 'hejotv.cookie')
sess = requests.Session()

if PY3:
    sess.cookies = http.cookiejar.LWPCookieJar(COOKIEFILE)
else:
    sess.cookies = cookielib.LWPCookieJar(COOKIEFILE)

kukz = ''
kukz2 = ''
packer = re.compile('(eval\(function\(p,a,c,k,e,(?:r|d).*)')

UA = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0'

headersok = {
    'User-Agent': UA,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
    'Referer': 'https://hejo.tv/home',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',}

class HejoTVUpdater(baseServiceUpdater):
    def __init__(self):
        self.serviceName        = serviceName
        self.localMapFile       = 'hejotvmap.xml'
        baseServiceUpdater.__init__(self)
        self.serviceEnabled     = ADDON.getSetting('hejotv_enabled')
        self.login              = ADDON.getSetting('hejotv_username').strip()
        self.password           = ADDON.getSetting('hejotv_password').strip()
        self.servicePriority    = int(ADDON.getSetting('priority_hejotv'))
        self.jakosc             = ADDON.getSetting('hejotv_video_quality')
        self.check              = ADDON.getSetting('hejotv_check')
        self.url                = hejotvUrl
        self.addDuplicatesToList = True
        ADDON.setSetting('hejotv_check', 'true')

    def cf_setCookies(self):
        sess.headers.update({
            'User-Agent': UA,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',})
        url = 'https://hejo.tv/'
        check = sess.get(url)
        cf = cloudflare3x.Cloudflare(url,check)
        token1=''
        if cf.is_cloudflare:
            authUrl = cf.get_url()
            makeAuth = sess.get(authUrl)
            result = sess.get(url).content
        dataPath=os.path.dirname(COOKIEFILE)
        if not os.path.exists(dataPath):
            os.makedirs(dataPath)
        if sess.cookies:
            sess.cookies.save(COOKIEFILE, ignore_discard = True)
        return
        
    def cookieString(self, COOKIEFILE):
        sc = ''
        if os.path.isfile(COOKIEFILE):
            sess.cookies.load(COOKIEFILE)
            sc = ''.join(['{}={};'.format(c.name, c.value) for c in sess.cookies])
        return sc  

    def getUrl(self, url, redir=True):
        sess.headers.update({'User-Agent': UA})
        if os.path.isfile(COOKIEFILE):
            sess.cookies.load(COOKIEFILE, ignore_discard = True)
        if redir:
            html = sess.get(url, cookies=sess.cookies, verify=False, allow_redirects = redir).text
        else:
            html = sess.get(url, cookies=sess.cookies, verify=False, allow_redirects = redir)
        if 'function setCookie' in html:
            try:
                kk = self.dodajKuki(html)
                if kk:
                    self.getUrl(url)
                else:
                    pass
            except:
                pass

        return html

    def dodajKuki(self, html):
        packer2 = re.compile('(eval\(function\(p,a,c,k,e,d\).+?{}\)\))')

        unpacked = ''
        packeds = packer2.findall(html)
        for packed in packeds:
            unpacked += jsunpack.unpack(packed)
        unpacked = unpacked.replace("\\'", '"')
        kukz = re.findall("""setCookie\(['"](.+?)['"],['"](.+?)['"]""",unpacked)#[0]
        if kukz:
            kukz = kukz[0]
            nowy_cookie = requests.cookies.create_cookie(kukz[0], kukz[1])
            sess.cookies.set_cookie(nowy_cookie)
            sess.cookies.save(COOKIEFILE, ignore_discard = True)
            return True
        else:
            return False

    def zalogujponownie(exlink):
        sess.cookies.clear()
        username = self.login
        password = self.password
        check = self.check
        
        if username and password and check == 'true':
            headers = {
                    'Host': 'hejo.tv',
                'User-Agent': UA,
                'Accept': 'text/html',
                'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = sess.get('http://hejo.tv/', headers=headers,verify=False).content
            if PY3:   
                response = response.decode(encoding='utf-8', errors='strict')

            packer2 = re.compile('(eval\(function\(p,a,c,k,e,d\).+?{}\)\))')

            unpacked = ''
            packeds = packer2.findall(response)#[0]
            for packed in packeds:
                unpacked += jsunpack.unpack(packed)
            unpacked = unpacked.replace("\\'", '"')

            try:
                kukz=re.findall("""setCookie\(['"](.+?)['"],['"](.+?)['"]""",unpacked)[0]
                nowy_cookie = requests.cookies.create_cookie(kukz[0],kukz[1])
                
                sess.cookies.set_cookie(nowy_cookie)
                response = sess.get('http://hejo.tv/',verify=False).content
                if PY3:       
                    response = response.decode(encoding='utf-8', errors='strict')
            except:
                pass

            token = parseDOM(response, 'meta', attrs={'name':'csrf-token'},ret='content')[0]  
            data = {'_token': token,'username': username,'password': password}
            response = sess.post('https://hejo.tv/login', data=data,verify=False).content
            if PY3:     
                response = response.decode(encoding='utf-8', errors='strict')
            packer2 = re.compile('(eval\(function\(p,a,c,k,e,d\).+?{}\)\))')
            unpacked = ''
            packeds = packer2.findall(response)#[0]
            for packed in packeds:
                unpacked += jsunpack.unpack(packed)

            unpacked = unpacked.replace("\\'", '"')
            kukz = re.findall("""setCookie\(['"](.+?)['"],['"](.+?)['"]""",unpacked)[0]
            nowy_cookie = requests.cookies.create_cookie(kukz[0],kukz[1])
            sess.cookies.set_cookie(nowy_cookie)
            html = sess.get('https://hejo.tv/login',verify=False).content
            if PY3:   
                html = html.decode(encoding='utf-8', errors='strict')

            if html.find('logowany jako') > 0:
                sess.cookies.save(COOKIEFILE, ignore_discard = True)
        return

    def loginService(self):
        try:
            self.cf_setCookies()

            username = self.login
            password = self.password
            check = self.check

            if username and password and check == 'true':
                mainurl = 'https://hejo.tv/'
                headers = {
                    'Host': 'hejo.tv',
                    'User-Agent': UA,
                    'Accept': 'text/html',
                    'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
                    'DNT': '1',
                    'Upgrade-Insecure-Requests': '1',
                }

                response = sess.get('http://hejo.tv/', headers=headers,verify=False).content
                if PY3:   
                    response = response.decode(encoding='utf-8', errors='strict')
                packer2 = re.compile('(eval\(function\(p,a,c,k,e,d\).+?{}\)\))')
                unpacked = ''
                packeds = packer2.findall(response)#[0]

                for packed in packeds:
                    unpacked += jsunpack.unpack(packed)
                unpacked = unpacked.replace("\\'", '"')

                try:
                    kukz=re.findall("""setCookie\(['"](.+?)['"],['"](.+?)['"]""",unpacked)[0]
                    nowy_cookie = requests.cookies.create_cookie(kukz[0],kukz[1])
                    sess.cookies.set_cookie(nowy_cookie)
                    response = sess.get('http://hejo.tv/',headers=headers,verify=False).content
                    if PY3:   
                        response = response.decode(encoding='utf-8', errors='strict')
                except:
                    pass

                token = parseDOM(response, 'meta', attrs={'name':'csrf-token'},ret='content')[0]
                headers2 = {
                    'Host': 'hejo.tv',
                    'user-agent': UA,
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'accept-language': 'pl,en-US;q=0.7,en;q=0.3',
                    'content-type': 'application/x-www-form-urlencoded',
                    'origin': 'https://hejo.tv',
                    'referer': 'https://hejo.tv/',
                    'upgrade-insecure-requests': '1',
                    'te': 'trailers'
                }

                data = '_token={}&username={}&password={}'.format(token,username,quote(password))

                response = sess.post('https://hejo.tv/login', data=data, headers=headers2, verify=False).content
                if PY3:   
                    response = response.decode(encoding='utf-8', errors='strict')

                packer2 = re.compile('(eval\(function\(p,a,c,k,e,d\).+?{}\)\))')
                unpacked = ''
                packeds = packer2.findall(response)#[0]

                for packed in packeds:
                    unpacked += jsunpack.unpack(packed)
                unpacked = unpacked.replace("\\'", '"')
                kukz = re.findall("""setCookie\(['"](.+?)['"],['"](.+?)['"]""",unpacked)#[0]
                if kukz:
                    kukz = kukz[0]
                    nowy_cookie = requests.cookies.create_cookie(kukz[0],kukz[1])
                    sess.cookies.set_cookie(nowy_cookie)
                html = sess.get('https://hejo.tv/login',verify=False).content
                if PY3:   
                    html = html.decode(encoding='utf-8', errors='strict')

                if html.find('logowany jako') > 0:
                    sess.cookies.save(COOKIEFILE, ignore_discard = True)
                    if 'Wykup konto premium' in html:
                        return True
                    else:
                        info = (re.findall('>(Premium do.+?)</a>', html)[0]).lower()
                        log1 = re.findall("""class="fa fa-user" aria-hidden="true"></i>([^<]+)<""", html)[0]
                        return True
                else:
                    self.log('Error when trying to login in hejo.tv!, result: %s' % str(response))
                    self.loginErrorMessage() 
                    return False
            else:
                self.log('Error when trying to login in hejo.tv!, result: %s' % str(response))
                self.loginErrorMessage() 
                return False

        except:
            self.log('Exception while trying to log in: %s' % getExceptionString())
            self.loginErrorMessage()  
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
            url = 'https://hejo.tv/'
            kuk = self.cookieString(COOKIEFILE)
            html = ''
            
            html += self.getUrl(url)  
            links = parseDOM(html, 'div', attrs={'class': "col-lg-3 col-md-4 col-sm-6 col-12 p-2"}) 
            
            for link in links:
                cid = parseDOM(link, 'a', ret='href')[0]
                name = parseDOM(link, 'img', ret='alt')[0]
                title = parseDOM(link, 'img', ret='alt')[0] + ' PL'
                img = parseDOM(link, 'img', ret='src')[0]

                name = re.sub(r'(?i)(\s*(on|off)line)', '', name)
                title = re.sub(r'(?i)(\s*(on|off)line)', '', title)

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
        url = chann.cid
        
        sess.headers.update({
            'User-Agent': UA,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
            'Referer': 'https://hejo.tv/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        try:
            html = self.getUrl(url)

            unpack = ''   
            
            htmlsy = re.findall('script.defer(.+?)$',html,re.DOTALL)#[0]
            htmlsy = htmlsy[0] if htmlsy else html
            pack3 = re.compile('(eval\(function\(p,a,c,k,e,d\).+?\)\)\))')
            results = pack3.findall(htmlsy)#[0]

            for result in results:
                try:
                    unpack += jsunpack.unpack(result)
                except:
                    self.noPremiumMessage()
            packer2 = re.compile('(eval\(function\(p,a,c,k,e,d\).+?{}\)\))') 
            results = packer2.findall(htmlsy)#[0]
            for result in results:
                unpack += jsunpack.unpack(result)
            
            unpack = unpack.replace("\\\'",'"')
            if 'setCookie' in unpack:
                self.zalogujponownie()
                self.getChannelStream(chann)
            
            api = re.findall('.get\("([^"]+)",function\(c\)',unpack)[0]
            nxturl = parseDOM(html, 'iframe', attrs={'name': "livetv","src":".+?"},ret='src')[0] 
            api = 'https://hejo.tv'+ api if api.startswith('/') else api

            chTbl = []
            
            headers2 = {
            'User-Agent': UA,
            'Accept': '*/*',
            'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
            'Referer': url,
            'TE': 'Trailers',
            }

            chTbl = sess.get(api, cookies=sess.cookies, headers=headers2, verify=False).json()

            headers = {
            'User-Agent': UA,
            'Accept': '*/*',
            'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
            'Referer': url,
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
            'TE': 'Trailers',}

            html = sess.get(nxturl, cookies=sess.cookies, headers=headers, verify=False)#.content

            ref = html.url
            html = html.content
            if PY3:    
                html = html.decode(encoding='utf-8', errors='strict')
            stream_url = re.findall("hls.loadSource\('(.+?)'\)",html)[0]
            
            pol = sess.get(stream_url, cookies=sess.cookies, headers=headers, verify=False).content
            if PY3:
                pol = pol.decode(encoding='utf-8', errors='strict')
            jakoscstream_url = re.findall('RESOLUTION=(.+?)\\r\\n(htt.+?)\\r',pol,re.DOTALL)
            if jakoscstream_url:
                if self.jakosc == 'Auto':
                    stream_url = jakoscstream_url[0][1]

                elif self.jakosc == 'HD':
                    self.jakosc = '1280x720'

                elif self.jakosc == 'FWVGA':
                    self.jakosc = '854x480'

                elif self.jakosc == 'SD':
                    self.jakosc = '640x360'

                else:
                    try:
                        for jak,href in jakoscstream_url:
                            if jakosc == jak:
                                stream_url = href
                            else:
                                continue

                    except:
                        stream_url = jakoscstream_url[0][1]

                data = stream_url + '|Referer=' + ref   
                #kuk = self.cookieString(COOKIEFILE)
                #data = stream_url+'|User-Agent='+urllib.quote(UA)+'&Referer='+ref+'&Cookie='+urllib.quote(kuk)     
            else:
                data = '' #stream_url+'|Referer='+ref
        
            if data is not None and data != "":
                chann.strm = data
                self.log('getChannelStream found matching channel: cid: %s, name: %s, rtmp: %s' % (chann.cid, chann.name, chann.strm))
                return chann
            else:
                self.log('getChannelStream error getting channel stream2, result: %s' % str(data))
                return None
        except Exception as e:
            self.log('getChannelStream exception while looping: %s\n Data: %s' % (getExceptionString(), str(data)))
        return None