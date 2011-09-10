from django.contrib.auth.models import User
from django.db import models
from django.db.backends.signals import connection_created
from django.dispatch import receiver

@receiver(connection_created)
def activate_foreign_keys(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA foreign_keys=1;')

User.__unicode__ = lambda x: x.email
