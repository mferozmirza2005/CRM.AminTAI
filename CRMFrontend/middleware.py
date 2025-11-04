import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

User = get_user_model()

class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware that authenticates users for template views using JWT tokens
    stored in Authorization headers or cookies.
    """

    def process_request(self, request):
        auth_header = request.headers.get("Authorization")
        token = None

        # Allow token from cookie (optional)
        if not auth_header and "Authorization" in request.COOKIES:
            auth_header = request.COOKIES.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        if not token:
            request.user = getattr(request, "user", None)
            return

        try:
            access = AccessToken(token)
            user_id = access["user_id"]
            user = User.objects.get(id=user_id)
            request.user = user
        except (User.DoesNotExist, TokenError, InvalidToken, jwt.ExpiredSignatureError):
            # Token invalid or expired
            from django.contrib.auth.models import AnonymousUser
            request.user = AnonymousUser()
