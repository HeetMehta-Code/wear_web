from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied

def allowed_users(allowed_roles=[]):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            # Check if user is logged in
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Check if user role matches allowed roles
            if request.user.role in allowed_roles or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                raise PermissionDenied
        return wrapper_func
    return decorator