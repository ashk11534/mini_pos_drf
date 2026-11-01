from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )

class CanManageProduct(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.has_perm(
                'base.can_manage_product'
            )
        )
