from rest_framework import permissions
from .models import BoardMembership

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        return obj.owner == request.user

class IsBoardMemberOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow only board members to edit tasks.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions allowed for all
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check if user is the owner
        if obj.owner == request.user:
            return True

        # Check if user is a collaborator
        if obj.collaborators.filter(id=request.user.id).exists():
            return True

        # Check if user is a board member
        return BoardMembership.objects.filter(user=request.user, board=obj.board).exists()