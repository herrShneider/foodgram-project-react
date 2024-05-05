"""Модуль кастомных прав."""

from rest_framework import permissions


# class IsAdmin(permissions.BasePermission):
#     """Пользователь - это admin или superamin django."""
#
#     def has_permission(self, request, view):
#         """Пользователь - это admin или superamin django."""
#         return request.user.is_authenticated and request.user.is_admin


class IsAuthorOrIsAdmin(permissions.BasePermission):
    """Пользователь - это автор объекта либо admin."""

    def has_object_permission(self, request, view, obj):
        """Пользователь - это автор объекта либо admin."""
        return obj.author == request.user or request.user.is_admin


class IsAuthorAdminOrReadOnly(permissions.BasePermission):
    """Пользователь - это автор объекта/admin либо только чтение."""

    def has_permission(self, request, view):
        return (
                request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated
            )

    def has_object_permission(self, request, view, obj):
        """Пользователь - это автор объекта/admin либо только чтение."""
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
            or request.user.is_admin
        )
