# 🖥️ IT Destek ve Envanter Yönetim Sistemi

**Kurumsal BT altyapısı için modern, tam özellikli helpdesk ve envanter yönetim platformu.**

> Django 6 + Django REST Framework + Tailwind CSS + Chart.js · Sıfır konfigürasyon, SQLite tabanlı

---

## 📋 İçindekiler

- [Özellikler](#-özellikler)
- [Teknoloji Yığını](#-teknoloji-yığını)
- [Mimari](#-mimari)
- [Kurulum](#-kurulum)
- [API Dokümantasyonu](#-api-dokümantasyonu)
- [Kullanıcı Rolleri](#-kullanıcı-rolleri)
- [Ekran Görüntüleri](#-ekran-görüntüleri)

---

## ✨ Özellikler

### 🎫 Destek Talebi Yönetimi
- Bilet oluşturma, atama ve durum yönetimi (State Machine)
- **SLA takibi** — aciliyete göre otomatik süre hesaplama (Kritik: 4s, Yüksek: 8s, Normal: 24s, Düşük: 72s)
- **Yorum sistemi** — bilet detayında gerçek zamanlı yorum ekleme
- Aciliyet ve kategori bazlı filtreleme
- Durum geçiş kuralları ile iş akışı kontrolü

### 🖥️ Envanter Yönetimi
- Donanım CRUD işlemleri (Seri No, Marka, Model, Kategori)
- **Garanti takibi** — garanti bitiş tarihi ve otomatik durum badge'i
- Zimmetleme ve iade sistemi
- Donanım durum yönetimi (Depoda → Kullanımda → Arızalı → Hurda)

### 📊 Dashboard & Raporlama
- Anlık metrikler (Toplam Bilet, Envanter, Açık Talepler, Arızalı Cihazlar)
- **Chart.js grafikleri** — Kategori Dağılımı (Doughnut) + Durum Dağılımı (Bar)
- Son destek talepleri ve zimmet hareketleri
- **CSV dışa aktarma** — Bilet ve envanter verileri

### 🎨 Modern UI/UX
- **Dark Mode** — localStorage ile kalıcı tema tercihi
- Glassmorphism login sayfası
- Responsive tasarım (Mobile + Desktop)
- Lucide ikonları ve mikro-animasyonlar
- Toast bildirim sistemi

### 🔐 Güvenlik
- JWT tabanlı kimlik doğrulama (Access + Refresh Token)
- **Token Blacklist** ile güvenli çıkış
- Ortam değişkenleri ile hassas veri yönetimi (python-decouple)
- Rol tabanlı erişim kontrolü (RBAC)

### 📜 Denetim & İzlenebilirlik
- Append-only zimmet log sistemi (düzenlenemez, silinemez)
- **Aktivite geçmişi** — kullanıcı bazlı kronolojik timeline
- Tüm zimmet hareketlerinin kayıt altına alınması

---

## 🛠️ Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| **Backend** | Python 3.12+, Django 6.0, Django REST Framework 3.17 |
| **Veritabanı** | SQLite (sıfır konfigürasyon) |
| **Kimlik Doğrulama** | SimpleJWT + Token Blacklist |
| **Frontend** | HTML5, Tailwind CSS (CDN), Vanilla JavaScript |
| **Grafikler** | Chart.js |
| **İkonlar** | Lucide Icons |
| **Ortam Yönetimi** | python-decouple (.env) |

---

## 🏗️ Mimari

```
Helpdesk/
├── config/              # Proje ayarları ve ana URL konfigürasyonu
│   ├── settings.py      # Django ayarları (decouple ile)
│   └── urls.py          # Ana URL router
├── core/                # Ana uygulama
│   ├── constants.py     # Enum'lar, state machine kuralları, SLA hedefleri
│   ├── models.py        # Kullanici, Donanim, DestekTalebi, TicketYorum, ZimmetLog
│   ├── serializers.py   # DRF Serializer'ları (SLA computed alanları dahil)
│   ├── views.py         # API ViewSet'leri (CRUD, Assign, Export, Activity)
│   ├── permissions.py   # Özel izin sınıfları (IsAdmin, IsITStaff)
│   ├── urls.py          # API router
│   └── frontend_views.py # Template view'ları
├── templates/           # Django template'leri
│   ├── base.html        # Ana layout (sidebar, dark mode, toast)
│   ├── login.html       # Giriş sayfası
│   ├── dashboard.html   # Dashboard + grafikler
│   ├── tickets.html     # Bilet yönetimi
│   ├── inventory.html   # Envanter yönetimi
│   ├── logs.html        # Zimmet logları
│   └── activity.html    # Aktivite geçmişi
├── .env                 # Ortam değişkenleri (git'e dahil değil)
├── .env.example         # Ortam değişkenleri şablonu
├── requirements.txt     # Python bağımlılıkları
└── manage.py
```

---

## 🚀 Kurulum

### Gereksinimler
- Python 3.12+
- pip

### Adımlar

```bash
# 1. Repoyu klonlayın
git clone https://github.com/enesardacanli/HelpDesk.git
cd HelpDesk

# 2. Sanal ortam oluşturun
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 4. Ortam değişkenlerini ayarlayın
cp .env.example .env
# .env dosyasını düzenleyin (SECRET_KEY otomatik oluşturulur)

# 5. Veritabanını hazırlayın
python manage.py migrate

# 6. Süper kullanıcı oluşturun
python manage.py createsuperuser

# 7. Sunucuyu başlatın
python manage.py runserver
```

Tarayıcıda `http://127.0.0.1:8000` adresini açın.

---

## 📡 API Dokümantasyonu

### Kimlik Doğrulama
| Endpoint | Metod | Açıklama |
|----------|-------|----------|
| `/api/auth/token/` | POST | JWT token al |
| `/api/auth/token/refresh/` | POST | Access token yenile |
| `/api/auth/logout/` | POST | Refresh token'ı blacklist'e ekle |

### Destek Talepleri
| Endpoint | Metod | Açıklama |
|----------|-------|----------|
| `/api/tickets/` | GET/POST | Bilet listele / oluştur |
| `/api/tickets/{id}/` | GET/PUT/DELETE | Bilet detay / güncelle / sil |
| `/api/tickets/{id}/status/` | PATCH | Durum güncelle (state machine) |
| `/api/tickets/{id}/assign/` | PATCH | Bileti üstlen |
| `/api/tickets/{id}/comments/` | GET/POST | Yorum listele / ekle |
| `/api/tickets/export/` | GET | CSV dışa aktar |

### Envanter
| Endpoint | Metod | Açıklama |
|----------|-------|----------|
| `/api/inventory/` | GET/POST | Donanım listele / ekle |
| `/api/inventory/{id}/` | GET/PUT/DELETE | Donanım detay / güncelle / sil |
| `/api/inventory/{id}/zimmetle/` | POST | Donanım zimmetle |
| `/api/inventory/{id}/iade/` | POST | Zimmet iade et |
| `/api/inventory/{id}/durum/` | PATCH | Durum güncelle |
| `/api/inventory/export/` | GET | CSV dışa aktar |

### Diğer
| Endpoint | Metod | Açıklama |
|----------|-------|----------|
| `/api/activity/` | GET | Aktivite timeline |
| `/api/logs/` | GET | Zimmet logları |
| `/api/kullanicilar/` | GET/POST | Kullanıcı yönetimi |
| `/api/departmanlar/` | GET/POST | Departman yönetimi |

---

## 👥 Kullanıcı Rolleri

| Rol | Yetkiler |
|-----|----------|
| **Admin** | Tam yetki — tüm CRUD, kullanıcı yönetimi, CSV export |
| **IT Uzmanı** | Bilet yönetimi, envanter CRUD, zimmetleme, CSV export |
| **Departman Yöneticisi** | Departman biletlerini görüntüleme, zimmet logları |
| **Standart Kullanıcı** | Kendi biletlerini oluşturma/görüntüleme, yorum ekleme |

---

## 📸 Ekran Görüntüleri

### Login Sayfası
Glassmorphism tasarımlı, responsive giriş ekranı.

### Dashboard
Anlık metrikler, Chart.js grafikleri ve son aktiviteler.

### Bilet Yönetimi
SLA badge'leri, yorum sistemi ve durum yönetimi.

### Envanter
Garanti takibi, zimmetleme ve CSV export.

### Dark Mode
Tüm sayfalarda tam dark mode desteği.

---

## 📝 Lisans

Bu proje eğitim amaçlı geliştirilmiştir.

---

## 👨‍💻 Geliştirici

**Enes Arda Canlı**
- GitHub: [@enesardacanli](https://github.com/enesardacanli)
