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

from django.contrib.auth.backends import ModelBackend
from django.contrib.admin.models import User

from app.tools import check_password


class EmailAuthBackend(ModelBackend):

    def authenticate(self, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=username)
            return user if check_password(user, password) else None
        except User.DoesNotExist:
            return None
