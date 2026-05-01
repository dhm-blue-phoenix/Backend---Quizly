from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from django.contrib.auth import authenticate

def create_user(data):
    """
    Validates data and creates a new user.
    """
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    confirmed_password = data.get('confirmed_password')

    if not username or not email or not password or not confirmed_password:
        raise ValidationError({"detail": "All fields are required."})
    
    if password != confirmed_password:
        raise ValidationError({"detail": "Passwords do not match."})

    if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
        raise ValidationError({"detail": "Username or email already exists."})

    return User.objects.create_user(username=username, email=email, password=password)

def authenticate_and_get_tokens(username, password):
    """
    Authenticates user and returns access and refresh tokens.
    """
    if not username or not password:
        raise AuthenticationFailed({"detail": "Invalid credentials."})

    user = authenticate(username=username, password=password)
    if user is None:
        raise AuthenticationFailed({"detail": "Invalid credentials."})

    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': {'id': user.id, 'username': user.username, 'email': user.email}
    }

def set_auth_cookies(response, access_token, refresh_token):
    """
    Sets http-only secure cookies for tokens.
    Frontend needs 'credentials: include'.
    """
    response.set_cookie('access_token', access_token, httponly=True, samesite='None', secure=True)
    response.set_cookie('refresh_token', refresh_token, httponly=True, samesite='None', secure=True)
    return response

def delete_auth_cookies(response):
    """
    Deletes auth cookies from the response.
    """
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response

def blacklist_refresh_token(request):
    """
    Adds refresh token to blacklist.
    """
    refresh_token = request.COOKIES.get('refresh_token')
    if not refresh_token:
        raise AuthenticationFailed({"detail": "No refresh token provided."})
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except Exception:
        raise AuthenticationFailed({"detail": "Token is invalid or expired."})

def refresh_access_token(request):
    """
    Gets new access token from refresh cookie.
    """
    refresh_token = request.COOKIES.get('refresh_token')
    if not refresh_token:
        raise AuthenticationFailed({"detail": "Refresh token missing."})
    try:
        return str(RefreshToken(refresh_token).access_token)
    except Exception:
        raise AuthenticationFailed({"detail": "Refresh token is invalid or expired."})
