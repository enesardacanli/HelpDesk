"""
Django REST Framework Serializer'ları.

Tüm API giriş/çıkış veri dönüşümlerini ve validasyonlarını yönetir.
"""

from rest_framework import serializers

from core.constants import (
    DONANIM_DURUM_GECISLERI,
    TICKET_DURUM_GECISLERI,
    DonanimDurum,
)
from core.models import Departman, DestekTalebi, Donanim, Kullanici, ZimmetLog


# ==========================================================================
# DEPARTMAN
# ==========================================================================


class DepartmanSerializer(serializers.ModelSerializer):
    """Departman CRUD serializer'ı."""

    class Meta:
        model = Departman
        fields = ['id', 'ad', 'aciklama']


# ==========================================================================
# KULLANICI
# ==========================================================================


class KullaniciSerializer(serializers.ModelSerializer):
    """Kullanıcı okuma serializer'ı."""

    departman_ad = serializers.CharField(
        source='departman.ad',
        read_only=True,
        default=None,
    )

    class Meta:
        model = Kullanici
        fields = [
            'id', 'email', 'ad', 'soyad', 'rol',
            'departman', 'departman_ad', 'is_active', 'kayit_tarihi',
        ]
        read_only_fields = ['id', 'kayit_tarihi']


class KullaniciCreateSerializer(serializers.ModelSerializer):
    """Kullanıcı oluşturma serializer'ı (şifre dahil)."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Kullanici
        fields = [
            'id', 'email', 'ad', 'soyad', 'rol',
            'departman', 'password',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Kullanici(**validated_data)
        user.set_password(password)
        user.save()
        return user


# ==========================================================================
# DONANIM
# ==========================================================================


class DonanimSerializer(serializers.ModelSerializer):
    """Donanım CRUD serializer'ı."""

    zimmetli_kullanici_ad = serializers.CharField(
        source='zimmetli_kullanici.tam_ad',
        read_only=True,
        default=None,
    )
    durum_display = serializers.CharField(
        source='get_durum_display',
        read_only=True,
    )
    garanti_durumu = serializers.CharField(read_only=True)

    class Meta:
        model = Donanim
        fields = [
            'id', 'seri_no', 'marka', 'model_adi', 'kategori',
            'durum', 'durum_display',
            'zimmetli_kullanici', 'zimmetli_kullanici_ad',
            'garanti_bitis_tarihi', 'garanti_durumu',
            'olusturma_tarihi', 'guncelleme_tarihi',
        ]
        read_only_fields = [
            'id', 'durum', 'zimmetli_kullanici',
            'olusturma_tarihi', 'guncelleme_tarihi',
        ]


class DonanimZimmetSerializer(serializers.Serializer):
    """Donanım zimmetleme isteği için serializer."""

    kullanici_id = serializers.IntegerField()
    aciklama = serializers.CharField(required=False, default='')

    def validate_kullanici_id(self, value):
        if not Kullanici.objects.filter(pk=value, is_active=True).exists():
            raise serializers.ValidationError('Geçerli ve aktif bir kullanıcı ID giriniz.')
        return value


class DonanimDurumGuncelleSerializer(serializers.Serializer):
    """Donanım durum güncelleme isteği için serializer."""

    yeni_durum = serializers.ChoiceField(choices=DonanimDurum.choices)
    aciklama = serializers.CharField(required=False, default='')

    def validate_yeni_durum(self, value):
        donanim = self.context.get('donanim')
        if donanim is None:
            raise serializers.ValidationError('Donanım bulunamadı.')

        mevcut_durum = donanim.durum
        gecerli_hedefler = DONANIM_DURUM_GECISLERI.get(mevcut_durum, [])

        if value not in gecerli_hedefler:
            raise serializers.ValidationError(
                f"'{donanim.get_durum_display()}' durumundan "
                f"'{DonanimDurum(value).label}' durumuna geçiş yapılamaz."
            )

        return value


# ==========================================================================
# DESTEK TALEBİ (TICKET)
# ==========================================================================


class DestekTalebiSerializer(serializers.ModelSerializer):
    """Destek talebi okuma/yazma serializer'ı."""

    olusturan_ad = serializers.CharField(
        source='olusturan.tam_ad',
        read_only=True,
    )
    atanan_it_uzmani_ad = serializers.CharField(
        source='atanan_it_uzmani.tam_ad',
        read_only=True,
        default=None,
    )
    durum_display = serializers.CharField(
        source='get_durum_display',
        read_only=True,
    )
    kategori_display = serializers.CharField(
        source='get_kategori_display',
        read_only=True,
    )
    aciliyet_display = serializers.CharField(
        source='get_aciliyet_display',
        read_only=True,
    )

    class Meta:
        model = DestekTalebi
        fields = [
            'id', 'baslik', 'aciklama',
            'kategori', 'kategori_display',
            'aciliyet', 'aciliyet_display',
            'durum', 'durum_display',
            'olusturan', 'olusturan_ad',
            'atanan_it_uzmani', 'atanan_it_uzmani_ad',
            'ilgili_donanim',
            'olusturma_tarihi', 'guncelleme_tarihi',
        ]
        read_only_fields = [
            'id', 'durum', 'olusturan', 'atanan_it_uzmani',
            'olusturma_tarihi', 'guncelleme_tarihi',
        ]


class TicketDurumGuncelleSerializer(serializers.Serializer):
    """Bilet durum güncelleme isteği için serializer."""

    yeni_durum = serializers.ChoiceField(choices=[
        c for c in DestekTalebi._meta.get_field('durum').choices
    ])

    def validate_yeni_durum(self, value):
        ticket = self.context.get('ticket')
        if ticket is None:
            raise serializers.ValidationError('Bilet bulunamadı.')

        mevcut_durum = ticket.durum
        gecerli_hedefler = TICKET_DURUM_GECISLERI.get(mevcut_durum, [])

        if value not in gecerli_hedefler:
            from core.constants import TicketDurum as TD

            raise serializers.ValidationError(
                f"'{TD(mevcut_durum).label}' durumundan "
                f"'{TD(value).label}' durumuna geçiş yapılamaz."
            )

        return value


# ==========================================================================
# ZİMMET LOG
# ==========================================================================


class ZimmetLogSerializer(serializers.ModelSerializer):
    """Zimmet log okuma serializer'ı (salt okunur)."""

    donanim_bilgi = serializers.CharField(
        source='donanim.__str__',
        read_only=True,
    )
    islem_turu_display = serializers.CharField(
        source='get_islem_turu_display',
        read_only=True,
    )
    islem_yapan_ad = serializers.CharField(
        source='islem_yapan.tam_ad',
        read_only=True,
    )
    eski_kullanici_ad = serializers.CharField(
        source='eski_kullanici.tam_ad',
        read_only=True,
        default=None,
    )
    yeni_kullanici_ad = serializers.CharField(
        source='yeni_kullanici.tam_ad',
        read_only=True,
        default=None,
    )

    class Meta:
        model = ZimmetLog
        fields = [
            'id', 'donanim', 'donanim_bilgi',
            'islem_turu', 'islem_turu_display',
            'eski_kullanici', 'eski_kullanici_ad',
            'yeni_kullanici', 'yeni_kullanici_ad',
            'islem_yapan', 'islem_yapan_ad',
            'aciklama', 'islem_tarihi',
        ]
        read_only_fields = fields
