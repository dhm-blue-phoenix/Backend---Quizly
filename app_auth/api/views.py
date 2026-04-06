"""
Views for the authentication API.

All views delegate business logic to functions.py and only handle
request/response flow. Each view is kept under 14 lines.

Frontend Cookie Handling:
    All auth tokens are delivered as HTTP-Only cookies.
    The frontend must use `credentials: 'include'` in every
    fetch request to ensure cookies are sent automatically.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .functions import (
    create_user,
    authenticate_and_get_tokens,
    set_auth_cookies,
    delete_auth_cookies,
    blacklist_refresh_token,
    refresh_access_token,
)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """Registers a new user and returns 201 on success."""
    create_user(request.data)
    return Response(
        {"detail": "User created successfully!"},
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Authenticates a user and sets auth cookies."""
    data = authenticate_and_get_tokens(
        request.data.get('username'),
        request.data.get('password'),
    )
    response = Response(
        {"detail": "Login successfully!", "user": data['user']},
        status=status.HTTP_200_OK,
    )
    return set_auth_cookies(response, data['access'], data['refresh'])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Blacklists the refresh token and deletes auth cookies."""
    blacklist_refresh_token(request)
    response = Response(
        {"detail": "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid."},
        status=status.HTTP_200_OK,
    )
    return delete_auth_cookies(response)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """Refreshes the access token using the refresh cookie."""
    new_access = refresh_access_token(request)
    response = Response(
        {"detail": "Token refreshed"},
        status=status.HTTP_200_OK,
    )
    response.set_cookie(
        'access_token', new_access, httponly=True, samesite='Lax',
    )
    return response
