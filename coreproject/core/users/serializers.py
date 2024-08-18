from rest_framework import serializers

from .models import *


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=True, write_only=True)

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