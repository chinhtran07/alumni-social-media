from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.shortcuts import render
from rest_framework import viewsets, permissions, parsers, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
import cloudinary.uploader

from .serializers import *


# Create your views here.


class UserViewSet(viewsets.ViewSet, generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    parser_classes = [parsers.MultiPartParser]
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
            return Response({"error": "Password is required"}, status=status)

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


class FriendRequestViewSet(viewsets.ViewSet,
                           generics.RetrieveAPIView,
                           generics.ListAPIView,
                           generics.CreateAPIView):
    queryset = FriendRequest.objects.all()
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        receiver_id = request.data.get('receiver')

        try:
            sender = request.user
            receiver = User.objects.get(id=receiver_id)
        except Exception as e:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            with transaction.atomic():
                if FriendRequest.objects.filter(sender=sender, receiver=receiver).exists():
                    return Response({'error': 'Friend request already sent'}, status=status.HTTP_400_BAD_REQUEST)

                friend_request = FriendRequest(sender=sender, receiver=receiver)
                friend_request.save()

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"user_{friend_request.receiver.id}",
                    {
                        'type': 'send_notification',
                        'payload': {
                            'friend_request_id': friend_request.id,
                            'sender_id': friend_request.sender.id ,
                            'message': f"You have a new friend request"
                        }
                    }
                )
                return Response({'status': 'Request sent'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        request_instance = self.get_object()
        if request_instance.accepted or request_instance.rejected:
            return Response({'detail': 'Request already processed'}, status=status.HTTP_400_BAD_REQUEST)

        request_instance.accepted = True
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
        if request_instance.accepted or request_instance.rejected:
            return Response({'detail': 'Request already processed'}, status=status.HTTP_400_BAD_REQUEST)

        request_instance.rejected = True
        request_instance.save()
        return Response({'status': 'Request rejected'}, status=status.HTTP_200_OK)