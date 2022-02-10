#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   GNU General Public License

#   m-TVGuide KODI Addon
#   Copyright (C) 2012 Tommy Winther

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

if PY3:
    import configparser
else:
    import ConfigParser

import os
import xbmc, xbmcaddon, xbmcvfs
from xml.etree import ElementTree
from xml.parsers.expat import ExpatError
from strings import *

class StreamsService(object):
    def __init__(self):
        path = os.path.join(ADDON_PATH, 'resources', 'addons.ini')
        if PY3:
            self.addonsParser = configparser.ConfigParser(dict_type=OrderedDict)
        else:
            self.addonsParser = ConfigParser.ConfigParser(dict_type=OrderedDict)
        self.addonsParser.optionxform = lambda option: option
        try:
            self.addonsParser.read(path)
        except:
            print('unable to parse addons.ini')

    def loadFavourites(self):
        entries = list() 
        if PY3:
            path = xbmcvfs.translatePath('special://userdata/favourites.xml')
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    xml = f.read()
        else:
            path = xbmc.translatePath('special://userdata/favourites.xml')
            if os.path.exists(path):
                with codecs.open(path, 'r', encoding='utf-8') as f:
                    xml = f.read()

        try:
            doc = ElementTree.fromstring(xml)
            for node in doc.findall('favourite'):
                value = node.text
                if value[0:11] == 'PlayMedia("':
                    value = value[11:-2]
                elif value[0:10] == 'PlayMedia(':
                    value = value[10:-1]
                elif value[0:22] == 'ActivateWindow(10025,"':
                    value = value[22:-9]
                elif value[0:22] == 'ActivateWindow(10025,':
                    value = value[22:-9]
                else:
                    continue

                entries.append((node.get('name'), value))
        except ExpatError:
            pass

        return entries

    def getAddons(self):
        return self.addonsParser.sections()

    def getAddonStreams(self, id):
        return self.addonsParser.items(id)

    def detectStream(self, channel):
        try:
            """
            @param channel:
            @type channel: source.Channel
            """
            favourites = self.loadFavourites()

            # First check favourites, if we get exact match we use it
            for label, stream in favourites:
                if label == channel.title:
                    return stream

            # Second check all addons and return all matches
            matches = []
            exact_matches = []

            for id in self.getAddons():
                try:
                    xbmcaddon.Addon(id)
                except Exception:
                    continue # ignore addons that are not installed

                for (label, stream) in self.getAddonStreams(id):
                    if type(stream) is list:
                        stream = stream[0]

                    if label.lower() == channel.title.lower(): #TODO unicode
                        exact_matches.append((id, label, stream))

                    try:
                        if label == channel.title or label.startswith(channel.title+' @'):
                            matches.append((id, label, stream))
                    except:
                        continue

            exact_matches = set(exact_matches)
            sorted_exact_matches = sorted(exact_matches, key=lambda match: match[1])
            matches = sorted_exact_matches

            if len(matches) == 1:
                return matches[0][2]
            else:
                return matches
        except:
            return None

class OrderedDict(dict):
    # From: http://code.activestate.com/recipes/576693/
    'Dictionary that remembers insertion order'
    # An inherited dict maps keys to values.
    # The inherited dict provides __getitem__, __len__, __contains__, and get.
    # The remaining methods are order-aware.
    # Big-O running times for all methods are the same as for regular dictionaries.

    # The internal self.__map dictionary maps keys to links in a doubly linked list.
    # The circular doubly linked list starts and ends with a sentinel element.
    # The sentinel element never gets deleted (this simplifies the algorithm).
    # Each link is stored as a list of length three:  [PREV, NEXT, KEY].

    def __init__(self, *args, **kwds):
        '''Initialize an ordered dictionary.  Signature is the same as for
        regular dictionaries, but keyword arguments are not recommended
        because their insertion order is arbitrary.
        '''
        if len(args) > 1:
            raise TypeError('expected at most 1 arguments, got %d' % len(args))
        try:
            self.__root
        except AttributeError:
            self.__root = root = []             	# sentinel node
            root[:] = [root, root, None]
            self.__map = {}
        self.__update(*args, **kwds)

    def __setitem__(self, key, value, dict_setitem=dict.__setitem__):
        'od.__setitem__(i, y) <==> od[i]=y'
	# Setting a new item creates a new link which goes at the end of the linked
	# list, and the inherited dictionary is updated with the new key/value pair.
        if key not in self:
            root = self.__root
            last = root[0]
            last[1] = root[0] = self.__map[key] = [last, root, key]
        dict_setitem(self, key, value)

    def __delitem__(self, key, dict_delitem=dict.__delitem__):
        'od.__delitem__(y) <==> del od[y]'
	# Deleting an existing item uses self.__map to find the link which is
	# then removed by updating the links in the predecessor and successor nodes.
        dict_delitem(self, key)
        link_prev, link_next, key = self.__map.pop(key)
        link_prev[1] = link_next
        link_next[0] = link_prev

    def __iter__(self):
        'od.__iter__() <==> iter(od)'
        root = self.__root
        curr = root[1]
        while curr is not root:
            yield curr[2]
            curr = curr[1]

    def __reversed__(self):
        'od.__reversed__() <==> reversed(od)'
        root = self.__root
        curr = root[0]
        while curr is not root:
            yield curr[2]
            curr = curr[0]

    def clear(self):
        'od.clear() -> None.  Remove all items from od.'
        try:
            for node in self.__map.values():
                del node[:]
            root = self.__root
            root[:] = [root, root, None]
            self.__map.clear()
        except AttributeError:
            pass
        dict.clear(self)

    def popitem(self, last=True):
        '''od.popitem() -> (k, v), return and remove a (key, value) pair.
        Pairs are returned in LIFO order if last is true or FIFO order if false.
        '''
        if not self:
            raise KeyError('dictionary is empty')
        root = self.__root
        if last:
            link = root[0]
            link_prev = link[0]
            link_prev[1] = root
            root[0] = link_prev
        else:
            link = root[1]
            link_next = link[1]
            root[1] = link_next
            link_next[0] = root
        key = link[2]
        del self.__map[key]
        value = dict.pop(self, key)
        return key, value

	# -- the following methods do not depend on the internal structure --

    def keys(self):
        'od.keys() -> list of keys in od'
        return list(self)

    def values(self):
        'od.values() -> list of values in od'
        return [self[key] for key in self]

    def items(self):
        'od.items() -> list of (key, value) pairs in od'
        return [(key, self[key]) for key in self]

    def iterkeys(self):
        'od.iterkeys() -> an iterator over the keys in od'
        return iter(self)

    def itervalues(self):
        'od.itervalues -> an iterator over the values in od'
        for k in self:
            yield self[k]

    def iteritems(self):
        'od.iteritems -> an iterator over the (key, value) items in od'
        for k in self:
            yield (k, self[k])

    def update(*args, **kwds):
        '''od.update(E, **F) -> None.  Update od from dict/iterable E and F.
        If E is a dict instance, does:           for k in E: od[k] = E[k]
        If E has a .keys() method, does:         for k in E.keys(): od[k] = E[k]
        Or if E is an iterable of items, does:   for k, v in E: od[k] = v
        In either case, this is followed by:     for k, v in F.items(): od[k] = v
        '''
        if len(args) > 2:
            raise TypeError('update() takes at most 2 positional '
                            'arguments (%d given)' % (len(args),))
        elif not args:
            raise TypeError('update() takes at least 1 argument (0 given)')
        self = args[0]
	# Make progressively weaker assumptions about "other"
        other = ()
        if len(args) == 2:
            other = args[1]
        if isinstance(other, dict):
            for key in other:
                self[key] = other[key]
        elif hasattr(other, 'keys'):
            for key in list(other.keys()):
                self[key] = other[key]
        else:
            for key, value in other:
                self[key] = value
        for key, value in list(kwds.items()):
            self[key] = value

    __update = update	# let subclasses override update without breaking __init__
    __marker = object()

    def pop(self, key, default=__marker):
        '''od.pop(k[,d]) -> v, remove specified key and return the corresponding value.
        If key is not found, d is returned if given, otherwise KeyError is raised.
        '''
        if key in self:
            result = self[key]
            del self[key]
            return result
        if default is self.__marker:
            raise KeyError(key)
        return default

    def setdefault(self, key, default=None):
        'od.setdefault(k[,d]) -> od.get(k,d), also set od[k]=d if k not in od'
        if key in self:
            return self[key]
        self[key] = default
        return default

    def __repr__(self, _repr_running={}):
        'od.__repr__() <==> repr(od)'
        call_key = id(self), _get_ident()
        if call_key in _repr_running:
            return '...'
        _repr_running[call_key] = 1
        try:
            if not self:
                return '%s()' % (self.__class__.__name__,)
            return '%s(%r)' % (self.__class__.__name__, list(self.items()))
        finally:
            del _repr_running[call_key]

    def __reduce__(self):
        'Return state information for pickling'
        items = [[k, self[k]] for k in self]
        inst_dict = vars(self).copy()
        for k in vars(OrderedDict()):
            inst_dict.pop(k, None)
        if inst_dict:
            return (self.__class__, (items,), inst_dict)
        return self.__class__, (items,)

    def copy(self):
        'od.copy() -> a shallow copy of od'
        return self.__class__(self)

    @classmethod
    def fromkeys(cls, iterable, value=None):
        '''OD.fromkeys(S[, v]) -> New ordered dictionary with keys from S
        and values equal to v (which defaults to None).
        '''
        d = cls()
        for key in iterable:
            d[key] = value
        return d

    def __eq__(self, other):
        '''od.__eq__(y) <==> od==y.  Comparison to another OD is order-sensitive
        while comparison to a regular mapping is order-insensitive.
        '''
        if isinstance(other, OrderedDict):
            return len(self)==len(other) and list(self.items()) == list(other.items())
        return dict.__eq__(self, other)

    def __ne__(self, other):
        return not self == other
