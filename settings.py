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

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('admin', 'admin@muspy.com'),
)
MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db/muspy.db',
    }
}

TIME_ZONE = None
LANGUAGE_CODE = 'en-gb'
USE_I18N = False
USE_L10N = False

MEDIA_ROOT = ''
MEDIA_URL = ''
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    'static',
)

# TODO: /releases if there are any otherwise /artists, or make it an option
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/signin'
AUTH_PROFILE_MODULE = 'app.UserProfile'
MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'
ROOT_URLCONF = 'urls'

# Change for production
SECRET_KEY = '^c)@qv0@pb$ym&zb^#vm8nuv0972qa9w(#le&atirpvfvi_yjc'
EMAIL_SUBJECT_PREFIX = '[muspy] '
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
#EMAIL_HOST_USER =
#EMAIL_HOST_PASSWORD =
#EMAIL_USE_TLS =

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
)
TEMPLATE_DIRS = (
    'templates',
)

AUTHENTICATION_BACKENDS = (
    'app.backends.EmailAuthBackend',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
