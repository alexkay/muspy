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

from calendar import monthrange
from datetime import date, timedelta, datetime
import re

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_control

from settings import LOGIN_REDIRECT_URL

from app import lastfm
from app.cover import Cover
from app.forms import *
from app.models import *
import app.musicbrainz as mb
from app.tools import arrange_for_table, str_to_date, date_to_str

def activate(request):
    if 'code' in request.GET:
        if UserProfile.activate(request.GET['code']):
            messages.success(request, 'Your email address has been activated.')
        else:
            messages.error(request, 'Invalid activation code, your email address was not activated.')
        return redirect('/')

    if not request.user.is_authenticated():
        messages.error(request, 'You need to sign in to activate your email address.')
        return redirect('/')

    if request.user.get_profile().email_activated:
        messages.info(request, 'Your email address is already active.')
        return redirect('/')

    request.user.get_profile().send_activation_email()
    return render(request, 'activate.html')

def artist(request, mbid):
    try:
        artist = Artist.get_by_mbid(mbid)
    except (Artist.Blacklisted, Artist.Unknown):
        return HttpResponseNotFound()
    if not artist:
        # TODO: Show a meaningful error message.
        return HttpResponseNotFound()

    PER_PAGE = 10
    try:
        offset = int(request.GET.get('offset', 0))
    except ValueError:
        return HttpResponseNotFound()
    user_has_artist = request.user.is_authenticated() and UserArtist.get(request.user, artist)
    if user_has_artist:
        show_stars = True
        release_groups = ReleaseGroup.get(
            artist=artist, user=request.user, limit=PER_PAGE, offset=offset)
    else:
        show_stars = False
        release_groups = ReleaseGroup.get(
            artist=artist, limit=PER_PAGE, offset=offset)

    release_groups = list(release_groups)
    offset = offset + PER_PAGE if len(release_groups) == PER_PAGE else None
    return render(request, 'artist.html', {
            'artist': artist,
            'release_groups': release_groups,
            'offset': offset,
            'PER_PAGE': PER_PAGE,
            'user_has_artist': user_has_artist,
            'show_stars': show_stars})

@login_required
def artists(request):
    artists = Artist.get_by_user(request.user)

    COLUMNS = 3
    artist_rows = arrange_for_table(artists, COLUMNS)

    # Using REQUEST because this handler can be called using both GET and POST.
    search = request.REQUEST.get('search', '')
    dontadd = request.REQUEST.get('dontadd', '')
    offset = request.REQUEST.get('offset', '')
    offset = int(offset) if offset.isdigit() else 0

    found_artists, count = [], 0
    LIMIT = 20
    if search:
        if len(search) > 16384:
            messages.error(request, 'The search string is too long.')
            return redirect('/artists')

        # FB likes are separated by '*'. 32 is completely random.
        if len(search) > 32 and search.count('*') > len(search) // 32:
            searches = [s.strip() for s in search.split('*') if s.strip()]
        else:
            searches = [s.strip() for s in search.split(',') if s.strip()]
        if len(searches) > 1 and not offset:
            # Batch add mode.
            if dontadd:
                messages.warning(
                    request,
                    'Cannot search for multiple artists. '
                    'Remove all commas and asterisks to search.')
                return render(request, 'artists.html', {
                        'artist_rows': artist_rows,
                        'search': search,
                        'dontadd': dontadd})

            Job.add_artists(request.user, searches)
            messages.info(
                request, 'Your artists will be processed in the next couple of '
                'minutes. In the meantime you can add more artists.')
            return redirect('/artists')

        found_artists, count = mb.search_artists(search, limit=LIMIT, offset=offset)
        if found_artists is None:
            messages.error(request, 'The search server could not fulfil your request '
                           'due to an internal error. Please try again later.')
            return render(request, 'artists.html', {
                    'artist_rows': artist_rows,
                    'search': search,
                    'dontadd': dontadd})

        only_one = len(found_artists) == 1
        first_is_exact = (len(found_artists) > 1 and
                          found_artists[0]['name'].lower() == search.lower() and
                          found_artists[1]['name'].lower() != search.lower())
        if not dontadd and not offset and (only_one or first_is_exact):
            # Only one artist found - add it right away.
            artist_data = found_artists[0]
            mbid = artist_data['id']
            try:
                artist = Artist.get_by_mbid(mbid)
            except (Artist.Blacklisted, Artist.Unknown):
                return redirect('/artists')
            if not artist:
                # TODO: error message
                return redirect('/artists')

            UserArtist.add(request.user, artist)
            messages.success(request, "%s has been added!" % artist.name)
            return redirect('/artists')

    artists_offset = offset + len(found_artists)
    artists_left = max(0, count - artists_offset)
    found_artists = [a for a in found_artists if a['id'] not in Artist.blacklisted]

    importing = ', '.join(Job.importing_artists(request.user))

    pending = sorted(s.search for s in UserSearch.get(request.user)[:200])
    pending_rows = arrange_for_table(pending, COLUMNS)

    return render(request, 'artists.html', {
            'artist_rows': artist_rows,
            'artist_count': len(artists),
            'search': search,
            'dontadd': dontadd,
            'found_artists': found_artists,
            'artists_offset': artists_offset,
            'artists_left': artists_left,
            'importing': importing,
            'pending_rows': pending_rows,
            'pending_count': len(pending)})

@login_required
def artists_add(request):
    mbid = request.GET.get('id', '').lower()
    try:
        artist = Artist.get_by_mbid(mbid)
    except Artist.Blacklisted:
        messages.error(request, 'The artist is special-purpose and cannot be added')
        return redirect('/artists')
    except Artist.Unknown:
        messages.error(request, 'Unknown artist')
        return redirect('/artists')
    if not artist:
        # TODO: Show a meaningful error message.
        return HttpResponseNotFound()

    UserArtist.add(request.user, artist)

    search = request.GET.get('search', '')
    UserSearch.remove(request.user, [search])

    messages.success(request, "%s has been added!" % artist.name)
    return redirect('/artists')

@login_required
def artists_remove(request):
    names = request.POST.getlist('name')
    mbids = request.POST.getlist('id')
    if not names and not mbids:
        messages.info(request, 'Use checkboxes to select the artists you want to remove.')
        return redirect('/artists')

    if names:
        UserSearch.remove(request.user, names)
        messages.success(request, 'Removed %d pending artists.' % len(names))
        return redirect('/artists')

    UserArtist.remove(request.user, mbids)
    messages.success(request, 'Removed %d artist%s.' % (len(mbids), 's' if len(mbids) > 1 else ''))
    return redirect('/artists')

def calendar(request):
    date_str = request.GET.get('date', None)
    today = int(date.today().strftime('%Y%m%d'))
    if date_str:
        if not re.match("^\d{4}(-\d{2})?(-\d{2})?$", date_str):
            return redirect('/calendar')
        date_int = str_to_date(date_str)
    else:
        date_int = today
    try:
        offset = int(request.GET.get('offset', 0))
    except ValueError:
        return HttpResponseNotFound()
    PER_PAGE = 10
    limit = PER_PAGE + 1
    releases = list(ReleaseGroup.get_calendar(date_int, limit, offset))

    if len(releases) == limit:
        if releases[0].date == releases[-1].date:
            next_date = date_to_str(date_int)
            next_offset = offset + PER_PAGE
            releases = releases[:-1]
        else:
            if offset:
                i = min(i for i in xrange(limit) if releases[i].date != releases[0].date)
                next_date = date_to_str(releases[i].date)
                next_offset = 0
                releases = releases[:i]
            else:
                next_date = date_to_str(releases[-1].date)
                next_offset = 0
                releases = [r for r in releases if r.date != releases[-1].date]
    else:
        next_date = None
        next_offset = 0

    for i, release in enumerate(releases):
        if i > 0 and release.date == releases[i - 1].date:
            release.date_first = None
        else:
            release.date_first = release.date_str
        release.date_str = None

    return render(request, 'calendar.html', {
            'releases': releases,
            'next_date': next_date,
            'next_offset': next_offset})

@cache_control(max_age=24*60*60)
def cover(request):
    mbid = request.GET.get('id', '')
    cover = Cover(mbid)
    if not cover.found:
        Job.get_cover(mbid)
        return HttpResponseNotFound(content=cover.image, content_type='image/jpeg')
    return HttpResponse(content=cover.image, content_type='image/jpeg')

@login_required
def delete(request):
    if request.POST.get('confirm', '') == '1':
        profile = request.user.get_profile()
        logout(request)
        profile.purge()
        return redirect('/')

    return render(request, 'delete.html')

def feed(request):
    user_id = request.GET.get('id', '')
    if user_id.isdigit():
        profile = UserProfile.get_by_legacy_id(user_id)
        if profile:
            return redirect('/feed?id=' + profile.user.username, permanent=True)

    profile = UserProfile.get_by_username(user_id)
    if not profile:
        return HttpResponseNotFound()

    LIMIT = 40
    releases = list(ReleaseGroup.get(user=profile.user, limit=LIMIT, offset=0, feed=True))
    date_iso8601 = None
    if releases:
        date_iso8601 = max(r.date_iso8601 for r in releases)

    return render(request, 'feed.xml', {
            'releases': releases,
            'date_iso8601': date_iso8601,
            'url': request.build_absolute_uri(),
            'root': request.build_absolute_uri('/')
            }, content_type='application/atom+xml')

def ical(request):
    user_id = request.GET.get('id', '')
    profile = UserProfile.get_by_username(user_id)
    if not profile:
        return HttpResponseNotFound()

    LIMIT = 40
    releases = list(ReleaseGroup.get(user=profile.user, limit=LIMIT, offset=0, feed=True))

    release_events = []

    for r in releases:
        event = {}
        event['summary'] = "{} - {}".format(r.artist.name, r.name)

        year = r.date // 10000

        # month/day aren't always present.
        month = (r.date // 100) % 100
        if month == 0:
            continue

        day = r.date % 100
        if day == 0:
            # arbitrarily set the release as the last day of the month.
            # hopefully, the date will be clarified before then, but this
            # will ensure it's not missed on the calendar.
            day = monthrange(year, month)[1]

        event_date = date(year, month, day)
        event['date_start_str'] = event_date.strftime('%Y%m%d')
        event['date_end_str'] = (event_date + timedelta(days=1)).strftime('%Y%m%d')

        # uid must be globally unique.
        # this approximates the recommended format on the spec.
        # the uid is important: it's used to sync events if changes are made.
        event['uid'] = "%s-%s@muspy.com" % (r.id, user_id)

        release_events.append(event)

    ical_str = render_to_string('ical.ical', {
        'company': 'Muspy',
        'title': 'Muspy releases',
        'release_events': release_events,
    })

    # ical spec declares \r\n newlines
    return HttpResponse(ical_str.replace('\n', '\r\n'),
                        content_type='text/calendar')

def forbidden(request):
    return HttpResponseForbidden()

@login_required
def import_artists(request):
    if request.method == 'GET':
        return render(request, 'import.html')

    type = request.POST.get('type', '')
    if type == 'last.fm':
        username = request.POST.get('username', '')
        if not username:
            messages.error(request, 'Please enter your Last.fm user name.')
            return redirect('/import')
        if Job.has_import_lastfm(request.user) or Job.importing_artists(request.user):
            messages.error(
                request, 'You already have a pending import. Please wait until '
                'the import finishes before importing again. '
                'Refresh this page to track the progress.')
            return redirect('/artists')
        if not lastfm.has_user(username):
            messages.error(request, 'Unknown user: %s' % username)
            return redirect('/import')

        count = request.POST.get('count', '')
        count = int(count) if count.isdigit() else 50
        count = min(500, count)
        period = request.POST.get('period', '')
        if period not in ['overall', '12month', '6month', '3month', '7day']:
            period = 'overall'
        Job.import_lastfm(request.user, username, count, period)
        messages.info(
            request, 'Your artists will be imported in a few minutes. '
            'Refresh this page to track the progress of the import.')
        return redirect('/artists')

    return redirect('/import')

def index(request):
    today = int(date.today().strftime('%Y%m%d'))
    releases = ReleaseGroup.get_calendar(today, 5, 0)
    return render(request, 'index.html', {'is_index': True, 'releases': releases})

@login_required
def releases(request):
    PER_PAGE = 10
    limit = PER_PAGE + 1
    offset = int(request.GET.get('offset', 0))
    release_groups = list(ReleaseGroup.get(user=request.user, limit=limit, offset=offset))
    offset = offset + PER_PAGE if len(release_groups) > PER_PAGE else None

    return render(request, 'releases.html', {
            'release_groups': release_groups[:PER_PAGE],
            'offset': offset,
            'PER_PAGE': PER_PAGE,
            'next': next,
            'show_stars': True})

def reset(request):
    form = code = user = None
    if request.method == 'POST':
        form = ResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            profile = UserProfile.get_by_email(email)
            if not profile:
                messages.error(request, 'Unknown email address: ' + email)
                return redirect('/')
            profile.send_reset_email()
            messages.success(
                request, 'An email has been sent to %s describing how to '
                'obtain your new password.' % email)
            return redirect('/')
    elif 'code' in request.GET:
        code = request.GET['code']
        email, password = UserProfile.reset(code)
        if email and password:
            user = authenticate(username=email, password=password)
            if user:
                login(request, user)
                return redirect('/settings')
    else:
        form = ResetForm()

    return render(request, 'reset.html', {'form': form, 'code': code, 'user': user})

@login_required
def settings(request):
    if request.method == 'POST':
        form = SettingsForm(request.POST)
        form.profile = request.user.get_profile()
        if form.is_valid():
            form.save()
            messages.success(request, 'Your settings have been saved.')
            return redirect(request.path)
    else:
        initial = {
            'email': request.user.email,
            'notify': request.user.get_profile().notify,
            'notify_album': request.user.get_profile().notify_album,
            'notify_single': request.user.get_profile().notify_single,
            'notify_ep': request.user.get_profile().notify_ep,
            'notify_live': request.user.get_profile().notify_live,
            'notify_compilation': request.user.get_profile().notify_compilation,
            'notify_remix': request.user.get_profile().notify_remix,
            'notify_other': request.user.get_profile().notify_other,
        }
        form = SettingsForm(initial=initial)

    return render(request, 'settings.html', {'form': form})

def signup(request):
    form = SignUpForm(request.POST or None)
    if form.is_valid():
        form.save(request)
        user = authenticate(
            username=form.cleaned_data['email'],
            password=form.cleaned_data['password'])
        user.get_profile().send_activation_email()
        login(request, user)
        return redirect(LOGIN_REDIRECT_URL)

    return render(request, 'signup.html', {'form': form})

@login_required
def signout(request):
    logout(request)
    return redirect('/')

def sitemap(request):
    root = request.build_absolute_uri('/')
    return render(request, 'sitemap.xml', {'root': root}, content_type='text/xml')

@login_required
def star(request):
    id = request.REQUEST.get('id', '').lower()
    value = int(request.REQUEST.get('value', 0))
    Star.set(request.user, id, value)
    if request.method == 'POST':
        return HttpResponse('{}', 'application/json')
    return redirect(request.META.get('HTTP_REFERER', '/'))

def unsubscribe(request):
    username = request.GET.get('id', '')
    profile = UserProfile.get_by_username(username) if username else None
    if not profile:
        messages.error(request, 'Bad request, you were not unsubscribed.')
        return redirect('/')
    profile.unsubscribe()
    messages.success(
        request, 'You have successfully unsubscribed from release notifications. '
        'If you change your mind, you can subscribe to notifications on the Settings page.')
    return redirect('/')
