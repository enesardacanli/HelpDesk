"""
Sistem genelinde kullanılan sabit değerler ve Enum tanımları.

Tüm magic string'ler burada merkezi olarak tanımlanır.
"""

from django.db import models


class Rol(models.TextChoices):
    """Sistemdeki kullanıcı rolleri."""

    ADMIN = 'ADMIN', 'Admin'
    IT_UZMANI = 'IT_UZMANI', 'IT Uzmanı'
    DEPARTMAN_YONETICISI = 'DEPARTMAN_YONETICISI', 'Departman Yöneticisi'
    STANDART_KULLANICI = 'STANDART_KULLANICI', 'Standart Kullanıcı'


class TicketDurum(models.TextChoices):
    """Destek talebinin yaşam döngüsü durumları."""

    YENI = 'YENI', 'Yeni'
    ISLEMDE = 'ISLEMDE', 'İşlemde'
    BEKLEMEDE = 'BEKLEMEDE', 'Beklemede'
    COZULDU = 'COZULDU', 'Çözüldü'
    KAPATILDI = 'KAPATILDI', 'Kapatıldı'


class TicketKategori(models.TextChoices):
    """Destek talebinin kategorisi."""

    DONANIM = 'DONANIM', 'Donanım'
    YAZILIM = 'YAZILIM', 'Yazılım'
    AG_ERISIMI = 'AG_ERISIMI', 'Ağ / Erişim'
    DIGER = 'DIGER', 'Diğer'


class TicketAciliyet(models.TextChoices):
    """Destek talebinin aciliyet seviyesi."""

    DUSUK = 'DUSUK', 'Düşük'
    NORMAL = 'NORMAL', 'Normal'
    YUKSEK = 'YUKSEK', 'Yüksek'
    KRITIK = 'KRITIK', 'Kritik'


class DonanimDurum(models.TextChoices):
    """Donanım envanterinin yaşam döngüsü durumları."""

    DEPODA = 'DEPODA', 'Depoda'
    KULLANIMDA = 'KULLANIMDA', 'Kullanımda'
    ARIZALI = 'ARIZALI', 'Arızalı'
    HURDA = 'HURDA', 'Hurda'


class ZimmetIslemTuru(models.TextChoices):
    """Zimmet log kaydı için işlem türleri."""

    ATAMA = 'ATAMA', 'Zimmet Atama'
    IADE = 'IADE', 'Zimmet İade'
    DURUM_DEGISIKLIGI = 'DURUM_DEGISIKLIGI', 'Durum Değişikliği'


# ==========================================================================
# DURUM GEÇİŞ KURALLARI (State Machine)
# ==========================================================================

# Her durumdan geçiş yapılabilecek durumların listesi.
TICKET_DURUM_GECISLERI: dict[str, list[str]] = {
    TicketDurum.YENI: [TicketDurum.ISLEMDE],
    TicketDurum.ISLEMDE: [TicketDurum.BEKLEMEDE, TicketDurum.COZULDU],
    TicketDurum.BEKLEMEDE: [TicketDurum.ISLEMDE],
    TicketDurum.COZULDU: [TicketDurum.KAPATILDI, TicketDurum.YENI],
    TicketDurum.KAPATILDI: [],
}

DONANIM_DURUM_GECISLERI: dict[str, list[str]] = {
    DonanimDurum.DEPODA: [DonanimDurum.KULLANIMDA, DonanimDurum.ARIZALI],
    DonanimDurum.KULLANIMDA: [DonanimDurum.DEPODA],
    DonanimDurum.ARIZALI: [DonanimDurum.DEPODA, DonanimDurum.HURDA],
    DonanimDurum.HURDA: [],  # Final state — geri dönüş yok
}

# ==========================================================================
# SLA HEDEFLERİ (saat cinsinden)
# ==========================================================================

SLA_HEDEFLERI: dict[str, int] = {
    TicketAciliyet.KRITIK: 4,
    TicketAciliyet.YUKSEK: 8,
    TicketAciliyet.NORMAL: 24,
    TicketAciliyet.DUSUK: 72,
}
