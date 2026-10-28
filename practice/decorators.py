from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache


def login_required_no_cache(view_func):
    """Combines Django's login_required with never_cache.

    Without never_cache, a browser can serve a protected page (e.g.
    /students/) straight from its back/forward cache after logout,
    without asking the server again — so pressing the Back button can
    briefly show stale authenticated content until the page is
    manually reloaded. never_cache sends
    'Cache-Control: no-store' (among other headers) on the response,
    which tells the browser never to cache this page at all, so Back
    always triggers a fresh request and correctly lands on /login/.
    """

    @wraps(view_func)
    @never_cache
    @login_required(login_url="login")
    def _wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def role_required(*allowed_roles):
    """View decorator restricting access to users whose Profile.role is
    one of ``allowed_roles``. Superusers are always allowed through
    (they can still use /admin/ regardless of their Profile.role).

    Also applies never_cache (see login_required_no_cache above) so
    these protected pages are never served from the browser's
    back/forward cache after logout.

    Usage:
        @role_required("admin", "teacher")
        def add_student(request):
            ...
    """

    def decorator(view_func):

        @wraps(view_func)
        @never_cache
        @login_required(login_url="login")
        def _wrapped_view(request, *args, **kwargs):

            profile = getattr(request.user, "profile", None)

            if request.user.is_superuser or (
                profile is not None and profile.role in allowed_roles
            ):
                return view_func(request, *args, **kwargs)

            messages.error(
                request,
                "You don't have permission to access that page for your account type."
            )

            return redirect("students")

        return _wrapped_view

    return decorator
