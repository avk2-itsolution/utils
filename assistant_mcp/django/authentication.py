from __future__ import annotations

from hmac import compare_digest

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import APIException, AuthenticationFailed


class McpBearerTokenNotConfigured(APIException):
    status_code = 503
    default_detail = {"error": "mcp_bearer_token_not_configured", "param": "MCP_TASKS_BEARER_TOKEN"}
    default_code = "mcp_bearer_token_not_configured"


class InvalidMcpBearerToken(APIException):
    status_code = 403
    default_detail = {"error": "invalid_bearer_token"}
    default_code = "invalid_bearer_token"


class McpBearerAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        token = getattr(settings, "MCP_TASKS_BEARER_TOKEN", "")
        if not token:
            raise McpBearerTokenNotConfigured()
        authorization = request.headers.get("Authorization", "")
        prefix = f"{self.keyword} "
        if not authorization.startswith(prefix):
            raise AuthenticationFailed({"error": "missing_bearer_token"})
        request_token = authorization[len(prefix):]
        if not compare_digest(request_token, str(token)):
            raise InvalidMcpBearerToken()
        return AnonymousUser(), request_token

    def authenticate_header(self, request) -> str:
        return self.keyword
