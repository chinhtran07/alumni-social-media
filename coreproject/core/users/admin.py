from django.contrib import admin

from .models import User


# Register your models here.


class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'email', 'role', 'is_active']
    search_fields = ['username']
    list_filter = ['role', 'username', 'first_name', ]


admin.site.register(User, UserAdmin)

