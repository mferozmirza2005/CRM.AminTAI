from rest_framework import permissions

class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == request.user.Role.SUPERADMIN

class IsAdminOrOwner(permissions.BasePermission):
    """
    Admins can access resources in their region or allowed_accounts.
    Employees can access resources assigned to them.
    SuperAdmin can access everything.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.role == user.Role.SUPERADMIN:
            return True
        if hasattr(obj, 'account'):
            account = obj.account
        elif hasattr(obj, 'accounts'):
            accounts = obj.accounts.all()
            return any(a in user.allowed_accounts.all() or (user.region and a.region == user.region) for a in accounts)
        elif hasattr(obj, 'owner'):
            account = getattr(obj, 'owner', None)
            account = None
        else:
            account = None

        if user.role == user.Role.ADMIN:
            if account:
                if user.region and account.region == user.region:
                    return True
                return account in user.allowed_accounts.all()
        if user.role == user.Role.EMPLOYEE:
            if getattr(obj, 'owner', None) == user or getattr(obj, 'assigned_to', None) == user:
                return True
        return False
