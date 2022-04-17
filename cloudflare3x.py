#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2020 Mariusz89B

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

from __future__ import unicode_literals

import sys

if sys.version_info[0] > 2:
    PY3 = True
else:
    PY3 = False

if PY3:
    import urllib.request, urllib.parse, urllib.error
else:
    import urllib
    import urlparse

import re
import time

class Cloudflare:
    def __init__(self, url,check):
        response = {}
        response['code']= check.status_code
        response['url'] = url
        response['data'] = check.content
        response['error'] = None
        response['headers']= check.headers
        response['succes'] = True

        self.timeout = 8
        if PY3:
            self.domain = urllib.parse.urlparse(response["url"])[1]
            self.protocol = urllib.parse.urlparse(response["url"])[0]
        else:
            self.domain = urlparse.urlparse(response["url"])[1]
            self.protocol = urlparse.urlparse(response["url"])[0]
        self.js_data = {}
        self.header_data = {}

        if not b"var s,t,o,p,b,r,e,a,k,i,n,g,f" in response["data"] or b"chk_jschl" in response["url"]:
            return

        try:

            self.html = response['data']
            self.js_data["auth_url"] = \
                re.compile('<form id="challenge-form" action="([^"]+)" method="get">').findall(response["data"])[0]
            self.js_data["params"] = {}
            self.js_data["params"]["jschl_vc"] = \
                re.compile('<input type="hidden" name="jschl_vc" value="([^"]+)"/>').findall(response["data"])[0]
            self.js_data["params"]["pass"] = \
                re.compile('<input type="hidden" name="pass" value="([^"]+)"/>').findall(response["data"])[0]
            self.js_data["params"]["s"] = \
                re.compile(r'name="s"\svalue="(?P<s_value>[^"]+)').findall(response["data"])[0]				
            self.js_data["wait"] = int(re.compile("\}, ([\d]+)\);", re.MULTILINE).findall(response["data"])[0]) // 1000
        except Exception as e:
            print(e)
            self.js_data = {}

        if "refresh" in response["headers"]:
            try:
                self.header_data["wait"] = int(response["headers"]["refresh"].split(";")[0])
                self.header_data["auth_url"] = response["headers"]["refresh"].split("=")[1].split("?")[0]
                self.header_data["params"] = {}
                self.header_data["params"]["pass"] = response["headers"]["refresh"].split("=")[2]
            except Exception as e:
                print(e)
                self.header_data = {}

    @property
    def wait_time(self):
        if self.js_data.get("wait", 0):
            return self.js_data["wait"]
        else:
            return self.header_data.get("wait", 0)

    @property
    def is_cloudflare(self):
        return self.header_data.get("wait", 0) > 0 or self.js_data.get("wait", 0) > 0

    def get_url(self):
        # Metodo #1 (javascript)
        if self.js_data.get("wait", 0):
           # html=response['data']
            formIndex = self.html.find('id="challenge-form"')
            if formIndex == -1:
                raise Exception('Form not found')	
            subHTML = self.html[formIndex:]	
            if self.html.find('id="cf-dn-', formIndex) != -1:
                extraDIV = re.search('id="cf-dn-.*?>(.*?)<', subHTML).group(1)
                if '/' in extraDIV:
                    subsecs = extraDIV.split('/', 1)
                    extraDIV = self.parseJSString(subsecs[0]) // float(self.parseJSString(subsecs[1]))
                    print(('extraDIV', extraDIV))
                else:
                    extraDIV = float(self.parseJSString(extraDIV))
            else:
                extraDIV = None
            
            # Extract the arithmetic operations.
            init = re.search('setTimeout\(function\(.*?:(.*?)}', self.html, re.DOTALL).group(1)
            builder = re.search("challenge-form'\);\s*;(.*);a.value", self.html, re.DOTALL).group(1)
            if '/' in init:
                subsecs = init.split('/')
                decryptVal = self.parseJSString(subsecs[0]) // float(self.parseJSString(subsecs[1]))
            else:
                decryptVal = self.parseJSString(init)
            lines = builder.replace(' return +(p)}();', '', 1).split(';') # Remove a function semicolon.

            for line in lines:
                if len(line) and '=' in line:
                    heading, expression = line.split('=', 1)
                    
                    if '/' in expression and not 'function' in expression:
                        subsecs = expression.split('/', 1)
                        line_val = self.parseJSString(subsecs[0]) // float(self.parseJSString(subsecs[1]))
                    
                    elif 'eval(eval(atob' in expression:
                        # Direct value function, uses the value in 'extraDIV'.
                        line_val = extraDIV
                            
                    elif '(function(p' in expression:
                        # Some expression + domain string function.                        
                        if '/' in expression:
                            subsecs = expression.split('/', 1)
                            funcSubsecsIndex = 0 if 'function' in subsecs[0] else 1
                            subsecs[funcSubsecsIndex], extraValue = self.sampleDomainFunction(subsecs[funcSubsecsIndex], self.domain)
                            line_val = self.parseJSString(subsecs[0]) // float(self.parseJSString(subsecs[1]) + extraValue)
                        else:
                            line_val = self.parseJSString(self.replaceDomainFunction(expression, self.domain))
                    else:
                        line_val = self.parseJSString(expression)

                    decryptVal = float(
                        eval(('%.16f'%decryptVal) + heading[-1] + ('%.16f'%line_val))
                    )

            answer = float('%.10f'%decryptVal)
            if '+ t.length).toFixed' in self.html:
                answer += len(self.domain) # Only old variantes add the domain length.		
		
            self.js_data["params"]["jschl_answer"] = answer

            if PY3:
                response = "%s://%s%s?%s" % (
                    self.protocol, self.domain, self.js_data["auth_url"], urllib.parse.urlencode(self.js_data["params"]))
            else:
                response = "%s://%s%s?%s" % (
                    self.protocol, self.domain, self.js_data["auth_url"], urllib.urlencode(self.js_data["params"]))

            time.sleep(self.js_data["wait"])

            return response

        # Metodo #2 (headers)
        if self.header_data.get("wait", 0):
            if PY3:
                response = "%s://%s%s?%s" % (
                    self.protocol, self.domain, self.header_data["auth_url"], urllib.parse.urlencode(self.header_data["params"]))
            else:
                response = "%s://%s%s?%s" % (
                    self.protocol, self.domain, self.header_data["auth_url"], urllib.urlencode(self.header_data["params"]))

            time.sleep(self.header_data["wait"])

            return response
			
    def sampleDomainFunction(self, section, domain):
        functionEndIndex = section.find('}')
        miniExpression = ''; parenthesisLevel = 0
        for c in section[functionEndIndex+1 : ]:
            if c == '(':
                parenthesisLevel += 1
            elif c == ')':
                parenthesisLevel -= 1
            else:
                pass
                
            if parenthesisLevel == -1:
                break
            else:
                miniExpression += c
                
        sampleIndex = self.parseJSString(miniExpression[1:-1])
        extraValue = ord(domain[sampleIndex])
        return section.split('+(function(p)', 1)[0] + ')', extraValue
        
        
    def parseJSString(self, s):
        val = int(
            eval(
                s.replace('!+[]','1').replace('!![]','1').replace('[]','0').replace('(', 'str(').replace('(+str', '(str').strip('+')
            )
        )
        return val
