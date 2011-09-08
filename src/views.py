from datetime import date

from django.shortcuts import render_to_response

def index(request):
    today = int(date.today().strftime('%Y%m%d'))
    releases = None
    # TODO: releases = Release.get_calendar(today, 5, None)
    return render_to_response('index.html', {'is_index': True, 'releases': releases})
