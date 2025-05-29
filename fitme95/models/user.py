from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, google_id, email, first_name="", last_name=""):
        if not google_id:
            raise ValueError("Users must have a Google ID")
        user = self.model(
            google_id=google_id,
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name
        )
        user.save(using=self._db)
        return user


class CustomUser(AbstractBaseUser):
    google_id = models.CharField(max_length=255, primary_key=True)  # Google ID as primary key
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    objects = CustomUserManager()

    USERNAME_FIELD = "google_id"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.email
