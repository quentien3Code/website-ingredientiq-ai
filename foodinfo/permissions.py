from rest_framework import permissions

class IsSuperAdmin(permissions.BasePermission):
    """
    Custom permission to only allow super admins to access the view.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and 
                   hasattr(request.user, 'is_super_admin') and request.user.is_super_admin) 