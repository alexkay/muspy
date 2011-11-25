# -*- coding: utf-8 -*-
#
# Copyright © 2011 Alexander Kojevnikov <alexander@kojevnikov.com>
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

from django.conf.urls.defaults import *

from piston.authentication import HttpBasicAuthentication

from api.handlers import *


auth = {'authentication': HttpBasicAuthentication(realm="api")}

artist_handler = ApiResource(handler=ArtistHandler)
artists_handler = ApiResource(handler=ArtistsHandler, **auth)
release_handler = ApiResource(handler=ReleaseHandler)
releases_handler = ApiResource(handler=ReleasesHandler)

urlpatterns = patterns('',
    (r'artist/(?P<mbid>[0-9a-f\-]{36})', artist_handler),
    (r'artists/(?P<userid>[0-9a-z]{30})(/(?P<mbid>[0-9a-f\-]{36}))?', artists_handler),
    (r'release/(?P<mbid>[0-9a-f\-]{36})', release_handler),
    (r'releases(/(?P<userid>[0-9a-z]{30}))?', releases_handler),
)
