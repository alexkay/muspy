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

from datetime import datetime, timedelta
import time


def sleep():
    """Sleep to avoid clogging up MusicBrainz servers.

    Call it before each MB request.

    """
    DELAY = 2 # seconds
    duration = time.time() - sleep.start
    if DELAY - duration > 0:
        time.sleep(DELAY - duration)
    sleep.start = time.time()

sleep.start = time.time()
