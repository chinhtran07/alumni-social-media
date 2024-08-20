from django.contrib import admin

from .models import *


# Register your models here.


class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'created_at', "shared_post"]
    list_filter = ['author', 'created_at']


class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'created_at']
    list_filter = ['author', 'created_at']


admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
