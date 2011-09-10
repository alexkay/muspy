from django.contrib.auth.models import User
from django.db import models

User.__unicode__ = lambda x: x.email
