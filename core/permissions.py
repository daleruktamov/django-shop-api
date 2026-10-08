from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """Читать может кто угодно, изменять — только администратор."""

    message = "Изменять этот раздел может только администратор."

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)


class IsOwnerOrAdmin(permissions.BasePermission):
    """Доступ к объекту есть у его владельца и у администратора."""

    message = "Доступ к чужим данным закрыт."

    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated and request.user.is_admin:
            return True
        return getattr(obj, "user_id", None) == request.user.id


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Редактировать и удалять запись может только её автор (или администратор)."""

    message = "Редактировать можно только свои записи."

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_authenticated and request.user.is_admin:
            return True
        return obj.user_id == request.user.id
