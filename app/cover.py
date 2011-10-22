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

import os
import time


class Cover(object):

    DELAY = 7 * 24 * 60 * 60 # 7 weeks

    def __init__(self, mbid):
        self._base = os.path.abspath(os.path.dirname(__file__) + '/..')
        self._default = os.path.join(self._base, 'static/cover.jpg')
        self.found = False
        if len(mbid) != 36:
            self.found = True
            self.image = self._read(self._default)
            return

        self._path = os.path.join(self._base, 'covers', mbid[0:2], mbid[2:4], mbid + '.jpg')
        if os.path.exists(self._path):
            if os.path.getsize(self._path):
                self.found = True
                self.image = self._read(self._path)
            else:
                # Empty file, check modification time
                mtime = os.path.getmtime(self._path)
                if time.time() - mtime > Cover.DELAY:
                    # Old file, delete.
                    os.remove(self._path)
                else:
                    self.found = True
            self.image = self._read(self._default)
        else:
            # Create dirs.
            dirname = os.path.dirname(self._path)
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            # Create an empty file.
            f = open(self._path, 'w+b')
            f.close()
            self.image = self._read(self._default)

    def _read(self, path):
        with open(path, 'rb') as f:
            return f.read()
