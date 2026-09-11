from django.conf import settings
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


class McpOriginPermission(BasePermission):
    def has_permission(self, request, view) -> bool:
        origin = request.headers.get("Origin")
        if not origin:
            return True
        allowed_origins = set(getattr(settings, "MCP_TASKS_ALLOWED_ORIGINS", ()))
        current_origin = f"{request.scheme}://{request.get_host()}"
        if origin == current_origin or origin in allowed_origins:
            return True
        raise PermissionDenied({"error": "origin_not_allowed"})
