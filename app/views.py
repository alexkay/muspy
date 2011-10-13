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

from datetime import date

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render

from settings import LOGIN_REDIRECT_URL

from app.forms import *
from app.models import *
import app.musicbrainz as mb
from app.tools import arrange_for_table

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
    artist = Artist.get_by_mbid(mbid)
    if not artist:
        # TODO: Show a meaningful error message.
        return HttpResponseNotFound()

    PER_PAGE = 10
    offset = int(request.GET.get('offset', 0))
    user_has_artist = False #TODO: (request.user.is_authenticated() and
                      # UserArtist.find(request.user, mbid))
    if user_has_artist:
        show_stars = True
        releases = UserRelease.get_releases(request.user, mbid,
                                            PER_PAGE, offset)
    else:
        show_stars = False
        release_groups = ReleaseGroup.get(artist=artist, limit=PER_PAGE, offset=offset)

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

        if ',' in search and not offset:
            # Batch add mode.
            Job.add_artists(request.user.key().id(), search, dontadd)
            messages.info(request, 'Your artists will be processed in the next couple of '
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
            artist = Artist.get_by_mbid(mbid)
            if not artist:
                # TODO: error message
                return redirect('/artists')

            UserArtist.add(request.user, artist)
            messages.success(request, "%s has been added!" % artist.name)
            return redirect('/artists')

    artists_offset = offset + len(found_artists)
    artists_left = max(0, count - artists_offset)

#    importing = Job.importing_artists(request.user.key().id())
#    pending = sorted(s.search for s in request.user.searches.fetch(200))
#    pending_rows = arrange_for_table(pending, COLUMNS)

    return render(request, 'artists.html', {
            'artist_rows': artist_rows,
            'search': search,
            'dontadd': dontadd,
            'found_artists': found_artists,
            'artists_offset': artists_offset,
            'artists_left': artists_left})

@login_required
def artists_add(request):
    mbid = request.GET.get('id', '').lower()
    artist = Artist.get_by_mbid(mbid)
    if not artist:
        # TODO: Show a meaningful error message.
        return HttpResponseNotFound()

    UserArtist.add(request.user, artist)

    #TODO
#    search = request.GET.get('search', '')
#    UserSearch.remove(request.user, [search])

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
    date_int = str_to_date(date_str) if date_str else today
    offset = int(request.GET.get('offset', 0))
    PER_PAGE = 4
    limit = PER_PAGE + 1
    releases = list(ReleaseGroup.get_calendar(date_int, limit, offset))

    if len(releases) == limit:
        if releases[0].date == releases[-1].date:
            next_date = date_str
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

def feed(request):
    user_id = request.GET.get('id', '')
    if user_id.isdigit():
        profile = UserProfile.get_by_legacy_id(user_id)
        if profile:
            return redirect('/feed?id=' + profile.user.username, permanent=True)

    profile = UserProfile.get_by_username(user_id)
    if not profile:
        return HttpResponseNotFound()

    LIMIT = 20
    releases = ReleaseGroup.get(user=profile.user, limit=LIMIT, offset=0)
    if releases:
        releases.date_iso8601 = min(r.date_iso8601 for r in releases)

    return render(request, 'feed.xml', {
            'releases': releases,
            'url': request.build_absolute_uri(),
            'root': request.build_absolute_uri('/')
            }, content_type='application/atom+xml')

def index(request):
    today = int(date.today().strftime('%Y%m%d'))
    releases = ReleaseGroup.get_calendar(today, 5, 0)
    return render(request, 'index.html', {'is_index': True, 'releases': releases})

def reset(request):
    form = resetting = password = None
    if request.method == 'POST':
        form = ResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            profile = UserProfile.get_by_email(email)
            if not profile:
                messages.error(request, 'Unknown email address: ' + email)
                return redirect('/')
            profile.send_reset_email()
            messages.success(request,
                             'An email has been sent to %s describing how to '
                             'obtain your new password.' % email)
            return redirect('/')
    elif 'code' in request.GET:
        code = request.GET['code']
        resetting = True
        email, password = UserProfile.reset(code)
        if email and password:
            # Sign in immediately.
            user = authenticate(username=email, password=password)
            login(request, user)
            return redirect(LOGIN_REDIRECT_URL)
    else:
        form = ResetForm()

    return render(request, 'reset.html', {'form': form, 'resetting': resetting, 'password': password})

@login_required
def settings(request):
    if request.method == 'POST':
        form = SettingsForm(request.POST)
        form.profile = request.user.get_profile()
        if form.is_valid():
            form.save()
            messages.success(request, 'Your settings have been saved.')
            return redirect('/')
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
        user = authenticate(username=request.POST['email'], password=request.POST['password'])
        user.get_profile().send_activation_email()
        login(request, user)
        return redirect(LOGIN_REDIRECT_URL)

    return render(request, 'signup.html', {'form': form})

@login_required
def signout(request):
    logout(request)
    return redirect('/')
