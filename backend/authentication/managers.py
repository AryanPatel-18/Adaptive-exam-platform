from django.contrib.auth.base_user import BaseUserManager

# This model is created to manage the user model and handle the creation of regular users and superusers
class UserManager(BaseUserManager):
    """
    Custom manager for the User model.
    Handles creation of regular users and superusers.
    """

    def create_user(self, username, email, password=None, **extra_fields):
        """
        Creates and saves a regular user.
        """

        if not username:
            raise ValueError("Username is required.")

        if not email:
            raise ValueError("Email address is required.")

        if not password:
            raise ValueError("Password is required.")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            username=username,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    # This function is to create the superuser
    def create_superuser(self, username, email, password=None, **extra_fields):
        """
        Creates and saves a superuser.
        """

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        if extra_fields.get("is_active") is not True:
            raise ValueError("Superuser must have is_active=True.")

        return self.create_user(
            username=username,
            email=email,
            password=password,
            **extra_fields
        )