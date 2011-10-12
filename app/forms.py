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

import uuid

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User

from app.models import *


class ResetForm(forms.Form):
    email = forms.EmailField(label='Email', required=True)

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if not UserProfile.get_by_email(email):
            raise forms.ValidationError('Unknown email address. '
                                        'Please enter another.')
        return email

class SettingsForm(forms.Form):
    email = forms.EmailField(label='New email')
    password = forms.CharField(label='Current password', max_length=100,
                               required=False,
                               widget=forms.PasswordInput(render_value=False))
    new_password = forms.CharField(label='New password', max_length=100,
                                   required=False,
                                   widget=forms.PasswordInput(render_value=False))
    notify = forms.BooleanField(label='Receive new release notifications '
                                'by email.', required=False)
    notify_album = forms.BooleanField(label='Album', required=False)
    notify_single = forms.BooleanField(label='Single', required=False)
    notify_ep = forms.BooleanField(label='EP', required=False)
    notify_live = forms.BooleanField(label='Live', required=False)
    notify_compilation = forms.BooleanField(label='Compilation', required=False)
    notify_remix = forms.BooleanField(label='Remix', required=False)
    notify_other = forms.BooleanField(label='Other', required=False)

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if self.profile.user.email != email and  User.objects.filter(email=email):
            raise forms.ValidationError('This email is already in use. '
                                        'Please enter another.')
        return email

    def clean_password(self):
        password = self.cleaned_data['password']
        if password and not self.profile.user.check_password(password):
            raise forms.ValidationError('Invalid password, try again.')
        if self.data['new_password'] and not password:
            raise forms.ValidationError('Enter the current password.')
        return password

    def save(self):
        if self.profile.user.email != self.cleaned_data['email']:
            self.profile.user.email = self.cleaned_data['email']
            self.profile.email_activated = False
            # TODO: transaction
            self.profile.user.save()
            self.profile.save()
            self.profile.send_activation_email()
        changed = False
        if self.cleaned_data['new_password']:
            self.profile.user.set_password(self.cleaned_data['new_password'])
            self.profile.user.save()
        if self.profile.notify != self.cleaned_data['notify']:
            self.profile.notify = self.cleaned_data['notify']
            changed = True
        if self.profile.notify_album != self.cleaned_data['notify_album']:
            self.profile.notify_album = self.cleaned_data['notify_album']
            changed = True
        if self.profile.notify_single != self.cleaned_data['notify_single']:
            self.profile.notify_single = self.cleaned_data['notify_single']
            changed = True
        if self.profile.notify_ep != self.cleaned_data['notify_ep']:
            self.profile.notify_ep = self.cleaned_data['notify_ep']
            changed = True
        if self.profile.notify_live != self.cleaned_data['notify_live']:
            self.profile.notify_live = self.cleaned_data['notify_live']
            changed = True
        if self.profile.notify_compilation != self.cleaned_data['notify_compilation']:
            self.profile.notify_compilation = self.cleaned_data['notify_compilation']
            changed = True
        if self.profile.notify_remix != self.cleaned_data['notify_remix']:
            self.profile.notify_remix = self.cleaned_data['notify_remix']
            changed = True
        if self.profile.notify_other != self.cleaned_data['notify_other']:
            self.profile.notify_other = self.cleaned_data['notify_other']
            changed = True
        if changed:
            self.profile.save()

class SignInForm(AuthenticationForm):

    username = forms.CharField(label='Email', max_length=75)

class SignUpForm(forms.Form):

    email = forms.EmailField(widget=forms.TextInput(attrs={'maxlength':75}), label='Email')
    password = forms.CharField(widget=forms.PasswordInput(render_value=False), label='Password')

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if User.objects.filter(email=email):
            raise forms.ValidationError('This email address is already in use. Please supply a different email address.')
        return email

    def save(self, request):
        login = uuid.uuid4().hex[:30]
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']
        user = User.objects.create_user(login, email, password)

        return user
