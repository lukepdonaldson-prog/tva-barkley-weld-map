import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST


def _superuser_required(view_func):
    """Decorator: requires the user to be logged in AND a superuser (403 otherwise)."""
    from functools import wraps
    from django.http import HttpResponseForbidden

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.conf import settings
            from django.shortcuts import redirect
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        if not request.user.is_superuser:
            return HttpResponseForbidden("You do not have permission to access this page.")
        return view_func(request, *args, **kwargs)

    return _wrapped


def _user_to_dict(u):
    """Serialize a User instance to a plain dict for JSON responses."""
    _DATETIME_FORMAT = '%Y-%m-%d %H:%M'
    last_login = u.last_login.strftime(_DATETIME_FORMAT) if u.last_login else ''
    date_joined = u.date_joined.strftime(_DATETIME_FORMAT) if u.date_joined else ''
    if u.is_superuser:
        role = 'superuser'
    elif u.is_staff:
        role = 'staff'
    else:
        role = 'user'
    return {
        'id': u.pk,
        'username': u.username,
        'first_name': u.first_name,
        'last_name': u.last_name,
        'email': u.email,
        'role': role,
        'is_active': u.is_active,
        'last_login': last_login,
        'date_joined': date_joined,
    }


# ---------------------------------------------------------------------------
# User management list page
# ---------------------------------------------------------------------------

@_superuser_required
def user_list(request):
    users = User.objects.all().order_by('username')
    total = users.count()
    active = users.filter(is_active=True).count()
    superusers = users.filter(is_superuser=True).count()
    staff = users.filter(is_staff=True, is_superuser=False).count()
    return render(request, 'welds/user_management.html', {
        'users': users,
        'total': total,
        'active': active,
        'superusers': superusers,
        'staff': staff,
    })


# ---------------------------------------------------------------------------
# Create user (AJAX POST)
# ---------------------------------------------------------------------------

@_superuser_required
@require_POST
def user_create(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    username = data.get('username', '').strip()
    password = data.get('password', '')
    confirm = data.get('confirm_password', '')
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    email = data.get('email', '').strip()
    role = data.get('role', 'user')
    is_active = bool(data.get('is_active', True))

    if not username:
        return JsonResponse({'success': False, 'error': 'Username is required.'}, status=400)
    if not password:
        return JsonResponse({'success': False, 'error': 'Password is required.'}, status=400)
    if len(password) < 8:
        return JsonResponse({'success': False, 'error': 'Password must be at least 8 characters.'}, status=400)
    if password != confirm:
        return JsonResponse({'success': False, 'error': 'Passwords do not match.'}, status=400)
    if User.objects.filter(username=username).exists():
        return JsonResponse({'success': False, 'error': f'Username "{username}" already exists.'}, status=400)

    user = User.objects.create_user(
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name,
        email=email,
        is_active=is_active,
    )
    if role == 'superuser':
        user.is_superuser = True
        user.is_staff = True
    elif role == 'staff':
        user.is_superuser = False
        user.is_staff = True
    else:
        user.is_superuser = False
        user.is_staff = False
    user.save()

    return JsonResponse({'success': True, 'user': _user_to_dict(user)})


# ---------------------------------------------------------------------------
# Update user (AJAX POST)
# ---------------------------------------------------------------------------

@_superuser_required
@require_POST
def user_update(request, pk):
    user = User.objects.filter(pk=pk).first()
    if user is None:
        return JsonResponse({'success': False, 'error': 'User not found.'}, status=404)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    username = data.get('username', '').strip()
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    email = data.get('email', '').strip()
    role = data.get('role', 'user')
    is_active = bool(data.get('is_active', True))
    password = data.get('password', '')
    confirm = data.get('confirm_password', '')

    if not username:
        return JsonResponse({'success': False, 'error': 'Username is required.'}, status=400)
    if User.objects.filter(username=username).exclude(pk=pk).exists():
        return JsonResponse({'success': False, 'error': f'Username "{username}" already exists.'}, status=400)

    # Prevent self-lockout
    if user.pk == request.user.pk:
        if not is_active:
            return JsonResponse({'success': False, 'error': 'You cannot deactivate your own account.'}, status=400)
        if role != 'superuser':
            return JsonResponse({'success': False, 'error': 'You cannot remove your own superuser status.'}, status=400)

    if password:
        if len(password) < 8:
            return JsonResponse({'success': False, 'error': 'Password must be at least 8 characters.'}, status=400)
        if password != confirm:
            return JsonResponse({'success': False, 'error': 'Passwords do not match.'}, status=400)
        user.set_password(password)

    user.username = username
    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    user.is_active = is_active

    if role == 'superuser':
        user.is_superuser = True
        user.is_staff = True
    elif role == 'staff':
        user.is_superuser = False
        user.is_staff = True
    else:
        user.is_superuser = False
        user.is_staff = False

    user.save()
    return JsonResponse({'success': True, 'user': _user_to_dict(user)})


# ---------------------------------------------------------------------------
# Delete user (AJAX POST)
# ---------------------------------------------------------------------------

@_superuser_required
@require_POST
def user_delete(request, pk):
    user = User.objects.filter(pk=pk).first()
    if user is None:
        return JsonResponse({'success': False, 'error': 'User not found.'}, status=404)

    if user.pk == request.user.pk:
        return JsonResponse({'success': False, 'error': 'You cannot delete your own account.'}, status=400)

    if user.is_superuser:
        superuser_count = User.objects.filter(is_superuser=True).count()
        if superuser_count <= 1:
            return JsonResponse(
                {'success': False, 'error': 'Cannot delete the last superuser account.'},
                status=400,
            )

    user.delete()
    return JsonResponse({'success': True})


# ---------------------------------------------------------------------------
# Reset password (AJAX POST)
# ---------------------------------------------------------------------------

@_superuser_required
@require_POST
def user_reset_password(request, pk):
    user = User.objects.filter(pk=pk).first()
    if user is None:
        return JsonResponse({'success': False, 'error': 'User not found.'}, status=404)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    password = data.get('password', '')
    confirm = data.get('confirm_password', '')

    if not password:
        return JsonResponse({'success': False, 'error': 'Password is required.'}, status=400)
    if len(password) < 8:
        return JsonResponse({'success': False, 'error': 'Password must be at least 8 characters.'}, status=400)
    if password != confirm:
        return JsonResponse({'success': False, 'error': 'Passwords do not match.'}, status=400)

    user.set_password(password)
    user.save()
    return JsonResponse({'success': True})
