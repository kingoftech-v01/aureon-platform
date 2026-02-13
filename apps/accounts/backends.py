"""
Custom authentication backends for the accounts app.

Provides a backend that supports authentication via both username and email,
regardless of the USERNAME_FIELD setting on the User model.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class UsernameOrEmailBackend(ModelBackend):
    """
    Authentication backend that supports login via username or email.

    When USERNAME_FIELD is 'email', the default ModelBackend only
    accepts email for authentication. This backend also tries to
    match against the 'username' field if the initial lookup fails.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()

        # First, try the default ModelBackend behavior (uses USERNAME_FIELD)
        user = super().authenticate(request, username=username, password=password, **kwargs)
        if user is not None:
            return user

        # If that failed and USERNAME_FIELD is not 'username',
        # try looking up by username field
        if username is not None and UserModel.USERNAME_FIELD != 'username':
            try:
                user = UserModel._default_manager.get(username=username)
            except UserModel.DoesNotExist:
                return None

            if user.check_password(password) and self.user_can_authenticate(user):
                return user

        return None
