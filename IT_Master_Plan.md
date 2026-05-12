# IT Destek ve Envanter Yönetim Sistemi - Master Plan

> [!NOTE]
> Bu doküman, "IT Destek ve Envanter Yönetim Sistemi" projesinin sıfırdan canlıya alınmasına kadar geçecek süreçteki teknik altyapıyı, mimari kararları ve geliştirme yol haritasını içermektedir.

---

## 1. Veritabanı ve Varlık-İlişki (ER) Mimarisi

Django ORM üzerinde tasarlanacak temel modeller, ilişkiler ve kısıtlar aşağıdaki gibi yapılandırılacaktır:

### Enum Yapıları (Choices)
*   **Roller:** `ADMIN`, `IT_UZMANI`, `DEPARTMAN_YONETICISI`, `STANDART_KULLANICI`
*   **Ticket Durumları:** `YENI`, `ISLEMDE`, `BEKLEMEDE`, `COZULDU`, `KAPATILDI`
*   **Ticket Kategorileri:** `DONANIM`, `YAZILIM`, `AG_ERISIMI`, `DIGER`
*   **Ticket Aciliyet Seviyeleri:** `DUSUK`, `NORMAL`, `YUKSEK`, `KRITIK`
*   **Donanım Durumları:** `DEPODA`, `KULLANIMDA`, `ARIZALI`, `HURDA`

### Modeller ve İlişkiler

1.  **Departman**
    *   `id` (PK)
    *   `ad` (CharField)
    *   `aciklama` (TextField)

2.  **Kullanici (Custom User Model)**
    *   `id` (PK)
    *   `email` (EmailField - Unique)
    *   `ad`, `soyad` (CharField)
    *   `rol` (CharField - Choices)
    *   `departman` (ForeignKey -> Departman, `on_delete=SET_NULL`, null=True)

3.  **Donanim**
    *   `id` (PK)
    *   `seri_no` (CharField - Unique, Index)
    *   `marka`, `model`, `kategori` (CharField)
    *   `durum` (CharField - Choices, Default: `DEPODA`)
    *   `zimmetli_kullanici` (ForeignKey -> Kullanici, `on_delete=SET_NULL`, null=True, related_name='donanimlar')

4.  **DestekTalebi (Ticket)**
    *   `id` (PK)
    *   `baslik` (CharField)
    *   `aciklama` (TextField)
    *   `kategori` (CharField - Choices)
    *   `aciliyet` (CharField - Choices, Default: `NORMAL`)
    *   `durum` (CharField - Choices, Default: `YENI`)
    *   `olusturan` (ForeignKey -> Kullanici, `on_delete=CASCADE`, related_name='acilan_biletler')
    *   `atanan_it_uzmani` (ForeignKey -> Kullanici, `on_delete=SET_NULL`, null=True, related_name='atanan_biletler')
    *   `ilgili_donanim` (ForeignKey -> Donanim, `on_delete=SET_NULL`, null=True)
    *   `olusturma_tarihi`, `guncelleme_tarihi` (DateTimeField)

5.  **ZimmetLog**
    *   `id` (PK)
    *   `donanim` (ForeignKey -> Donanim, `on_delete=CASCADE`)
    *   `islem_turu` (CharField - Choices: `ATAMA`, `IADE`, `DURUM_DEGISIKLIGI`)
    *   `eski_kullanici` (ForeignKey -> Kullanici, null=True)
    *   `yeni_kullanici` (ForeignKey -> Kullanici, null=True)
    *   `islem_yapan` (ForeignKey -> Kullanici, `on_delete=PROTECT`) *(CON-7 Audit gereksinimi)*
    *   `islem_tarihi` (DateTimeField, auto_now_add=True)
    *   `aciklama` (TextField)

---

## 2. Durum Yönetimi (State Machine) Haritaları

Sistemdeki kritik varlıkların durum geçişleri katı kurallara (business logic) bağlanacaktır.

### Destek Talebi (Ticket) State Haritası
*   `YENI` $\rightarrow$ `ISLEMDE` : IT Uzmanı bileti üzerine aldığında.
*   `ISLEMDE` $\rightarrow$ `BEKLEMEDE` : Kullanıcıdan veya tedarikçiden ek bilgi/parça bekleniyorsa.
*   `BEKLEMEDE` $\rightarrow$ `ISLEMDE` : Bilgi/parça temin edildiğinde.
*   `ISLEMDE` $\rightarrow$ `COZULDU` : Sorun IT uzmanı tarafından giderildiğinde.
*   `COZULDU` $\rightarrow$ `KAPATILDI` : Kullanıcı onayı ile veya 3 gün işlem görmezse otomatik.

> [!WARNING]
> Kural: Sadece IT Uzmanı veya Admin bir bileti `KAPATILDI` dışındaki durumlara alabilir. Standart kullanıcı sadece `KAPATILDI` durumuna çekebilir (Eğer çözüm işe yaramadıysa `YENI`'ye döndürebilir).

### Donanım Envanteri State Haritası
*   `DEPODA` $\rightarrow$ `KULLANIMDA` : Kullanıcıya zimmetlendiğinde.
*   `KULLANIMDA` $\rightarrow$ `DEPODA` : Cihaz iade edildiğinde (Zimmet düşürülür).
*   `KULLANIMDA` $\rightarrow$ `ARIZALI` : **(İzin Verilmez!)** Cihaz önce zimmetten düşürülüp `DEPODA` yapılmalı, ardından `ARIZALI` statüsüne alınmalıdır.
*   `DEPODA` $\rightarrow$ `ARIZALI` : Cihaz arızalandığında tespit edilirse.
*   `ARIZALI` $\rightarrow$ `DEPODA` : Tamir işlemi tamamlandığında.
*   `ARIZALI` $\rightarrow$ `HURDA` : Cihaz tamir edilemez (PERT) raporu aldığında. `HURDA` durumu **final state** olup geri dönüşü yoktur.

---

## 3. RESTful API ve Uç Nokta (Endpoint) Tasarımı

Sistem Django REST Framework (DRF) ile geliştirilecek, standart HTTP metodları kullanılacaktır.

### Auth & User Management
*   `POST /api/auth/token/` : Login (JWT Token üretimi)
*   `GET /api/users/me/` : Kendi profilini çekme

### Inventory (Donanım)
*   `GET /api/inventory/` : Donanım listesi (Arama, filtreleme destekli)
*   `POST /api/inventory/` : Yeni donanım ekleme (Sadece IT/Admin)
*   `PUT /api/inventory/{id}/` : Donanım bilgisi güncelleme
*   `POST /api/inventory/{id}/assign/` : Donanımı zimmetleme. *Payload: `{"user_id": 12, "aciklama": "Yeni personel"}`* (ZimmetLog tetikler)
*   `POST /api/inventory/{id}/return/` : Zimmet iadesi.

### Ticket (Destek Talebi)
*   `GET /api/tickets/` : Bilet havuzu (Role göre liste döner)
*   `POST /api/tickets/` : Yeni bilet oluşturma. *Payload: `{"baslik": "...", "aciklama": "...", "donanim_id": 4}`*
*   `PATCH /api/tickets/{id}/status/` : Durum güncelleme. *Payload: `{"durum": "ISLEMDE"}`*
*   `PATCH /api/tickets/{id}/assign/` : Bileti üstüne alma (IT Uzmanı)

---

## 4. RBAC (Rol Bazlı Erişim Kontrolü) ve Güvenlik

Yetkilendirme DRF Permissions (Custom Permission sınıfları) üzerinden yürütülecektir.

*   **Admin:** Tüm okuma/yazma/silme yetkilerine (CRUD) sahiptir. `IsAdminUser` permission sınıfı kullanılır.
*   **IT Uzmanı:** Kullanıcıları okuyabilir, Envanter üzerinde CRUD yapabilir, tüm Ticket'ları görebilir ve yönetebilir. (KG-3)
*   **Departman Yöneticisi:** Sadece kendi departmanındaki (`user.departman_id == ticket.olusturan.departman_id`) biletleri görebilir, sadece departmanına ait envanter raporlarını okuyabilir. (KG-6)
*   **Standart Kullanıcı:** Sadece `olusturan=self.request.user` olan biletleri görebilir. Sadece kendi üzerindeki zimmetli donanımları görebilir. (KG-2)

> [!IMPORTANT]
> İzolasyon (Tenant-like Isolation): Queryset filtrelemesi override edilecek. `get_queryset()` metodunda `if user.rol == STANDART_KULLANICI: return queryset.filter(olusturan=user)` mantığı zorunlu kılınacaktır.

---

## 5. Frontend Mimari Haritası (HTML / Tailwind CSS)

Arayüz "Vanilla JS + HTML + Tailwind CSS" (veya template engine olarak Django Templates) yapısıyla modern bir şekilde tasarlanacaktır.

### Temel View'lar (Sayfalar)
1.  **Dashboard (`/dashboard`)**:
    *   Role göre değişen metrik kartları (Örn: "Bekleyen Biletler", "Depodaki Boş Cihazlar").
    *   Son aktiviteler log tablosu (ZimmetLog).
2.  **Envanter Yönetimi (`/inventory`)**:
    *   Tailwind ile tasarlanmış gelişmiş Data Table (Arama, Kategori Filtresi, Durum Badge'leri).
    *   Satır içi aksiyonlar: "Zimmetle", "İade Al", "Arızalı Bildir" (Modal üzerinden).
3.  **Bilet Havuzu (`/tickets`)**:
    *   Kanban Board (Yeni -> İşlemde -> Çözüldü kolonları) IT uzmanları için.
    *   Standart kullanıcılar için basit liste (Accordion veya Modal ile detay görme).
4.  **Zimmet Geçmişi (`/logs`)**: Salt okunur, denetim (audit) amaçlı log listesi.

---

## 6. Edge Case Analizi ve Kısıt Yönetimi

*   **CON-7 (Onaysız Zimmetleme & Audit):** Kullanıcı onayı beklenmediği için IT uzmanı bir cihazı anında zimmetleyebilir. Kötüye kullanımı engellemek için `ZimmetLog` tablosu `islem_yapan` alanıyla birlikte asenkron veya veritabanı trigger'ı (Django Signal) ile kesin olarak kaydedilir. Bu tablo uygulamanın hiçbir yerinden silinemez (Append-only).
*   **KG-1 (Performans Hedefi):** Dashboard ve Envanter listesindeki N+1 Query problemini çözmek için Django'da `select_related('zimmetli_kullanici', 'ilgili_donanim')` kullanılacaktır. Veritabanı indeksleri (`seri_no`, `durum`) eklenecektir.
*   **Concurrency (Eşzamanlılık):** Aynı anda iki IT uzmanı aynı boş cihazı farklı kişilere zimmetlemeye çalışırsa sistemin çökmemesi veya mükerrer işlem olmaması için zimmet atama endpoint'inde `select_for_update()` ile veritabanı satır kilidi (Row Level Lock) kullanılacaktır.

---

## 7. Aşama Aşama Geliştirme Yol Haritası (Roadmap)

### Faz 1: Core Altyapı & Veritabanı (Hafta 1)
*   Django projesinin kurulması ve konfigürasyon.
*   Custom User Model ve Departman, Donanim, DestekTalebi, ZimmetLog modellerinin kodlanması.
*   RBAC yetki sınıflarının (Permissions) DRF tarafında oluşturulması.
*   JWT Auth sisteminin entegrasyonu.

### Faz 2: Envanter & Zimmet Yönetimi (Hafta 2)
*   Envanter CRUD API uç noktalarının yazılması.
*   Zimmetleme (Assign) ve İade (Return) iş mantığının (Business Logic) yazılması.
*   Django Signals ile ZimmetLog otomasyonunun bağlanması.
*   Transaction ve Lock mekanizmalarının eklenmesi.

### Faz 3: Helpdesk (Bilet) Sistemi (Hafta 3)
*   Ticket CRUD API uç noktalarının oluşturulması.
*   State Machine (Durum geçiş) kısıtlarının backend seviyesinde yazılması.
*   Biletlere donanım bağlama ve yorum/durum güncelleme özelliklerinin eklenmesi.

### Faz 4: Frontend Geliştirme (Hafta 4)
*   HTML/Tailwind CSS şablonlarının oluşturulması (Dashboard, Login, Envanter, Biletler).
*   JavaScript (Fetch/Axios) ile Backend API entegrasyonu.
*   Modal, Tablo, Form Validasyonları ve Toast Notification (Hata/Başarı) UI etkileşimlerinin eklenmesi.

### Faz 5: Kalite Güvence & Canlıya Alım (Hafta 5)
*   Uçtan uca (E2E) iş akışı testleri.
*   Performans testleri (KG-1 için sorgu optimizasyonlarının doğrulanması).
*   Master dataların (Departmanlar, Kategoriler) veritabanına Seed edilmesi.
*   Prod ortama (Örn: Gunicorn + Nginx + PostgreSQL) deploy edilmesi.
