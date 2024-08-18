from django.contrib import admin

from .models import *


# Register your models here.


class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'email', 'role', 'is_active']
    search_fields = ['username']
    list_filter = ['role', 'username', 'first_name', ]


class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ['id']


admin.site.register(User, UserAdmin)
admin.site.register(FriendRequest, FriendRequestAdmin)

