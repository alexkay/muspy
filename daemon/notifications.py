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
import logging

from app.models import *
from daemon import jobs, tools


def send():
    sent_emails = 0
    sleep = True
    while True:
        if sleep:
            jobs.process()
            tools.sleep()
            sleep = False
        try:
            notification = Notification.objects.order_by('-user')[0]
        except IndexError:
            break # last one

        with transaction.commit_on_success():
            user = notification.user
            profile = user.get_profile()
            if profile.notify and profile.email_activated:
                types = profile.get_types()
                rg = notification.release_group
                if rg.type in types and is_recent(rg.date):
                    sleep = True
                    result = user.get_profile().send_email(
                        subject='[muspy] New Release: %s - %s' % (rg.artist.name, rg.name),
                        text_template='email/release.txt',
                        html_template='email/release.html',
                        release=rg,
                        username=user.username,
                        root='https://muspy.com/')
                    if not result:
                        logging.warning('Could not send to user %d, retrying' % user.id)
                        continue
                    sent_emails += 1
                    logging.info('Sent a notification to user %d' % user.id)

            notification.delete()

    logging.info('Sent %d email notifications' % sent_emails)


def is_recent(date):
    """Check if the integer date is not older than one year."""
    date = datetime(
        year=date // 10000,
        month=(date // 100) % 100 or 1,
        day=date % 100 or 1)
    one_year = timedelta(weeks=52)
    return date > datetime.utcnow() - one_year
