from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated


class IsAdminOrReadOnly(IsAuthenticated):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True  

        return request.user.is_authenticated and request.user.role == 'admin'
    

class IsLibrarianOrAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return request.user.role in ['librarian', 'admin']


class IsMemberOrAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return request.user.role in ['member', 'admin']


class IsOwnerOrAdmin(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        return request.user.is_authenticated and (
            request.user.role == 'admin' or
            hasattr(obj, 'user') and obj.user == request.user
        )


class CanManageBooks(IsAuthenticated):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if not request.user.is_authenticated:
            return False

        if request.user.role == 'admin':
            return True
        
        elif request.user.role == 'librarian':
            return request.method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
        
        elif request.user.role == 'member':
            return request.method in permissions.SAFE_METHODS

        return False
    
    
class CanManageBookCopies(IsAuthenticated):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.role == 'admin':
            return True

        if request.user.role == 'librarian':
            return True
        
        if request.user.role == 'member':
            return request.method in permissions.SAFE_METHODS

        return False

class CanManageBorrow(IsAuthenticated):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return request.user.role in ['librarian', 'admin']