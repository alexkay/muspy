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

import random
from smtplib import SMTPException
from time import sleep

from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.db import IntegrityError, models, transaction
from django.db.backends.signals import connection_created
from django.db.models import Count, Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string

import app.musicbrainz as mb
from app.tools import date_to_iso8601, date_to_str, str_to_date


class Artist(models.Model):

    mbid = models.CharField(max_length=36, unique=True)
    name = models.CharField(max_length=512)
    sort_name = models.CharField(max_length=512)
    disambiguation = models.CharField(max_length=512)
    users = models.ManyToManyField(User, through='UserArtist')

    blacklisted = [
        '89ad4ac3-39f7-470e-963a-56509c546377', # Various Artists
        'fe5b7087-438f-4e7e-afaf-6d93c8c888b2', # Various Artists
        'f731ccc4-e22a-43af-a747-64213329e088', # [anonymous]
        '33cf029c-63b0-41a0-9855-be2a3665fb3b', # [data]
        '314e1c25-dde7-4e4d-b2f4-0a7b9f7c56dc', # [dialogue]
        'eec63d3c-3b81-4ad4-b1e4-7c147d4d2b61', # [no artist]
        '9be7f096-97ec-4615-8957-8d40b5dcbc41', # [traditional]
        '125ec42a-7229-4250-afc5-e057484327fe', # [unknown]
        '203b6058-2401-4bf0-89e3-8dc3d37c3f12', # [unknown]
        '5e760f5a-ea55-4b53-a18f-021c0d9779a6', # [unknown]
        '1d8bc797-ec8a-40d2-8d80-b1346b56a65f', # [unknown]
        '7734d67f-44d9-4ba2-91e3-9b067263210e', # [unknown]
        'd6bd72bc-b1e2-4525-92aa-0f853cbb41bf', # [soundtrack]
        ]
    class Blacklisted(Exception): pass
    class Unknown(Exception): pass

    @classmethod
    def get_by_mbid(cls, mbid):
        """ Fetches the artist and releases from MB if not in the database. """
        if mbid in cls.blacklisted:
            raise cls.Blacklisted()

        try:
            return cls.objects.get(mbid=mbid)
        except cls.DoesNotExist:
            pass

        artist_data = mb.get_artist(mbid)
        if artist_data is None:
            return None
        if not artist_data:
            raise cls.Unknown

        artist = Artist(
            mbid=mbid, name=artist_data['name'], sort_name=artist_data['sort-name'],
            disambiguation=artist_data.get('disambiguation', ''))
        try:
            artist.save()
        except IntegrityError:
            # The artist was added while we were querying MB.
            return cls.objects.get(mbid=mbid)

        # Add a few release groups immediately.
        # Sleep 1s to comply with the MB web service.
        sleep(1)
        LIMIT = 100
        release_groups = mb.get_release_groups(mbid, limit=LIMIT, offset=0)
        if release_groups:
            with transaction.commit_on_success():
                for rg_data in release_groups:
                    # Ignoring releases without a release date or a type.
                    if rg_data.get('first-release-date') and rg_data.get('type'):
                        release_group = ReleaseGroup(
                            artist=artist,
                            mbid=rg_data['id'],
                            name=rg_data['title'],
                            type=rg_data['type'],
                            date=str_to_date(rg_data['first-release-date']),
                            is_deleted=False)
                        release_group.save()

        if release_groups is None or len(release_groups) == LIMIT:
            # Add the remaining release groups
            Job.add_release_groups(artist)

        return artist

    @classmethod
    def get_by_user(cls, user):
        # TODO: paging
        return cls.objects.filter(users=user).order_by('sort_name')[:1000]


class Job(models.Model):

    ADD_ARTIST = 1
    ADD_RELEASE_GROUPS = 2
    GET_COVER = 3
    IMPORT_LASTFM = 4

    user = models.ForeignKey(User, null=True)
    type = models.IntegerField()
    data = models.TextField()

    @classmethod
    def add_artists(cls, user, names):
        with transaction.commit_on_success():
            for name in names:
                cls(user=user, type=cls.ADD_ARTIST, data=name).save()

    @classmethod
    def add_release_groups(cls, artist):
        cls(user=None, type=cls.ADD_RELEASE_GROUPS, data=artist.mbid).save()

    @classmethod
    def get_cover(cls, mbid):
        cls(user=None, type=cls.GET_COVER, data=mbid).save()

    @classmethod
    def import_lastfm(cls, user, username, count):
        cls(user=user, type=cls.IMPORT_LASTFM, data=str(count) + ',' + username).save()

    @classmethod
    def importing_artists(cls, user):
        """Returns a comma-separated list of all artists yet to be imported."""
        q = cls.objects.filter(user=user)
        q = q.filter(type=cls.ADD_ARTIST)
        return [r.data for r in q]

    @classmethod
    def has_import_lastfm(cls, user):
        return cls.objects.filter(user=user).filter(type=cls.IMPORT_LASTFM).exists()


class Notification(models.Model):

    class Meta:
        db_table = 'app_notification'
        unique_together = ('user', 'release_group')

    user = models.ForeignKey(User)
    release_group = models.ForeignKey('ReleaseGroup')


class ReleaseGroup(models.Model):
    """De-normalised release groups

    A release group can have different artists. Instead of adding a
    many-to-many relationship between them, keep everything in one
    table and group by mbid as needed.

    """
    class Meta:
        unique_together = ('artist', 'mbid')

    artist = models.ForeignKey(Artist)
    mbid = models.CharField(max_length=36)
    name = models.CharField(max_length=512)
    type = models.CharField(max_length=16)
    date = models.IntegerField() # 20080101 OR 20080100 OR 20080000
    is_deleted = models.BooleanField()

    users_who_starred = models.ManyToManyField(
        User, through='Star', related_name='starred_release_groups')
    users_to_notify = models.ManyToManyField(
        User, through='Notification', related_name='new_release_groups')

    def date_str(self):
        return date_to_str(self.date)

    def date_iso8601(self):
        return date_to_iso8601(self.date)

    @classmethod
    def get(cls, artist=None, user=None, limit=0, offset=0, feed=False):
        if not artist and not user:
            assert 'Both artist and user are None'
            return None

        # Unfortunately I don't see how to use ORM for these queries.
        sql = """
SELECT
    "app_releasegroup"."id",
    "app_releasegroup"."artist_id",
    "app_releasegroup"."mbid",
    "app_releasegroup"."name",
    "app_releasegroup"."type",
    "app_releasegroup"."date",
    "app_releasegroup"."is_deleted",
    "app_artist"."mbid" AS "artist_mbid",
    "app_artist"."name" AS "artist_name"
    {select}
FROM "app_releasegroup"
JOIN "app_artist" ON "app_artist"."id" = "app_releasegroup"."artist_id"
{join}
WHERE "app_releasegroup"."is_deleted" = 0
{where}
ORDER BY {order}
"""
        select = join = where = ''
        order = '"app_releasegroup"."date" DESC'
        params = []
        if artist:
            where += '\nAND "app_releasegroup"."artist_id" = %s'
            params.append(artist.id)
        if user:
            # Stars.
            select += ',\n"app_star"."id" as "is_starred"'
            join += '\nJOIN "app_userartist" ON "app_userartist"."artist_id" = "app_artist"."id"'
            join += '\nLEFT JOIN "app_star" ON "app_star"."user_id" = "app_userartist"."user_id" AND "app_star"."release_group_id" = "app_releasegroup"."id"'
            where += '\nAND "app_userartist"."user_id" = %s'
            params.append(user.id)
            order = '"app_star"."id" DESC, ' + order
            # Release types.
            profile = user.get_profile()
            types = profile.get_types()
            ss = ','.join('%s' for i in xrange(len(types)))
            where += '\nAND "app_releasegroup"."type" IN (' + ss + ')'
            params.extend(types)

            if feed and profile.legacy_id:
                # Don't include release groups added during the import
                # TODO: Feel free to remove this check some time in 2013.
                where += '\nAND "app_releasegroup"."id" > 261202'

        sql = sql.format(select=select, join=join, where=where, order=order)
        return cls.objects.raw(sql, params)[offset:offset+limit]

    @classmethod
    def get_calendar(cls, date, limit, offset):
        """Returns the list of release groups for the date."""
        q = cls.objects.filter(date__lte=date)
        q = q.select_related('artist')
        # Calendar uses the same template as releases, adapt to conform.
        q = q.extra(select={
                'artist_mbid': '"app_artist"."mbid"',
                'artist_name': '"app_artist"."name"'})
        # TODO: benchmark, do we need an index?
        q = q.filter(is_deleted=False)
        q = q.order_by('-date', 'id')
        return q[offset:offset+limit]


class Star(models.Model):

    class Meta:
        db_table = 'app_star'
        unique_together = ('user', 'release_group')

    user = models.ForeignKey(User)
    release_group = models.ForeignKey(ReleaseGroup)

    @classmethod
    def set(cls, user, id, value):
        try:
            release_group = ReleaseGroup.objects.get(id=id)
        except ReleaseGroup.DoesNotExist:
            return
        if value:
            cls.objects.get_or_create(user=user, release_group=release_group)
        else:
            cls.objects.filter(user=user, release_group=release_group).delete()


class UserArtist(models.Model):

    class Meta:
        unique_together = ('user', 'artist')

    user = models.ForeignKey(User)
    artist = models.ForeignKey(Artist)
    date = models.DateTimeField(auto_now_add=True)

    @classmethod
    def get(cls, user, artist):
        try:
            return cls.objects.get(user=user, artist=artist)
        except cls.DoesNotExist:
            return None

    @classmethod
    def add(cls, user, artist):
        user_artist = cls(user=user, artist=artist)
        try:
            user_artist.save()
        except IntegrityError:
            pass

    @classmethod
    def remove(cls, user, mbids):
        with transaction.commit_on_success():
            for mbid in mbids:
                q = cls.objects.filter(user=user)
                q = q.filter(artist__mbid=mbid)
                q.delete()


class UserProfile(models.Model):

    code_length = 16

    user = models.OneToOneField(User)

    notify = models.BooleanField(default=True)
    notify_album = models.BooleanField(default=True)
    notify_single = models.BooleanField(default=True)
    notify_ep = models.BooleanField(default=True)
    notify_live = models.BooleanField(default=True)
    notify_compilation = models.BooleanField(default=True)
    notify_remix = models.BooleanField(default=True)
    notify_other = models.BooleanField(default=True)
    email_activated = models.BooleanField(default=False)
    activation_code = models.CharField(max_length=code_length)
    reset_code = models.CharField(max_length=code_length)
    legacy_id = models.IntegerField(null=True)

    def get_types(self):
        """Return the list of release types the user wants to follow."""
        types = []
        if self.notify_album: types.append('Album')
        if self.notify_single: types.append('Single')
        if self.notify_ep: types.append('EP')
        if self.notify_live: types.append('Live')
        if self.notify_compilation: types.append('Compilation')
        if self.notify_remix: types.append('Remix')
        if self.notify_other:
            types.extend(['Soundtrack', 'Spokenword', 'Interview', 'Audiobook', 'Other'])
        return types

    def generate_code(self):
        code_chars = '23456789abcdefghijkmnpqrstuvwxyz'
        return ''.join(random.choice(code_chars) for i in xrange(UserProfile.code_length))

    def send_email(self, subject, text_template, html_template, **kwds):
        sender = 'info@muspy.com'
        text = render_to_string(text_template, kwds)
        msg = EmailMultiAlternatives(subject, text, sender, [self.user.email])
        if html_template:
            html = render_to_string(html_template, kwds)
            msg.attach_alternative(html, "text/html")
        try:
            msg.send()
        except SMTPException:
            return False
        return True

    def send_activation_email(self):
        code = self.generate_code()
        self.activation_code = code
        self.save()
        self.send_email(
            subject='Email Activation',
            text_template='email/activate.txt',
            html_template=None,
            code=code)

    def send_reset_email(self):
        code = self.generate_code()
        self.reset_code = code
        self.save()
        self.send_email(
            subject='Password Reset Confirmation',
            text_template='email/reset.txt',
            html_template=None,
            code=code)

    @classmethod
    def activate(cls, code):
        profiles = UserProfile.objects.filter(activation_code=code)
        if not profiles:
            return False
        profile = profiles[0]
        profile.activation_code = ''
        profile.email_activated = True
        profile.save()
        return True

    @classmethod
    def reset(cls, code):
        profiles = UserProfile.objects.filter(reset_code=code)
        if not profiles:
            return None, None
        profile = profiles[0]
        password = User.objects.make_random_password(length=16)
        profile.reset_code = ''
        profile.user.set_password(password)
        with transaction.commit_on_success():
            profile.user.save()
            profile.save()
        return profile.user.email, password

    @classmethod
    def get_by_email(cls, email):
        users = User.objects.filter(email=email.lower())
        return users[0].get_profile() if users else None

    @classmethod
    def get_by_legacy_id(cls, legacy_id):
        profiles = cls.objects.filter(legacy_id=legacy_id)
        return profiles[0] if profiles else None

    @classmethod
    def get_by_username(cls, username):
        users = User.objects.filter(username=username)
        return users[0].get_profile() if users else None


class UserSearch(models.Model):

    user = models.ForeignKey(User)
    search = models.CharField(max_length=512)

    @classmethod
    def get(cls, user):
        return cls.objects.filter(user=user)

    @classmethod
    def remove(cls, user, searches):
        with transaction.commit_on_success():
            for search in searches:
                cls.objects.filter(user=user, search=search).delete()


# Activate foreign keys for sqlite.
@receiver(connection_created)
def activate_foreign_keys(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA foreign_keys=1;')


# Create a profile for each user.
@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    if created:
        p = UserProfile()
        p.user = instance
        p.save()


User.__unicode__ = lambda x: x.email
