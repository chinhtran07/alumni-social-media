from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'friend-request', FriendRequestViewSet, basename='friend-request')

urlpatterns = [
    path('v1/', include(router.urls))
]

