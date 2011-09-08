from django.conf.urls.defaults import *
from django.views.generic.simple import redirect_to

urlpatterns = patterns('src.views',
    (r'^$', 'index'),
    (r'^activate$', 'activate'),
    (r'^artist/([0-9a-f\-]+)$', 'artist'),
    (r'^artists$', 'artists'),
    (r'^artists-add$', 'artists_add'),
    (r'^artists-remove$', 'artists_remove'),
    (r'^blog$', 'blog'),
    (r'^blog/feed$', 'blog_feed'),
    (r'^calendar$', 'calendar'),
    (r'^cover$', 'cover'),
    (r'^daemon$', 'daemon'),
    (r'^feed$', 'feed'),
    (r'^feed/(?P<id>\d+)$', redirect_to, {'url': '/feed?id=%(id)s'}),
    (r'^import$', 'import_artists'),
    (r'^releases$', 'releases'),
    (r'^reset$', 'reset'),
    (r'^screencast/([a-z\-\.]+)$', 'screencast'),
    (r'^settings$', 'settings'),
    (r'^signin$', 'signin'),
    (r'^signout$', 'signout'),
    (r'^signup$', 'signup'),
    (r'^sitemap.xml$', 'sitemap'),
    (r'^star$', 'star'),
    (r'^test$', 'test'),
    # Try to map other URLs to blog articles.
    (r'^([a-z\-\.]+)$', 'article')
)
