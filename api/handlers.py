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

from django.core.exceptions import ObjectDoesNotExist

from piston.handler import AnonymousBaseHandler, BaseHandler
from piston.utils import rc

from app.models import *


class ArtistHandler(AnonymousBaseHandler):
    allowed_methods = ('GET',)

    def read(self, request, mbid):
        try:
            artist = Artist.objects.get(mbid=mbid)
        except Artist.DoesNotExist:
            return rc.NOT_HERE

        return {
            'mbid': artist.mbid,
            'name': artist.name,
            'sort_name': artist.sort_name,
            'disambiguation': artist.disambiguation,
            }

class ReleaseHandler(AnonymousBaseHandler):
    allowed_methods = ('GET',)

    def read(self, request, mbid):
        q = ReleaseGroup.objects.select_related('artist')
        q = q.filter(mbid=mbid)
        q = q.filter(is_deleted=False)
        releases = list(q)
        if not releases:
            return rc.NOT_HERE

        release = releases[0]
        artists = [release.artist for release in releases]
        return {
            'mbid': release.mbid,
            'name': release.name,
            'type': release.type,
            'date': release.date_str(),
            'artists': [{
                    'mbid': artist.mbid,
                    'name': artist.name,
                    'sort_name': artist.sort_name,
                    'disambiguation': artist.disambiguation,
                    } for artist in artists]
            }
