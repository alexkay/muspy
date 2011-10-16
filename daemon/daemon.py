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

from datetime import datetime, timedelta
import logging
import time
import traceback

from django.db import connection, transaction

from app.models import *
import app.musicbrainz as mb
from app.tools import str_to_date


def daemon():
    """Perform background processing.

    * Periodically check for new releases and send email notifications.
    * Process background jobs triggered by the users.

    """
    logging.info('Start checking artists')
    checked_artists = 0
    artist = None
    while True:

        # Get the next artist.
        artists = Artist.objects.order_by('mbid')
        if artist:
            artists = artists.filter(mbid__gt=artist.mbid)
        try:
            artist = artists[0]
        except IndexError:
            break # last artist
        checked_artists += 1

        sleep()
        logging.info('Checking artist %s' % artist.mbid)
        artist_data = mb.get_artist(artist.mbid)
        if not artist_data:
            # TODO: musicbrainz/network error or deleted?
            logging.warning('Could not fetch artist data')
            continue # skip for now

        # Update artist info if changed.
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

        current = {rg.mbid: rg for rg in ReleaseGroup.objects.filter(artist=artist)}

        # Get release groups
        LIMIT = 100
        offset = 0
        checked_release_groups = 0
        while True:
            sleep()
            release_groups = mb.get_release_groups(artist.mbid, LIMIT, offset)
            if release_groups is None:
                logging.warning('Could not fetch release groups, retrying')
                continue
            logging.info('Fetched %s release groups' % len(release_groups))
            with transaction.commit_on_success():
                for rg_data in release_groups:
                    mbid = rg_data['id']
                    # Ignore releases without a release date.
                    if not rg_data.get('first-release-date'):
                        if mbid in current:
                            release_group = current[mbid]
                            if not release_group.is_deleted:
                                release_group.is_deleted = True
                                release_group.save()
                                logging.info('Deleted release group %s' % mbid)
                        continue

                    checked_release_groups += 1
                    release_date = str_to_date(rg_data['first-release-date'])
                    if mbid in current:
                        release_group = current[mbid]

                        updated = False
                        if release_group.is_deleted:
                            release_group.is_deleted = False
                            updated = True
                        if release_group.name != rg_data['title']:
                            release_group.name = rg_date['title']
                            updated = True
                        if release_group.type != rg_data['type']:
                            release_group.type = rg_date['type']
                            updated = True
                        if release_group.date != release_date:
                            release_group.date = release_date
                            updated = True
                        if updated:
                            release_group.save()
                            logging.info('Updated release group %s' % mbid)

                        del current[mbid]
                    else:
                        release_group = ReleaseGroup(
                            artist=artist,
                            mbid=rg_data['id'],
                            name=rg_data['title'],
                            type=rg_data['type'],
                            date=release_date,
                            is_deleted=False)
                        release_group.save()
                        logging.info('Created release group %s' % mbid)

                        # Notify users
                        cursor = connection.cursor()
                        cursor.execute(
                            """
                            INSERT INTO "app_notification" ("user_id", "release_group_id")
                            SELECT "app_userartist"."user_id", "app_releasegroup"."id"
                            FROM "app_userartist"
                            JOIN "app_artist" ON "app_artist"."id" = "app_userartist"."artist_id"
                            JOIN "app_releasegroup" ON "app_releasegroup"."artist_id" = "app_artist"."id"
                            WHERE "app_releasegroup"."id" = %s
                            """, [release_group.id])
                        logging.info('Notified %d users' % cursor.rowcount)

            if len(release_groups) < LIMIT: break
            offset += LIMIT

        with transaction.commit_on_success():
            for release_group in current:
                release_group.is_deleted = True
                release_group.save()
                logging.info('Deleted release group %s' % mbid)

    logging.info('Checked %d artists and %d release groups' % (checked_artists, checked_release_groups))

    sent_emails = 0
    while True:
        try:
            notification = Notification.objects.all()[0]
        except IndexError:
            break # last one

        with transaction.commit_on_success():
            user = notification.user
            profile = user.get_profile()
            if profile.notify and profile.email_activated:
                types = profile.get_types()
                release_groups = user.new_release_groups.select_related('artist').all()
                release_groups = [
                    rg for rg in release_groups
                    if rg.type in types and is_recent(rg.date)]
                if release_groups:
                    sleep()
                    result = user.get_profile().send_email(
                        subject='[muspy] New Release Notification',
                        text_template='email/release.txt',
                        html_template='email/release.html',
                        releases=release_groups,
                        root='http://muspy.com/')
                    if not result:
                        logging.warning('Could not send to user %d, retrying' % user.id)
                        continue
                    sent_emails += 1
                    logging.info('Sent notification to user %d' % user.id)

            user.new_release_groups.clear()

    logging.info('Sent %d email notifications, restarting' % sent_emails)


def is_recent(date):
    """Check if the integer date is not older than one year."""
    date = datetime(
        year=date // 10000,
        month=(date // 100) % 100 or 1,
        day=date % 100 or 1)
    one_year = timedelta(weeks=52)
    return date > datetime.utcnow() - one_year


def sleep():
    """Sleep to avoid clogging up MusicBrainz servers.

    Call it before each MB request.

    """
    DELAY = 2 # seconds
    duration = time.time() - sleep.start
    if DELAY - duration > 0:
        time.sleep(DELAY - duration)
    sleep.start = time.time()

sleep.start = time.time()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    try:
        daemon()
    except:
        logging.error('Daemon error:\n' + traceback.format_exc())
