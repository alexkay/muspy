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

from django.conf.urls.defaults import *
from django.contrib.auth.views import login
from django.views.generic.simple import redirect_to

from app.forms import SignInForm

urlpatterns = patterns('app.views',
    (r'^$', 'index'),
    (r'^activate$', 'activate'),
    (r'^artist/([0-9a-f\-]+)$', 'artist'),
    (r'^artists$', 'artists'),
    (r'^artists-add$', 'artists_add'),
    (r'^artists-remove$', 'artists_remove'),
    (r'^blog$', 'blog'),
    (r'^blog/feed$', 'blog_feed'),
#    (r'^calendar$', 'calendar'),
#    (r'^cover$', 'cover'),
#    (r'^daemon$', 'daemon'),
#    (r'^feed$', 'feed'),
#    (r'^feed/(?P<id>\d+)$', redirect_to, {'url': '/feed?id=%(id)s'}),
#    (r'^import$', 'import_artists'),
#    (r'^releases$', 'releases'),
    (r'^reset$', 'reset'),
    (r'^settings$', 'settings'),
    (r'^signin$', login, {'authentication_form': SignInForm, 'template_name': 'signin.html'}),
    (r'^signout$', 'signout'),
    (r'^signup$', 'signup'),
#    (r'^sitemap.xml$', 'sitemap'),
#    (r'^star$', 'star'),
#    (r'^test$', 'test'),
    # Try to map other URLs to blog articles.
    (r'^([a-z\-\.]+)$', 'article'),
)
