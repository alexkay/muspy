from datetime import date

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from settings import LOGIN_REDIRECT_URL

from app.forms import *
from app.models import *

def activate(request):
    if 'code' in request.GET:
        if UserProfile.activate(request.GET['code']):
            messages.success(request, 'Your email address has been activated.')
        else:
            messages.error(request, 'Invalid activation code, your email address was not activated.')
        return redirect('/')

    if not request.user.is_authenticated():
        messages.error(request, 'You need to sign in to activate your email address.')
        return redirect('/')

    if request.user.get_profile().email_activated:
        messages.info(request, 'Your email address is already active.')
        return redirect('/')

    request.user.get_profile().send_activation_email()
    return render(request, 'activate.html')

def index(request):
    today = int(date.today().strftime('%Y%m%d'))
    releases = None
    # TODO: releases = Release.get_calendar(today, 5, None)
    return render(request, 'index.html', {'is_index': True, 'releases': releases})

def reset(request):
    form = resetting = password = None
    if request.method == 'POST':
        form = ResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            profile = UserProfile.find(email)
            if not profile:
                messages.error(request, 'Unknown email address: ' + email)
                return redirect('/')
            profile.send_reset_email()
            messages.success(request,
                             'An email has been sent to %s describing how to '
                             'obtain your new password.' % email)
            return redirect('/')
    elif 'code' in request.GET:
        code = request.GET['code']
        resetting = True
        email, password = UserProfile.reset(code)
        if email and password:
            # Sign in immediately.
            user = authenticate(username=email, password=password)
            login(request, user)
            return redirect(LOGIN_REDIRECT_URL)
    else:
        form = ResetForm()

    return render(request, 'reset.html', {'form': form, 'resetting': resetting, 'password': password})

@login_required
def settings(request):
    if request.method == 'POST':
        form = SettingsForm(request.POST)
        form.profile = request.user.get_profile()
        if form.is_valid():
            form.save()
            messages.success(request, 'Your settings have been saved.')
            return redirect('/')
    else:
        initial = {
            'email': request.user.email,
            'notify': request.user.get_profile().notify,
            'notify_album': request.user.get_profile().notify_album,
            'notify_single': request.user.get_profile().notify_single,
            'notify_ep': request.user.get_profile().notify_ep,
            'notify_live': request.user.get_profile().notify_live,
            'notify_compilation': request.user.get_profile().notify_compilation,
            'notify_remix': request.user.get_profile().notify_remix,
            'notify_other': request.user.get_profile().notify_other,
        }
        form = SettingsForm(initial=initial)

    return render(request, 'settings.html', {'form': form})

def signup(request):

    form = SignUpForm(request.POST or None)
    if form.is_valid():
        form.save(request)
        user = authenticate(username=request.POST['email'], password=request.POST['password'])
        user.get_profile().send_activation_email()
        login(request, user)
        return redirect(LOGIN_REDIRECT_URL)

    return render(request, 'signup.html', {'form': form})

@login_required
def signout(request):
    logout(request)
    return redirect('/')
