from django.contrib.auth.base_user import BaseUserManager
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