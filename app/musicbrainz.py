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

from urllib import urlencode
from urllib2 import Request, urlopen
from xml.etree import ElementTree as et

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
