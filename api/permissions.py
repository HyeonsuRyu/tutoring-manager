from rest_framework.permissions import BasePermission


class IsOwnerResource(BasePermission):
    """Object must belong to request.user (via .owner or .student.owner)."""

    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, "owner", None)
        if owner is not None:
            return owner == request.user
        student = getattr(obj, "student", None)
        if student is not None:
            return student.owner == request.user
        return False
