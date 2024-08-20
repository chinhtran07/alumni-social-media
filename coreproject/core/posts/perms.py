from rest_framework import permissions


class IsOwner(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view) and obj.author == request.user


class IsCommentOwnerOrPostAuthor(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user or obj.post.author == request.user
