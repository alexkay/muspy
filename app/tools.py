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

def arrange_for_table(items, columns):
    """Prepare a list of items to show it in a table.

    Sort the items by columns, fill by rows. Return a list of rows.

    The algorithm is a bit tricky to allow for example this:
    |0 2 3| instead of |0 2 .|
    |1 . .|            |1 3 .|

    """
    L = len(items)
    N = columns
    M = 1 + (L - 1) // N
    return [[items[i + j * M -
                   # Next line compensates for empty cells in the last row.
                   max(0, j - L % N  if i < M - 1 and L % N else 0)]
             if i * N + j < L else None
             for j in xrange(N)]
            for i in xrange(M)]

def str_to_date(date_str):
    """ Convert a date string into int

    '2010-01-02' -> 20100102
    '2010-01'    -> 20100100
    '2010'       -> 20100000

    """
    date = 0
    if not date_str:
        return date
    year = date_str[0:4]
    if not year.isdigit():
        return date
    date += int(year) * 10000
    month = date_str[5:7]
    if not month.isdigit():
        return date
    date += int(month)
    day = date_str[8:10]
    if not day.isdigit():
        return date
    date += int(day)
    return date

def date_to_str(date):
    """ Reverse of str_to_date() """

    year = date // 10000
    month = (date // 100) % 100
    day = date % 100
    date_str = str(year)
    if month:
        date_str += '-%02d' % month
        if day:
            date_str += '-%02d'% day
    return date_str

def date_to_iso8601(date):
    """ Int date to ISO 8601 string

    20100203 -> 2010-02-03T00:00:00Z
    20100200 -> 2010-02-01T00:00:00Z
    20100000 -> 2010-01-01T00:00:00Z

    """
    year = date // 10000
    month = (date // 100) % 100
    day = date % 100
    return "%04d-%02d-%02dT00:00:00Z" % (year, month or 1, day or 1)

def check_password(user, password):
    # Legacy users have their passwords hashed with SHA512.
    # TODO: Remove when Django supports SHA512 (1.4?)
    if user.password.startswith('sha512$'):
        import hashlib
        from django.utils.crypto import constant_time_compare
        from django.utils.encoding import smart_str
        algo, salt, hsh = user.password.split('$')
        password, salt = smart_str(password), smart_str(salt)
        hash = hashlib.new('sha512')
        hash.update(password)
        hash.update(salt)
        hexdigest = hash.hexdigest()
        return constant_time_compare(hsh, hexdigest)
    return user.check_password(password)
