from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        MEMBER = 'member', 'Member'
        GUEST = 'guest', 'Guest'
        LIBRARIAN = 'librarian', 'Librarian'

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)

    join_date = models.DateTimeField(default=timezone.now)

    borrow_limit = models.PositiveIntegerField(default=3)
    
    phone_verified = models.BooleanField(default=False)

    email_verified = models.BooleanField(default=False)

    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return f'{self.username or self.email} [{self.role}]'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=32, null=True, blank=True)
    city = models.CharField(max_length=32, null=True, blank=True)
    address_line1 = models.CharField(max_length=128, null=True, blank=True)
    address_line2 = models.CharField(max_length=128, null=True, blank=True)
    postal_code = models.CharField(max_length=16, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Profile of {self.user.username}'


class OneTimeCode(models.Model):
    class Purpose(models.TextChoices):
        ACCOUNT_ACTIVATION = 'activation', 'Activation'
        LOGIN = 'login', 'Login'
        PASSWORD_RESET = 'password_reset', 'Password Reset'
        PHONE_VERIFICATION = 'phone_verification', 'Phone Verification'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    purpose = models.CharField(max_length=20, choices=Purpose.choices)
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f'{self.user_id} - {self.purpose} - {self.code}'