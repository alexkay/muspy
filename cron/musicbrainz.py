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

from app.models import *
