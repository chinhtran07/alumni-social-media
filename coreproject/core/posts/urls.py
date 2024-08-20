from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'posts', PostViewSet, 'posts')
router.register(r'comments', CommentViewSet, 'comments')

urlpatterns = [
    path('v1/', include(router.urls))
]