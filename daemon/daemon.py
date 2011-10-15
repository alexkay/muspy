#!/usr/bin/env python
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

# Allow the cron script to run in the Django project context
import os, sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../..'))
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'muspy.settings'

import logging
import time

from app.models import *
import app.musicbrainz as mb

DELAY = 4

def daemon():
    """Perform background processing.

    * Periodically check for new releases and send email notifications.
    * Process background jobs triggered by the users.

    """
    logging.info('Start checking artists')
    start = time.time()

    artist = None
    while True:
        # Sleep to avoid clogging up MusicBrainz servers.
        start = sleep(start)

        # Get the next artist.
        artists = Artist.objects.order_by('mbid')
        if artist:
            artists = artists.filter(mbid__gt=artist.mbid)
        try:
            artist = artists[0]
        except IndexError:
            break # last artist

        logging.info('Checking artist %s' % artist.mbid)
        artist_data = mb.get_artist(artist.mbid)
        if not artist_data:
            # TODO: musicbrainz/network error or deleted?
            logging.warning('Could not fetch artist data')
            continue # skip for now

        updated = False
        if artist.name != artist_data['name']:
            artist.name = artist_data['name']
            updated = True
        if artist.sort_name != artist_data['sort-name']:
            artist.sort_name = artist_data['sort-name']
            updated = True
        if artist.disambiguation != artist_data.get('disambiguation', ''):
            artist.disambiguation = artist_data.get('disambiguation', '')
            updated = True
        if updated:
            logging.info('Artist changed, updating')
            artist.save()

        start = sleep(start)

    logging.info('Done checking artists')

def sleep(start):
    duration = time.time() - start
    if DELAY - duration > 0:
        time.sleep(DELAY - duration)
    return time.time()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    daemon()
