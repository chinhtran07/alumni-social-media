from django.db import models
from users.models import User


# Create your models here.

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Post(BaseModel):
    title = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    media = models.CharField(max_length=255)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    shared_post = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='shared_by')
    comment_blocked = models.BooleanField(default=False)

    def __str__(self):
        return self.title if self.title else f"Shared post by {self.author.username}"


class Comment(BaseModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')

    def __str__(self):
        return f'Comment by {self.author} on {self.post}'

    @property
    def is_reply(self):
        return self.parent is not None


class Reaction(models.Model):

    class ReactionType(models.IntegerChoices):
        LIKE = 1, "like",
        HAHA = 2, "haha",
        LOVE = 3, "love"

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction_type = models.IntegerField(choices=ReactionType.choices)

    class Meta:
        unique_together = ('post', 'user')

    def __str__(self):
        return f"{self.user.username} reacted with {self.reaction_type.name} on {self.post.title}"