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

    @classmethod
    def get_by_mbid(cls, mbid):
        """ Fetches the artist and releases from MB if not in the database. """
        try:
            return cls.objects.get(mbid=mbid)
        except cls.DoesNotExist:
            pass

        artist_data = mb.get_artist(mbid)
        if not artist_data:
            return None

        # Sleep 1s to comply with the MB web service.
        sleep(1)

        artist = Artist(
            mbid=mbid, name=artist_data['name'], sort_name=artist_data['sort-name'],
            disambiguation=artist_data.get('disambiguation', ''))
        artist.save()

        # Add a few release groups immediately.
        release_groups = mb.get_release_groups(mbid, limit=100, offset=0)
        if release_groups:
            with transaction.commit_on_success():
                for rg_data in release_groups:
                    # Ignoring releases without a release date.
                    if rg_data.get('first-release-date'):
                        release_group = ReleaseGroup(
                            artist=artist,
                            mbid=rg_data['id'],
                            name=rg_data['title'],
                            type=rg_data['type'],
                            date=str_to_date(rg_data['first-release-date']),
                            is_deleted=False)
                        release_group.save()
        return artist

    @classmethod
    def get_by_user(cls, user):
        # TODO: paging
        return cls.objects.filter(users=user).order_by('sort_name')[:1000]


class ReleaseGroup(models.Model):

    artist = models.ForeignKey(Artist)
    mbid = models.CharField(max_length=36, unique=True)
    name = models.CharField(max_length=512)
    type = models.CharField(max_length=16)
    date = models.IntegerField() # 20080101 OR 20080100 OR 20080000
    is_deleted = models.BooleanField()
    users = models.ManyToManyField(User, through='Star') # users that starred this release

    def date_str(self):
        return date_to_str(self.date)

    def date_iso8601(self):
        return date_to_iso8601(self.date)

    @classmethod
    def get(cls, artist=None, user=None, limit=0, offset=0):
        if not artist and not user:
            assert 'Both artist and user are None'
            return None
        q = cls.objects.filter(is_deleted=False)
        q = q.select_related('artist__mbid', 'artist__name')
        if artist:
            q = q.filter(artist=artist)
        if user:
            q = q.filter(artist__userartist__user=user)
            q = q.filter(Q(users=user) | Q(users__isnull=True))
            q = q.filter(type__in=user.get_profile().get_types())
            q = q.annotate(is_starred=Count('users'))
            q = q.order_by('-users', '-date')
        else:
            q = q.order_by('-date')
        return q[offset:offset+limit]

    @classmethod
    def get_calendar(cls, date, limit, offset):
        """Returns the list of release groups for the date."""
        q = cls.objects.filter(date__lte=date)
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
    def set(cls, user, mbid, value):
        try:
            release_group = ReleaseGroup.objects.get(mbid=mbid)
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
                q = cls.objects.filter(user__id=user.id)
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
            msg.attach_alternative(html_content, "text/html")
        msg.send()

    def send_activation_email(self):
        code = self.generate_code()
        self.activation_code = code
        self.save()
        self.send_email(subject='Email Activation',
                        text_template='email/activate.txt',
                        html_template=None,
                        code=code)

    def send_reset_email(self):
        code = self.generate_code()
        self.reset_code = code
        self.save()
        self.send_email(subject='Password Reset Confirmation',
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
        # TODO: transaction
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
