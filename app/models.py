import random

from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.db.backends.signals import connection_created
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string

@receiver(connection_created)
def activate_foreign_keys(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA foreign_keys=1;')

@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    if created:
        p = UserProfile()
        p.user = instance
        p.save()

User.__unicode__ = lambda x: x.email

class UserProfile(models.Model):

    code_length = 16

    user = models.OneToOneField(User)

    notify = models.BooleanField(default=True)
    notify_album = models.BooleanField(default=True)
    notify_single = models.BooleanField(default=True)
    notify_ep = models.BooleanField(default=True)
    notify_live = models.BooleanField(default=True)
    notify_compilation = models.BooleanField(default=True)
    notify_remix = models.BooleanField(default=True)
    notify_other = models.BooleanField(default=True)
    email_activated = models.BooleanField(default=False)
    activation_code = models.CharField(max_length=code_length)
    reset_code = models.CharField(max_length=code_length)

    def generate_code(self):
        code_chars = '23456789abcdefghijkmnpqrstuvwxyz'
        return ''.join(random.choice(code_chars) for i in xrange(UserProfile.code_length))

    def send_email(self, subject, text_template, html_template, **kwds):
        sender = 'info@muspy.com'
        text = render_to_string(text_template, kwds)
        msg = EmailMultiAlternatives(subject, text, sender, [self.user.email])
        if html_template:
            html = render_to_string(html_template, kwds)
            msg.attach_alternative(html_content, "text/html")
        msg.send()

    def send_activation_email(self):
        code = self.generate_code()
        self.activation_code = code
        self.save()
        self.send_email(subject='Email Activation',
                        text_template='email/activate.txt',
                        html_template=None,
                        code=code)

    def send_reset_email(self):
        code = self.generate_code()
        self.reset_code = code
        self.save()
        self.send_email(subject='Password Reset Confirmation',
                        text_template='email/reset.txt',
                        html_template=None,
                        code=code)

    @classmethod
    def activate(cls, code):
        profiles = UserProfile.objects.filter(activation_code__exact=code)
        if not profiles:
            return False
        profile = profiles[0]
        profile.activation_code = ''
        profile.email_activated = True
        profile.save()
        return True

    @classmethod
    def reset(cls, code):
        users = User.objects.filter(reset_code__exact=code)
        if not users:
            return None, None
        profile = users[0].get_profile()
        password = profile.user.objects.make_random_password(length=16)
        profile.reset_code = ''
        profile.user.set_password(password)
        # TODO: transaction
        profile.user.save()
        profile.save()
        return profile.user.email, password

    @classmethod
    def find(cls, email):
        users = User.objects.filter(email__exact=email)
        return users[0].get_profile() if users else None
