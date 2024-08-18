from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        LECTURER = "LECTURER", "Lecturer",
        ALUMNI = "ALUMNI", "Alumni"

    created_date = models.DateTimeField(auto_now_add=True, null=True)
    updated_date = models.DateTimeField(auto_now=True, null=True)
    verified = models.BooleanField(default=False)
    date_of_birth = models.DateField(null=True)
    phone_number = models.CharField(max_length=11)

    role = models.CharField(max_length=50, choices=Roles.choices, default=Roles.ALUMNI)
    avatar = models.CharField(max_length=255)
    cover_image = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f'{self.get_full_name()} - {self.role}'

    def save(self, *args, **kwargs):
        if not self.verified and self.role == User.Roles.LECTURER:
            self.password = make_password("123456")
        self.password = make_password(self.password)
        super().save(*args, **kwargs)


class AlumniManager(BaseUserManager):
    def get_queryset(self):
        return super().get_queryset().select_related('alumniprofile').filter(role=User.Roles.ALUMNI)


class AlumniProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.TextField(blank=True)
    graduation_year = models.CharField(max_length=4, blank=False, null=False)
    major = models.CharField(max_length=100, blank=True)
    current_job_title = models.CharField(max_length=100)
    current_company = models.CharField(max_length=100)


class Alumni(User):
    objects = AlumniManager()

    @property
    def more(self):
        return self.alumniprofile

    class Meta:
        proxy = True


class LecturerManager(BaseUserManager):
    def get_queryset(self):
        return super().get_queryset().select_related('lecturerprofile').filter(role=User.Roles.LECTURER)


class LecturerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=255)
    bio = models.TextField(blank=True, null=True)


class Lecturer(User):
    objects = LecturerManager()

    @property
    def more(self):
        return self.lecturerprofile

    class Meta:
        proxy = True


class FriendRequest(models.Model):
    sender = models.ForeignKey(User, related_name="sent_requests", on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name="received_requests", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender} -> {self.receiver}"


class Friendship(models.Model):
    user1 = models.ForeignKey(User, related_name='friendship_user1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='friendship_user2', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user1', 'user2')

    def __str__(self):
        return f"{self.user1} <-> {self.user2}"

