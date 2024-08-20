from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, parsers, generics, status, filters
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import cloudinary.uploader

from .serializers import *
from posts.models import Post

from posts.serializers import PostSerializer


# Create your views here.


class UserViewSet(viewsets.ViewSet, generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    parser_classes = [parsers.MultiPartParser]
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ['first_name', 'last_name']
    permission_classes = [permissions.IsAuthenticated()]

    def get_permissions(self):
        if self.action == 'register_user':
            return [permissions.AllowAny()]

        return self.permission_classes

    @action(detail=False, methods=['get'], url_path='current-user')
    def current_user(self, request):
        user = request.user

        if user.role == User.Roles.ALUMNI:
            # Include Alumni profile information
            alumni_profile = user.alumniprofile
            alumni_serializer = AlumniSerializer(alumni_profile)
            return Response({
                "user": self.get_serializer(user).data,
                "alumni": alumni_serializer.data
            }, status=status.HTTP_200_OK)

        elif user.role == User.Roles.LECTURER:
            # Include Lecturer profile information
            lecturer_profile = user.lecturerprofile
            lecturer_serializer = LecturerSerializer(lecturer_profile)
            return Response({
                "user": self.get_serializer(user).data,
                "lecturer": lecturer_serializer.data
            }, status=status.HTTP_200_OK)

        # Return only user data if not Alumni or Lecturer
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='register')
    def register_user(self, request):
        data = request.data
        password = data.get('password')
        if not password:
            return Response({"error": "Password is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                avatar = data.get('avatar')
                res = cloudinary.uploader.upload(avatar, folder='avatar/')
                new_user = User.objects.create_user(
                    username=data.get('username'),
                    password=password,
                    email=data.get('email'),
                    first_name=data.get('first_name'),
                    last_name=data.get('last_name'),
                    phone_number=data.get('phone_number'),
                    avatar=res['secure_url']
                )

                serializer = self.get_serializer(new_user)

                return Response(data=serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='change-password')
    def change_password(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not user.check_password(old_password):
            return Response({"error": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['patch'], url_path='update-lecturer')
    @transaction.atomic
    def update_lecturer(self, request):
        user = request.user
        if user.role != User.Roles.LECTURER:
            return Response({"error": "User must be a Lecturer to update Lecturer profile"},
                            status=status.HTTP_400_BAD_REQUEST)

        lecturer_profile = user.lecturerprofile
        lecturer_data = request.data.get('lecturer', {})
        user_data = request.data.get('user', {})

        try:
            with transaction.atomic():
                # Update the common user fields
                user_serializer = UserSerializer(user, data=user_data, partial=True)
                if user_serializer.is_valid():
                    user_serializer.save()
                else:
                    return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                # Update the lecturer-specific fields
                lecturer_serializer = LecturerSerializer(lecturer_profile, data=lecturer_data, partial=True)
                if lecturer_serializer.is_valid():
                    lecturer_serializer.save()
                else:
                    return Response(lecturer_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['patch'], url_path='update-alumni')
    @transaction.atomic
    def update_alumni(self, request):
        user = request.user
        if user.role != User.Roles.ALUMNI:
            return Response({"error": "User must be an Alumni to update Alumni profile"},
                            status=status.HTTP_400_BAD_REQUEST)

        alumni_profile = user.alumniprofile
        alumni_data = request.data.get('alumni', {})
        user_data = request.data.get('user', {})

        try:
            with transaction.atomic():
                # Update the common user fields
                user_serializer = UserSerializer(user, data=user_data, partial=True)
                if user_serializer.is_valid():
                    user_serializer.save()
                else:
                    return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                # Update the alumni-specific fields
                alumni_serializer = AlumniSerializer(alumni_profile, data=alumni_data, partial=True)
                if alumni_serializer.is_valid():
                    alumni_serializer.save()
                else:
                    return Response(alumni_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='friends')
    def add_friend(self, request):
        receiver_id = request.data.get('receiver')

        try:
            sender = request.user
            receiver = User.objects.get(id=receiver_id)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        try:
            with transaction.atomic():
                if self.handle_rejected_request(sender, receiver):
                    return Response({'status': 'Request resent and is now pending'}, status=status.HTTP_200_OK)

                    # Kiểm tra nếu có yêu cầu pending
                if self.is_request_pending(sender, receiver):
                    return Response({'error': 'Friend request already sent and pending'},
                                    status=status.HTTP_400_BAD_REQUEST)

                    # Tạo yêu cầu kết bạn mới
                friend_request = FriendRequest(sender=sender, receiver=receiver)
                friend_request.save()

                # Gửi thông báo thời gian thực
                self.send_notification(friend_request)

                return Response({'status': 'Request sent'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='posts')
    def add_post(self, request):
        data = request.data
        try:
            with transaction.atomic():
                media = data.get('media')
                res = cloudinary.uploader.upload(media, folder='posts/')
                post = Post.objects.create(
                    title=data.get('title'),
                    content=data.get('content'),
                    media = res['secure_url'],
                    author=request.user
                )

                serializer = PostSerializer(post)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def handle_rejected_request(self, sender, receiver):
        rejected_request = FriendRequest.objects.filter(
            sender=sender, receiver=receiver, status=FriendRequest.Status.REJECTED
        ).first()

        if rejected_request:
            rejected_request.status = FriendRequest.Status.PENDING
            rejected_request.save()

            # Gửi thông báo thời gian thực
            self.send_notification(rejected_request)
            return True
        return False

    def is_request_pending(self, sender, receiver):
        return FriendRequest.objects.filter(sender=sender, receiver=receiver, status=FriendRequest.Status.PENDING).exists()

    def send_notification(self, friend_request):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{friend_request.receiver.id}",
            {
                'type': 'send_notification',
                'payload': {
                    'friend_request_id': friend_request.id,
                    'sender_id': friend_request.sender.id,
                    'message': "You have a new friend request"
                }
            }
        )


class FriendRequestViewSet(viewsets.ViewSet,
                           generics.RetrieveAPIView,
                           generics.CreateAPIView):
    queryset = FriendRequest.objects.all()
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='received-requests')
    def received_requests(self, request):
        received_requests = self.get_queryset().filter(receiver=request.user, status=FriendRequest.Status.PENDING)

        paginator = PageNumberPagination()
        paginator.page_size = 10
        paginated_requests = paginator.paginate_queryset(received_requests, request)

        serializer = FriendRequestSerializer(paginated_requests, many=True)
        return  paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        request_instance = self.get_object()
        if request_instance.status == FriendRequest.Status.PENDING:
            return Response({'detail': 'Request already processed'}, status=status.HTTP_400_BAD_REQUEST)

        request_instance.status = FriendRequest.Status.ACCEPTED
        request_instance.save()

        Friendship.objects.create(user1=request_instance.sender, user2=request_instance.receiver)

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{request_instance.sender.id}",
            {
                'type': 'send_notification',
                'payload': {
                    'message': f"Your friend request to {request_instance.receiver.username} has been accepted",
                }
            }
        )

        return Response({'status': 'Request accepted'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        request_instance = self.get_object()
        if request_instance.status == FriendRequest.Status.PENDING:
            return Response({'detail': 'Request already processed'}, status=status.HTTP_400_BAD_REQUEST)

        request_instance.status = FriendRequest.Status.REJECTED
        request_instance.save()
        return Response({'status': 'Request rejected'}, status=status.HTTP_200_OK)


class FriendshipViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Friendship.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='friends')
    def list_friends(self, request):
        user = request.user

        friends = User.objects.filter(
            id__in =Friendship.objects.filter(user1=user).value('user2')
        ) | User.objects.filter(
            id__in=Friendship.objects.filter(user2=user).values('user1')
        )

        paginator = PageNumberPagination()
        paginator.page_size = 10
        paginated_friends = paginator.paginate_queryset(friends, request)

        serializer = UserSerializer(paginated_friends, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=['post'], url_path='unfriend')
    def unfriend(self, request):
        try:
            user_id_to_unfriend = request.data.get('user_id')
            if not user_id_to_unfriend:
                return Response({'error': 'User ID is required'}, status=status.HTTP_400_BAD_REQUEST)

            user_to_unfriend = User.objects.get(id=user_id_to_unfriend)

            friendship = Friendship.objects.filter(
                (Q(user1=request.user, user2=user_to_unfriend) | Q(user1=user_to_unfriend, user2=request.user))
            ).first()

            if not friendship:
                return Response({'error': 'Friendship does not exist'}, status=status.HTTP_404_NOT_FOUND)

            friendship.delete()

            friend_request = FriendRequest.objects.filter(
                Q(sender=request.user, receiver=user_to_unfriend) |
                Q(sender=user_to_unfriend, receiver=request.user)
            ).first()

            if friend_request:
                friend_request.status = FriendRequest.Status.REJECTED
                friend_request.save()

            return Response({'status': 'Unfriended and request status updated successfully'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def send_activity_status(user_id):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            'type': 'send_activity_status',
            'user_id': user_id,
            'status': 'active'
        }
    )