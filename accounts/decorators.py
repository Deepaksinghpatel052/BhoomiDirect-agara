from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


def staff_required(view_func):
    """Company staff only (admin, evaluator, field agent or superuser)."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not request.user.is_company_staff:
            raise PermissionDenied("Staff access only.")
        return view_func(request, *args, **kwargs)

    return _wrapped


def role_required(*roles):
    """Restrict a view to specific roles. Superusers always pass."""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not request.user.has_any_role(*roles):
                raise PermissionDenied("Your role does not have permission for this action.")
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
