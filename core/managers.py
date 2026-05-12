"""
Kullanıcı modeli yöneticileri (managers).

Custom User Model için gerekli UserManager tanımını içerir.
"""

from django.contrib.auth.models import BaseUserManager

from core.constants import Rol


class KullaniciManager(BaseUserManager):
    """Custom user model için manager."""

    def create_user(self, email, password=None, **extra_fields):
        """Standart kullanıcı oluşturur."""
        if not email:
            raise ValueError('E-posta adresi zorunludur.')

        email = self.normalize_email(email)
        extra_fields.setdefault('rol', Rol.STANDART_KULLANICI)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Admin (superuser) oluşturur."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('rol', Rol.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser için is_staff=True olmalıdır.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser için is_superuser=True olmalıdır.')

        return self.create_user(email, password, **extra_fields)
