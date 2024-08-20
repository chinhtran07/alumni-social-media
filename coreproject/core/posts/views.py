from random import random

from django.shortcuts import render
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response

from . import perms
from .models import Post, Comment, Reaction
from .pagination import PostPagination
from .serializers import CommentSerializer, PostSerializer, ReactionSerializer
from users.models import User


# Create your views here.


class PostViewSet(viewsets.ViewSet,
                  generics.ListAPIView,
                  generics.UpdateAPIView,
                  generics.RetrieveAPIView,
                  generics.DestroyAPIView):
    queryset = Post.objects.filter(is_active=True).all().order_by('-updated_at')
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostSerializer

    def get_permissions(self):
        if self.action in ['update', 'block_comments']:
            return [perms.IsOwner()]
        if self.action.__eq__('destroy'):
            return [perms.IsOwner(), permissions.IsAdminUser()]
        return self.permission_classes

    def get_queryset(self):
        queries = self.queryset

        q = self.request.query_params.get('userId')

        if q:
            user = User.objects.get(pk=q)

            if user:
                queries = user.posts.filter(is_active=True).order_by('-created_date')

        return queries

    @action(methods=['post'], detail=True)
    def comments(self, request, pk=None):
        post = self.get_object()
        content = request.data.get('content')
        parent_id = request.data.get('parent', None)

        if not content:
            return Response({'error': 'Content is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            parent_comment = Comment.objects.get(id=parent_id) if parent_id else None
        except Comment.DoesNotExist:
            return Response({'error': 'Parent comment not found'}, status=status.HTTP_404_NOT_FOUND)

        comment = Comment.objects.create(
            post=post,
            author=request.user,
            content=content,
            parent=parent_comment
        )

        serializer = CommentSerializer(comment)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['post'], detail=True)
    def reacts(self, request, pk=None):
        reaction_type = request.data.get('reaction_type')

        if reaction_type not in dict(Reaction.ReactionType.choices).keys():
            return Response({'error': 'Invalid reaction type'}, status=status.HTTP_400_BAD_REQUEST)

        existing_reaction = Reaction.objects.filter(post=self.get_object(), user=request.user).first()

        if existing_reaction:
            if existing_reaction.reaction_type == int(reaction_type):
                existing_reaction.is_active = not existing_reaction.is_active
                return Response(ReactionSerializer(existing_reaction).data,status=status.HTTP_200_OK)
            else:
                existing_reaction.reaction_type = int(reaction_type)
                existing_reaction.save()
                serializer = ReactionSerializer(existing_reaction)
                return Response(serializer.data, status=status.HTTP_200_OK)

        reaction = Reaction.objects.create(
            post = self.get_object(),
            user = request.user,
            reaction_type = int(reaction_type)
        )

        serializer = ReactionSerializer(reaction)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='random-posts')
    def random_posts(self, request):
        count = int(request.query_params.get('count', 100))  # Tổng số bài viết ngẫu nhiên
        all_posts = list(Post.objects.all())  # Lấy tất cả bài viết
        random_posts = random.sample(all_posts, min(count, len(all_posts)))  # Chọn ngẫu nhiên

        # Phân trang
        paginator = PostPagination()
        paginated_posts = paginator.paginate_queryset(random_posts, request)
        serializer = self.get_serializer(paginated_posts, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(methods=['post'], detail=True, url_path='block-comment')
    def block_comments(self, request, pk=None):
        post = self.get_object()
        post.comment_blocked = not post.comment_blocked
        post.save()

        return Response(status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True)
    def share(self, request, pk=None):
        original_post = self.get_object()
        content = request.data.get('content', '')
        shared_post = Post.objects.create(
            author=request.user,
            content=content,
            shared_post=original_post
        )

        serializer = PostSerializer(shared_post)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CommentViewSet(viewsets.ViewSet,
                     generics.CreateAPIView,
                     generics.UpdateAPIView,
                     generics.DestroyAPIView,
                     generics.ListAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['update']:
            return [perms.IsOwner()]
        if self.action.__eq__('destroy'):
            return [perms.IsCommentOwnerOrPostAuthor()]
        return self.permission_classes

    def get_queryset(self):
        queries = self.queryset

        q = self.request.query_params.get('postId')

        if q:
            post = Post.objects.get(pk=q)

            if post:
                queries = post.comments.filter(is_active=True).order_by('-created_date')

        return queries

    def create(self, request, *args, **kwargs):
        post_id = request.data.get('post')
        parent_id = request.data.get('parent', None)
        content = request.data.get('content')

        try:
            post = Post.objects.get(id=post_id)
            parent = Comment.objects.get(id=parent_id) if parent_id else None
        except Post.DoesNotExist:
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)
        except Comment.DoesNotExist:
            return Response({'error': 'Parent comment not found'}, status=status.HTTP_404_NOT_FOUND)

        comment = Comment.objects.create(
            post=post,
            author=request.user,
            content=content,
            parent=parent
        )
        serializer = self.get_serializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)