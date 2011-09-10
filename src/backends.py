from django.contrib.auth.backends import ModelBackend
from django.contrib.admin.models import User

class EmailAuthBackend(ModelBackend):

    def authenticate(self, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=username)
            if user.check_password(password):
                return user
            return None
        except User.DoesNotExist:
            return None
