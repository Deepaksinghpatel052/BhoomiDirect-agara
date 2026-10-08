from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class PhoneEmailUsernameBackend(ModelBackend):
    """Login with username, email address or 10 digit mobile number."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(get_user_model().USERNAME_FIELD)
        if not username or not password:
            return None
        User = get_user_model()
        identifier = username.strip()
        digits = identifier.replace(" ", "").replace("+91", "")
        user = (
            User.objects.filter(
                Q(username__iexact=identifier) | Q(email__iexact=identifier) | Q(phone=digits)
            )
            .order_by("id")
            .first()
        )
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
