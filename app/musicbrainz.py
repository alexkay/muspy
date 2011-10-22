# -*- coding: utf-8 -*-
#
# Copyright © 2009-2011 Alexander Kojevnikov <alexander@kojevnikov.com>
#
# muspy is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# muspy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with muspy.  If not, see <http://www.gnu.org/licenses/>.

from socket import setdefaulttimeout
from urllib import urlencode
from urllib2 import Request, urlopen
from xml.etree import ElementTree as et

setdefaulttimeout(10)

def search_artists(query, limit, offset):
    try:
        xml = _fetch('artist', query=query, limit=limit, offset=offset)
    except:
        return None, 0

    root, ns = _parse_root(xml)
    if root is None:
        return [], 0

    artist_list = root.find('%sartist-list' % ns)
    if artist_list is None:
        return [], 0

    count = int(artist_list.get('count'))
    artists = [_parse_artist(element, ns) 
               for element 
               in root.findall('%sartist-list/%sartist' % (ns, ns))]
    return artists, count

def get_artist(mbid):
    try:
        xml = _fetch('artist', mbid=mbid)
    except:
        return None

    root, ns = _parse_root(xml)
    if root is None:
        return None

    return _parse_artist(root.find('%sartist' % ns), ns)

def get_release_groups(mbid, limit, offset=0):
    try:
        xml = _fetch('release-group', artist=mbid, limit=limit, offset=offset)
    except:
        return None

    root, ns = _parse_root(xml)
    if root is None or ns is None:
        return []

    return [_parse_release_group(element, ns)
            for element
            in root.findall('%srelease-group-list/%srelease-group' % (ns, ns))]

def get_releases(mbid, limit, offset=0):
    try:
        kw = {'release-group': mbid, 'limit': limit, 'offset': offset}
        xml = _fetch('release', **kw)
    except:
        return None

    root, ns = _parse_root(xml)
    if root is None or ns is None:
        return []

    return [_parse_release(element, ns)
            for element
            in root.findall('%srelease-list/%srelease' % (ns, ns))]

def _fetch(resource, mbid=None, **kw):
    url = 'http://musicbrainz.org/ws/2/'
    url += resource + '/'
    if mbid: 
        url += mbid
    url += '?' + _urlencode(kw)

    request = Request(url, headers = {'User-Agent': 'muspy/2.0'})
    response = urlopen(request)
    return response.read()

def _urlencode(params):
    if isinstance(params, dict):
        params = params.items()
    return urlencode([(k, v.encode('utf-8') if isinstance(v, unicode) else v)
                      for k, v in params])

def _parse_root(xml):
    try:
        root = et.fromstring(xml)
        ns = root.tag[:root.tag.find('metadata')]
        return root, ns
    except:
        return None, None

def _parse_artist(element, ns):
    d = {}
    d['id'] = element.get('id').lower()
    for attr in element.attrib:
        if attr.endswith('score'):
            d['score'] = element.get(attr)
            d['best_match'] = d['score'] in ('100', '99')
            break
    for prop in element:
        d[prop.tag[len(ns):]] = prop.text
    return d

def _parse_release_group(element, ns):
    d = {}
    d['id'] = element.get('id').lower()
    d['type'] = element.get('type')
    for prop in element:
        d[prop.tag[len(ns):]] = prop.text
    return d

def _parse_release(element, ns):
    d = {}
    d['id'] = element.get('id').lower()
    for prop in element:
        d[prop.tag[len(ns):]] = prop.text
    return d
