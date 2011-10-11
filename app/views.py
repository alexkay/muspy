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
from time import sleep

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect, render

from settings import LOGIN_REDIRECT_URL

from app.blog import articles, get_posts
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

def article(request, slug):
    if not slug in articles:
        return HttpResponseNotFound()
    article = articles[slug]
    is_blog = 'date' in article
    if is_blog:
        template_name = 'articles/%s-%s.html' % (article['date'], slug)
    else:
        template_name = 'articles/%s.html' % slug
    root =  request.build_absolute_uri('/')
    return render(request, 'article.html', {'slug': slug, 'article': article,
                                            'is_blog': is_blog, 'root': root,
                                            'template_name': template_name})

def artist(request, mbid):
    artist = Artist.get_by_mbid(mbid)
    if not artist:
        artist_data = mb.get_artist(mbid)
        if not artist_data:
            # TODO: Show a meaningful error message.
            return HttpResponseNotFound()

        # Sleep 1s to comply with the MB web service.
        sleep(1)

        artist = Artist(
            mbid=mbid, name=artist_data['name'], sort_name=artist_data['sort-name'],
            disambiguation=artist_data['disambiguation'] if 'disambiguation' in artist_data else '')
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
                            date=ReleaseGroup.parse_date(rg_data['first-release-date']),
                            is_deleted=False)
                        release_group.save()

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
        release_groups = ReleaseGroup.get_release_groups(mbid, PER_PAGE, offset)

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
            messages.error('The search string is too long.')
            return redirect('/artists')

        if ',' in search and not offset:
            # Batch add mode.
            Job.add_artists(request.user.key().id(), search, dontadd)
            messages.info('Your artists will be processed in the next couple of '
                          'minutes. In the meantime you can add more artists.')
            return redirect('/artists')

        found_artists, count = mb.search_artists(search, limit=LIMIT, offset=offset)
        if found_artists is None:
            messages.error('The search server could not fulfill your request '
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
            artist = Artist.find(mbid)
            if not artist:
                artist = Artist.add(mbid, artist_data['name'], artist_data['sort-name'])
                Job.add_releases(mbid)

            UserArtist.add(request.user, artist)
            Job.copy_releases(mbid, request.user.key().id())

            message.success("%s has been added!" % artist.name)
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

def blog(request):
    posts = get_posts()
    root =  request.build_absolute_uri('/')
    return render(request, 'blog.html', {'posts': posts, 'root': root})

def blog_feed(request):
    posts = get_posts()
    feed = render_to_string('blog_feed.xml',
                            {'posts': posts,
                             'updated_feed': max(p['updated'] for p in posts),
                             'url': request.build_absolute_uri(),
                             'root': request.build_absolute_uri('/')})
    return HttpResponse(content=feed, content_type='application/atom+xml')

def index(request):
    today = int(date.today().strftime('%Y%m%d'))
    releases = None
    # TODO: releases = Release.get_calendar(today, 5, None)
    return render(request, 'index.html', {'is_index': True, 'releases': releases})

def reset(request):
    form = resetting = password = None
    if request.method == 'POST':
        form = ResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            profile = UserProfile.find(email)
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
