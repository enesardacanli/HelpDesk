"""
IT Destek ve Envanter Yönetim Sistemi — Veritabanı Modelleri.

Modeller:
    - Departman
    - Kullanici (Custom User)
    - Donanim
    - DestekTalebi (Ticket)
    - ZimmetLog (Audit Trail)
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from core.constants import (
    DonanimDurum,
    Rol,
    TicketAciliyet,
    TicketDurum,
    TicketKategori,
    ZimmetIslemTuru,
)
from core.managers import KullaniciManager


# ==========================================================================
# DEPARTMAN
# ==========================================================================


class Departman(models.Model):
    """Kurumsal departman bilgisi."""

    ad = models.CharField(max_length=100, unique=True)
    aciklama = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Departman'
        verbose_name_plural = 'Departmanlar'
        ordering = ['ad']

    def __str__(self):
        return self.ad


# ==========================================================================
# KULLANICI (Custom User Model)
# ==========================================================================


class Kullanici(AbstractBaseUser, PermissionsMixin):
    """E-posta tabanlı özel kullanıcı modeli."""

    email = models.EmailField(unique=True)
    ad = models.CharField(max_length=50)
    soyad = models.CharField(max_length=50)
    rol = models.CharField(
        max_length=25,
        choices=Rol.choices,
        default=Rol.STANDART_KULLANICI,
    )
    departman = models.ForeignKey(
        Departman,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='personeller',
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    kayit_tarihi = models.DateTimeField(auto_now_add=True)

    objects = KullaniciManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['ad', 'soyad']

    class Meta:
        verbose_name = 'Kullanıcı'
        verbose_name_plural = 'Kullanıcılar'
        ordering = ['ad', 'soyad']

    def __str__(self):
        return f'{self.ad} {self.soyad}'

    @property
    def tam_ad(self):
        """Kullanıcının tam adını döndürür."""
        return f'{self.ad} {self.soyad}'


# ==========================================================================
# DONANIM
# ==========================================================================


class Donanim(models.Model):
    """BT donanım envanteri kaydı."""

    seri_no = models.CharField(max_length=100, unique=True, db_index=True)
    marka = models.CharField(max_length=100)
    model_adi = models.CharField(max_length=100)
    kategori = models.CharField(max_length=100)
    durum = models.CharField(
        max_length=15,
        choices=DonanimDurum.choices,
        default=DonanimDurum.DEPODA,
        db_index=True,
    )
    zimmetli_kullanici = models.ForeignKey(
        Kullanici,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donanimlar',
    )
    garanti_bitis_tarihi = models.DateField(null=True, blank=True)
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Donanım'
        verbose_name_plural = 'Donanımlar'
        ordering = ['-olusturma_tarihi']

    def __str__(self):
        return f'{self.marka} {self.model_adi} ({self.seri_no})'

    @property
    def garanti_durumu(self):
        """Garantide / Garanti Bitti / Belirtilmemis."""
        if not self.garanti_bitis_tarihi:
            return 'Belirtilmemis'
        from django.utils import timezone
        today = timezone.now().date()
        if self.garanti_bitis_tarihi >= today:
            return 'Garantide'
        return 'Garanti Bitti'


# ==========================================================================
# DESTEK TALEBİ (TICKET)
# ==========================================================================


class DestekTalebi(models.Model):
    """Kullanıcıların oluşturduğu IT destek talepleri (ticket)."""

    baslik = models.CharField(max_length=200)
    aciklama = models.TextField()
    kategori = models.CharField(
        max_length=15,
        choices=TicketKategori.choices,
    )
    aciliyet = models.CharField(
        max_length=10,
        choices=TicketAciliyet.choices,
        default=TicketAciliyet.NORMAL,
    )
    durum = models.CharField(
        max_length=15,
        choices=TicketDurum.choices,
        default=TicketDurum.YENI,
        db_index=True,
    )
    olusturan = models.ForeignKey(
        Kullanici,
        on_delete=models.CASCADE,
        related_name='acilan_biletler',
    )
    atanan_it_uzmani = models.ForeignKey(
        Kullanici,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='atanan_biletler',
    )
    ilgili_donanim = models.ForeignKey(
        Donanim,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='destek_talepleri',
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Destek Talebi'
        verbose_name_plural = 'Destek Talepleri'
        ordering = ['-olusturma_tarihi']

    def __str__(self):
        return f'[{self.get_durum_display()}] {self.baslik}'


# ==========================================================================
# ZİMMET LOG (Audit Trail — Append-Only)
# ==========================================================================


class ZimmetLog(models.Model):
    """
    Donanım zimmet işlemlerinin değiştirilemez denetim kaydı.

    Bu tablo append-only olarak tasarlanmıştır.
    Uygulama seviyesinde silme ve güncelleme işlemleri engellenir.
    """

    donanim = models.ForeignKey(
        Donanim,
        on_delete=models.CASCADE,
        related_name='zimmet_loglari',
    )
    islem_turu = models.CharField(
        max_length=20,
        choices=ZimmetIslemTuru.choices,
    )
    eski_kullanici = models.ForeignKey(
        Kullanici,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eski_zimmet_loglari',
    )
    yeni_kullanici = models.ForeignKey(
        Kullanici,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='yeni_zimmet_loglari',
    )
    islem_yapan = models.ForeignKey(
        Kullanici,
        on_delete=models.PROTECT,
        related_name='yapilan_zimmet_loglari',
    )
    aciklama = models.TextField(blank=True, default='')
    islem_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Zimmet Logu'
        verbose_name_plural = 'Zimmet Logları'
        ordering = ['-islem_tarihi']

    def __str__(self):
        return (
            f'{self.get_islem_turu_display()} — '
            f'{self.donanim} ({self.islem_tarihi:%d.%m.%Y %H:%M})'
        )

    def save(self, *args, **kwargs):
        """Mevcut kayıtların güncellenmesini engeller (append-only)."""
        if self.pk is not None:
            raise ValueError('Zimmet log kayıtları güncellenemez.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Silme işlemini engeller (append-only)."""
        raise ValueError('Zimmet log kayıtları silinemez.')
