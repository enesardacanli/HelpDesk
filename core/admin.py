"""
Django Admin panel konfigürasyonu.

Tüm modeller için zengin admin arayüzü tanımları içerir.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from core.models import Departman, DestekTalebi, Donanim, Kullanici, ZimmetLog


# ==========================================================================
# DEPARTMAN
# ==========================================================================


@admin.register(Departman)
class DepartmanAdmin(admin.ModelAdmin):
    list_display = ('ad', 'aciklama')
    search_fields = ('ad',)


# ==========================================================================
# KULLANICI
# ==========================================================================


@admin.register(Kullanici)
class KullaniciAdmin(BaseUserAdmin):
    model = Kullanici
    list_display = ('email', 'ad', 'soyad', 'rol', 'departman', 'is_active')
    list_filter = ('rol', 'is_active', 'departman')
    search_fields = ('email', 'ad', 'soyad')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Kişisel Bilgiler', {'fields': ('ad', 'soyad', 'departman')}),
        ('Rol & Yetki', {'fields': ('rol', 'is_active', 'is_staff', 'is_superuser')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'ad', 'soyad', 'rol', 'departman', 'password1', 'password2'),
        }),
    )


# ==========================================================================
# DONANIM
# ==========================================================================


@admin.register(Donanim)
class DonanimAdmin(admin.ModelAdmin):
    list_display = ('seri_no', 'marka', 'model_adi', 'kategori', 'durum', 'zimmetli_kullanici')
    list_filter = ('durum', 'kategori', 'marka')
    search_fields = ('seri_no', 'marka', 'model_adi')
    raw_id_fields = ('zimmetli_kullanici',)


# ==========================================================================
# DESTEK TALEBİ
# ==========================================================================


@admin.register(DestekTalebi)
class DestekTalebiAdmin(admin.ModelAdmin):
    list_display = (
        'baslik', 'kategori', 'aciliyet', 'durum',
        'olusturan', 'atanan_it_uzmani', 'olusturma_tarihi',
    )
    list_filter = ('durum', 'kategori', 'aciliyet')
    search_fields = ('baslik', 'aciklama')
    raw_id_fields = ('olusturan', 'atanan_it_uzmani', 'ilgili_donanim')
    readonly_fields = ('olusturma_tarihi', 'guncelleme_tarihi')


# ==========================================================================
# ZİMMET LOG
# ==========================================================================


@admin.register(ZimmetLog)
class ZimmetLogAdmin(admin.ModelAdmin):
    list_display = (
        'donanim', 'islem_turu', 'islem_yapan',
        'eski_kullanici', 'yeni_kullanici', 'islem_tarihi',
    )
    list_filter = ('islem_turu',)
    search_fields = ('donanim__seri_no', 'aciklama')
    readonly_fields = (
        'donanim', 'islem_turu', 'eski_kullanici', 'yeni_kullanici',
        'islem_yapan', 'aciklama', 'islem_tarihi',
    )

    def has_add_permission(self, request):
        """Admin panelinden log eklemeyi engeller."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Admin panelinden log silmeyi engeller (Append-only)."""
        return False

    def has_change_permission(self, request, obj=None):
        """Admin panelinden log düzenlemeyi engeller (Append-only)."""
        return False
