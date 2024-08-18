from rest_framework import serializers

from .models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'role',
                  'avatar']
        extra_kwargs = {
            'password': {'write_only': True},
            'role': {'read_only': True}
        }


class AlumniProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlumniProfile
        fields = ['address', 'graduation_year', 'major', 'current_job_title', 'current_company']


class LecturerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LecturerProfile
        fields = ['department', 'bio']


class AlumniSerializer(UserSerializer):
    more = AlumniProfileSerializer(read_only=True)

    class Meta(UserSerializer.Meta):
        model = Alumni
        fields = UserSerializer.Meta.fields + ['more']


class LecturerSerializer(UserSerializer):
    more = LecturerProfileSerializer(read_only=True)

    class Meta(UserSerializer.Meta):
        model = Lecturer
        fields = UserSerializer.Meta.fields + ['more']


class UserFriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'avatar']


class FriendRequestSerializer(serializers.ModelSerializer):
    sender = UserFriendRequestSerializer()
    receiver = UserFriendRequestSerializer()

    class Meta:
        model = FriendRequest
        fields = ['id', 'sender', 'receiver', 'created_at', 'accepted', 'rejected']


class FriendshipSerializer(serializers.ModelSerializer):
    user1 = UserFriendRequestSerializer()
    user2 = UserFriendRequestSerializer()

    class Meta:
        model = Friendship
        fields = ['id', 'user1', 'user2', 'created_at']
