import uuid

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django import forms


class ResetForm(forms.Form):
    email = forms.EmailField(label='E-mail', required=True)

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if not User.find(email):
            raise forms.ValidationError('Unknown e-mail address. '
                                        'Please enter another.')
        return email

class SettingsForm(forms.Form):
    email = forms.EmailField(label='New e-mail')
    password = forms.CharField(label='Current password', max_length=100,
                               required=False,
                               widget=forms.PasswordInput(render_value=False))
    new_password = forms.CharField(label='New password', max_length=100,
                                   required=False,
                                   widget=forms.PasswordInput(render_value=False))
    notify = forms.BooleanField(label='Receive new release notifications '
                                'by e-mail.', required=False)
    notify_album = forms.BooleanField(label='Album', required=False)
    notify_single = forms.BooleanField(label='Single', required=False)
    notify_ep = forms.BooleanField(label='EP', required=False)
    notify_live = forms.BooleanField(label='Live', required=False)
    notify_compilation = forms.BooleanField(label='Compilation', required=False)
    notify_remix = forms.BooleanField(label='Remix', required=False)
    notify_other = forms.BooleanField(label='Other', required=False)

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if self.user.email != email and User.find(email):
            raise forms.ValidationError('This e-mail is already in use. '
                                        'Please enter another.')
        return email

    def clean_password(self):
        password = self.cleaned_data['password']
        if password and not self.user.check_password(password):
            raise forms.ValidationError('Invalid password, try again.')
        if self.data['new_password'] and not password:
            raise forms.ValidationError('Enter the current password.')
        return password

    def save(self):
        messages = []
        if self.user.email != self.cleaned_data['email']:
            self.user.email = self.cleaned_data['email']
            self.user.email_activated = False
            self.user.put()
            self.user.send_activation_email()
            messages += 'An activation e-mail has been sent to ' + self.user.email
        self.user.changed = False
        if self.cleaned_data['new_password']:
            self.user.set_password(self.cleaned_data['new_password'])
            self.user.changed = True
            messages += 'Successfully changed the password.'
        if self.user.notify != self.cleaned_data['notify']:
            self.user.notify = self.cleaned_data['notify']
            self.user.changed = True
            messages += ('E-mail notifications turned %s.' %
                         ('ON' if self.user.notify else 'OFF'))

        self.user.notification_changed = False
        if self.user.notify_album != self.cleaned_data['notify_album']:
            self.user.notify_album = self.cleaned_data['notify_album']
            self.user.notification_changed = True
        if self.user.notify_single != self.cleaned_data['notify_single']:
            self.user.notify_single = self.cleaned_data['notify_single']
            self.user.notification_changed = True
        if self.user.notify_ep != self.cleaned_data['notify_ep']:
            self.user.notify_ep = self.cleaned_data['notify_ep']
            self.user.notification_changed = True
        if self.user.notify_live != self.cleaned_data['notify_live']:
            self.user.notify_live = self.cleaned_data['notify_live']
            self.user.notification_changed = True
        if self.user.notify_compilation != self.cleaned_data['notify_compilation']:
            self.user.notify_compilation = self.cleaned_data['notify_compilation']
            self.user.notification_changed = True
        if self.user.notify_remix != self.cleaned_data['notify_remix']:
            self.user.notify_remix = self.cleaned_data['notify_remix']
            self.user.notification_changed = True
        if self.user.notify_other != self.cleaned_data['notify_other']:
            self.user.notify_other = self.cleaned_data['notify_other']
            self.user.notification_changed = True
        if self.user.changed or self.user.notification_changed:
            self.user.put()
        if self.user.notification_changed:
            Job.update_releases(self.user.key().id())
        return messages

class SignInForm(AuthenticationForm):

    username = forms.CharField(label='Email', max_length=75)

class SignUpForm(forms.Form):

    email = forms.EmailField(widget=forms.TextInput(attrs={'maxlength':75}), label='Email')
    password = forms.CharField(widget=forms.PasswordInput(render_value=False), label='Password')

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if User.objects.filter(email__iexact=email):
            raise forms.ValidationError('This email address is already in use. Please supply a different email address.')
        return email

    def save(self, request):
        login = uuid.uuid4().hex[:30]
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']
        user = User.objects.create_user(login, email, password)

        return user
