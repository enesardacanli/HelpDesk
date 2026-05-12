"""
Seed Data — Veritabanına örnek veriler ekleyen management komutu.

Kullanım: python manage.py seed_data
"""

from django.core.management.base import BaseCommand

from core.constants import (
    DonanimDurum,
    Rol,
    TicketAciliyet,
    TicketDurum,
    TicketKategori,
    ZimmetIslemTuru,
)
from core.models import Departman, DestekTalebi, Donanim, Kullanici, ZimmetLog


class Command(BaseCommand):
    help = 'Veritabanına örnek departman, kullanıcı, donanım ve bilet verileri ekler.'

    def handle(self, *args, **options):
        self.stdout.write('Seed data oluşturuluyor...\n')

        # ── Departmanlar ──
        departmanlar_data = [
            ('Bilgi Teknolojileri', 'IT altyapı ve destek hizmetleri'),
            ('İnsan Kaynakları', 'Personel yönetimi ve işe alım süreçleri'),
            ('Muhasebe', 'Finans ve muhasebe operasyonları'),
            ('Pazarlama', 'Dijital ve geleneksel pazarlama faaliyetleri'),
            ('Hukuk', 'Kurumsal hukuk danışmanlığı'),
        ]

        departmanlar = {}
        for ad, aciklama in departmanlar_data:
            dept, created = Departman.objects.get_or_create(
                ad=ad, defaults={'aciklama': aciklama},
            )
            departmanlar[ad] = dept
            status = 'oluşturuldu' if created else 'zaten mevcut'
            self.stdout.write(f'  Departman: {ad} — {status}')

        # ── Kullanıcılar ──
        kullanicilar_data = [
            ('it_uzman@helpdesk.local', 'Ahmet', 'Yılmaz', Rol.IT_UZMANI, 'Bilgi Teknolojileri'),
            ('it_uzman2@helpdesk.local', 'Zeynep', 'Kara', Rol.IT_UZMANI, 'Bilgi Teknolojileri'),
            ('ik_yonetici@helpdesk.local', 'Fatma', 'Demir', Rol.DEPARTMAN_YONETICISI, 'İnsan Kaynakları'),
            ('muhasebe_yonetici@helpdesk.local', 'Mehmet', 'Öztürk', Rol.DEPARTMAN_YONETICISI, 'Muhasebe'),
            ('kullanici1@helpdesk.local', 'Ali', 'Çelik', Rol.STANDART_KULLANICI, 'İnsan Kaynakları'),
            ('kullanici2@helpdesk.local', 'Ayşe', 'Arslan', Rol.STANDART_KULLANICI, 'Muhasebe'),
            ('kullanici3@helpdesk.local', 'Emre', 'Şahin', Rol.STANDART_KULLANICI, 'Pazarlama'),
            ('kullanici4@helpdesk.local', 'Selin', 'Koç', Rol.STANDART_KULLANICI, 'Hukuk'),
        ]

        kullanicilar = {}
        for email, ad, soyad, rol, dept_ad in kullanicilar_data:
            if Kullanici.objects.filter(email=email).exists():
                kullanicilar[email] = Kullanici.objects.get(email=email)
                self.stdout.write(f'  Kullanıcı: {email} — zaten mevcut')
                continue

            user = Kullanici.objects.create_user(
                email=email,
                password='Test1234!',
                ad=ad,
                soyad=soyad,
                rol=rol,
                departman=departmanlar.get(dept_ad),
            )
            kullanicilar[email] = user
            self.stdout.write(f'  Kullanıcı: {email} — oluşturuldu')

        # Admin kullanıcısını da referans al
        admin_user = Kullanici.objects.filter(rol=Rol.ADMIN).first()
        it_uzman = kullanicilar.get('it_uzman@helpdesk.local')

        # ── Donanımlar ──
        donanimlar_data = [
            ('SN-LP-001', 'Lenovo', 'ThinkPad T14s', 'Laptop'),
            ('SN-LP-002', 'Dell', 'Latitude 5540', 'Laptop'),
            ('SN-LP-003', 'HP', 'EliteBook 840 G10', 'Laptop'),
            ('SN-LP-004', 'Apple', 'MacBook Pro 14"', 'Laptop'),
            ('SN-LP-005', 'Lenovo', 'ThinkPad X1 Carbon', 'Laptop'),
            ('SN-MN-001', 'Dell', 'UltraSharp U2723QE', 'Monitör'),
            ('SN-MN-002', 'LG', '27UK850-W', 'Monitör'),
            ('SN-MN-003', 'Samsung', 'Odyssey G5', 'Monitör'),
            ('SN-PR-001', 'HP', 'LaserJet Pro M404dn', 'Yazıcı'),
            ('SN-PR-002', 'Brother', 'MFC-L3770CDW', 'Yazıcı'),
            ('SN-KB-001', 'Logitech', 'MX Keys', 'Klavye'),
            ('SN-MS-001', 'Logitech', 'MX Master 3S', 'Mouse'),
            ('SN-HS-001', 'Jabra', 'Evolve2 85', 'Kulaklık'),
            ('SN-TB-001', 'Samsung', 'Galaxy Tab S9', 'Tablet'),
            ('SN-SW-001', 'Ubiquiti', 'USW-24-PoE', 'Ağ Ekipmanı'),
        ]

        donanimlar = {}
        for seri_no, marka, model_adi, kategori in donanimlar_data:
            donanim, created = Donanim.objects.get_or_create(
                seri_no=seri_no,
                defaults={
                    'marka': marka,
                    'model_adi': model_adi,
                    'kategori': kategori,
                },
            )
            donanimlar[seri_no] = donanim
            status = 'oluşturuldu' if created else 'zaten mevcut'
            self.stdout.write(f'  Donanım: {seri_no} ({marka} {model_adi}) — {status}')

        # ── Zimmetleme İşlemleri ──
        zimmet_data = [
            ('SN-LP-001', 'kullanici1@helpdesk.local', 'Yeni işe başlayan personel'),
            ('SN-LP-002', 'kullanici2@helpdesk.local', 'Muhasebe departmanı ataması'),
            ('SN-LP-003', 'kullanici3@helpdesk.local', 'Pazarlama ekibi tahsisi'),
            ('SN-MN-001', 'kullanici1@helpdesk.local', 'Çift monitör ihtiyacı'),
            ('SN-KB-001', 'kullanici4@helpdesk.local', 'Ergonomik klavye talebi'),
            ('SN-MS-001', 'kullanici4@helpdesk.local', 'Ergonomik mouse talebi'),
        ]

        islem_yapan = it_uzman or admin_user
        for seri_no, email, aciklama in zimmet_data:
            donanim = donanimlar.get(seri_no)
            kullanici = kullanicilar.get(email)
            if not donanim or not kullanici:
                continue
            if donanim.durum != DonanimDurum.DEPODA:
                continue

            donanim.zimmetli_kullanici = kullanici
            donanim.durum = DonanimDurum.KULLANIMDA
            donanim.save()

            ZimmetLog.objects.create(
                donanim=donanim,
                islem_turu=ZimmetIslemTuru.ATAMA,
                eski_kullanici=None,
                yeni_kullanici=kullanici,
                islem_yapan=islem_yapan,
                aciklama=aciklama,
            )
            self.stdout.write(f'  Zimmet: {seri_no} -> {kullanici.tam_ad}')

        # ── Arızalı Cihaz ──
        arizali = donanimlar.get('SN-PR-002')
        if arizali and arizali.durum == DonanimDurum.DEPODA:
            arizali.durum = DonanimDurum.ARIZALI
            arizali.save()
            ZimmetLog.objects.create(
                donanim=arizali,
                islem_turu=ZimmetIslemTuru.DURUM_DEGISIKLIGI,
                islem_yapan=islem_yapan,
                aciklama='DEPODA -> ARIZALI. Kağıt sıkışması sorunu, servis gerekli.',
            )
            self.stdout.write(f'  Arıza: {arizali.seri_no} -> ARIZALI')

        # ── Destek Talepleri ──
        biletler_data = [
            {
                'baslik': 'Laptop ekranı titriyor',
                'aciklama': 'Lenovo ThinkPad T14s ekranında sürekli titreme sorunu yaşıyorum. Harici monitörde sorun yok.',
                'kategori': TicketKategori.DONANIM,
                'aciliyet': TicketAciliyet.YUKSEK,
                'olusturan': 'kullanici1@helpdesk.local',
                'durum': TicketDurum.ISLEMDE,
                'atanan': 'it_uzman@helpdesk.local',
            },
            {
                'baslik': 'VPN bağlantısı kurulamıyor',
                'aciklama': 'Evden çalışırken kurumsal VPN\'e bağlanamıyorum. "Connection timed out" hatası alıyorum.',
                'kategori': TicketKategori.AG_ERISIMI,
                'aciliyet': TicketAciliyet.KRITIK,
                'olusturan': 'kullanici2@helpdesk.local',
                'durum': TicketDurum.YENI,
                'atanan': None,
            },
            {
                'baslik': 'Office 365 lisansı süresi doldu',
                'aciklama': 'Microsoft Office uygulamaları lisans sürenizin dolduğunu bildiriyor, yenilenebilir mi?',
                'kategori': TicketKategori.YAZILIM,
                'aciliyet': TicketAciliyet.NORMAL,
                'olusturan': 'kullanici3@helpdesk.local',
                'durum': TicketDurum.COZULDU,
                'atanan': 'it_uzman2@helpdesk.local',
            },
            {
                'baslik': 'Yazıcıdan çıktı alınamıyor',
                'aciklama': 'HP LaserJet yazıcı yazdırma komutunu alıyor ama hiçbir çıktı vermiyor. Kuyrukta bekliyor.',
                'kategori': TicketKategori.DONANIM,
                'aciliyet': TicketAciliyet.NORMAL,
                'olusturan': 'kullanici4@helpdesk.local',
                'durum': TicketDurum.BEKLEMEDE,
                'atanan': 'it_uzman@helpdesk.local',
            },
            {
                'baslik': 'Yeni çalışan için hesap oluşturma',
                'aciklama': 'Pazarlama departmanına yeni katılan personel için e-posta, AD hesabı ve sistem erişimleri gerekiyor.',
                'kategori': TicketKategori.DIGER,
                'aciliyet': TicketAciliyet.DUSUK,
                'olusturan': 'ik_yonetici@helpdesk.local',
                'durum': TicketDurum.YENI,
                'atanan': None,
            },
            {
                'baslik': 'Dosya sunucusuna erişim hatası',
                'aciklama': 'Paylaşımlı sürücüye (\\\\fileserver\\paylasim) erişmek istediğimde yetki hatası alıyorum.',
                'kategori': TicketKategori.AG_ERISIMI,
                'aciliyet': TicketAciliyet.YUKSEK,
                'olusturan': 'kullanici1@helpdesk.local',
                'durum': TicketDurum.ISLEMDE,
                'atanan': 'it_uzman2@helpdesk.local',
            },
            {
                'baslik': 'SAP sisteminde yetki talebi',
                'aciklama': 'Muhasebe modülünde FA10 ve FA11 raporlarına erişim yetkisi talep ediyorum.',
                'kategori': TicketKategori.YAZILIM,
                'aciliyet': TicketAciliyet.NORMAL,
                'olusturan': 'muhasebe_yonetici@helpdesk.local',
                'durum': TicketDurum.KAPATILDI,
                'atanan': 'it_uzman@helpdesk.local',
            },
        ]

        for bilet_data in biletler_data:
            olusturan = kullanicilar.get(bilet_data['olusturan'])
            if not olusturan:
                continue

            if DestekTalebi.objects.filter(
                baslik=bilet_data['baslik'],
                olusturan=olusturan,
            ).exists():
                self.stdout.write(f'  Bilet: "{bilet_data["baslik"]}" — zaten mevcut')
                continue

            atanan = kullanicilar.get(bilet_data['atanan']) if bilet_data['atanan'] else None
            DestekTalebi.objects.create(
                baslik=bilet_data['baslik'],
                aciklama=bilet_data['aciklama'],
                kategori=bilet_data['kategori'],
                aciliyet=bilet_data['aciliyet'],
                durum=bilet_data['durum'],
                olusturan=olusturan,
                atanan_it_uzmani=atanan,
            )
            self.stdout.write(f'  Bilet: "{bilet_data["baslik"]}" — oluşturuldu')

        self.stdout.write(self.style.SUCCESS('\nSeed data basariyla olusturuldu!'))
        self.stdout.write(self.style.WARNING(
            '\nTum test kullanicilarinin sifresi: Test1234!'
        ))
