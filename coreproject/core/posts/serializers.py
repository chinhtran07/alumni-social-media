from rest_framework import serializers
from users.serializers import UserFriendSerializer

from .models import Post, Reaction, Comment


class PostSerializer(serializers.ModelSerializer):
    author = UserFriendSerializer()
    likes_count = serializers.IntegerField(source='likes.count', read_only=True)
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)
    shared_post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all(), allow_null=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'media', 'author', 'shared_post', 'comment_blocked', 'updated_at',
                  'likes_count', 'comments_count']
        read_only_fields = ['id', 'updated_at', 'likes_count', 'comments_count', 'shared_post', 'comment_blocked',
                            'author']


class CommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'author', 'content', 'created_at', 'parent', 'replies']
        read_only_fields = ['id', 'created_at', 'parent', 'replies']

    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True).data
        return None


class ReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reaction
        fields = ['id', 'user', 'reaction_type', 'updated_at']
        read_only_fields = ['id']