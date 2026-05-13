"""
IT Destek ve Envanter Yönetim Sistemi — API ViewSet'leri.

Tüm Use Case'leri (UC-01 ~ UC-12) karşılayan endpoint iş mantığı burada yer alır.
"""

import csv

from django.http import HttpResponse
from django.db import transaction
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken


class LogoutView(APIView):
    """Refresh token'i blacklist'e ekleyerek guvenli cikis saglar."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token gerekli.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {'detail': 'Gecersiz veya suresi dolmus token.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {'detail': 'Basariyla cikis yapildi.'},
            status=status.HTTP_200_OK,
        )


from core.constants import (
    DonanimDurum,
    Rol,
    TicketDurum,
    ZimmetIslemTuru,
)
from core.models import (
    Departman, DestekTalebi, Donanim, Kullanici, TicketYorum, ZimmetLog,
)
from core.permissions import IsAdmin, IsITStaff
from core.serializers import (
    DepartmanSerializer,
    DestekTalebiSerializer,
    DonanimDurumGuncelleSerializer,
    DonanimSerializer,
    DonanimZimmetSerializer,
    KullaniciCreateSerializer,
    KullaniciSerializer,
    TicketDurumGuncelleSerializer,
    TicketYorumSerializer,
    ZimmetLogSerializer,
)


# ==========================================================================
# DEPARTMAN
# ==========================================================================


class DepartmanViewSet(viewsets.ModelViewSet):
    """
    Departman CRUD işlemleri.

    Sadece Admin oluşturabilir/güncelleyebilir/silebilir.
    Tüm giriş yapmış kullanıcılar listeleyebilir.
    """

    queryset = Departman.objects.all()
    serializer_class = DepartmanSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdmin()]
        return [IsAuthenticated()]


# ==========================================================================
# KULLANICI
# ==========================================================================


class KullaniciViewSet(viewsets.ModelViewSet):
    """
    Kullanıcı yönetimi.

    - Admin: Tam CRUD.
    - IT Uzmanı: Sadece okuma.
    - Diğerleri: Sadece kendi profilini görme (/me endpoint).
    """

    queryset = Kullanici.objects.select_related('departman').all()

    def get_serializer_class(self):
        if self.action == 'create':
            return KullaniciCreateSerializer
        return KullaniciSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdmin()]
        if self.action in ('list', 'retrieve'):
            return [IsITStaff()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """Giriş yapmış kullanıcının kendi profil bilgisini döndürür."""
        serializer = KullaniciSerializer(request.user)
        return Response(serializer.data)


# ==========================================================================
# DONANIM (Envanter)
# ==========================================================================


class DonanimViewSet(viewsets.ModelViewSet):
    """
    Donanım envanter yönetimi.

    - Admin / IT Uzmanı: Tam CRUD + Zimmetleme + İade + Durum güncelleme.
    - Departman Yöneticisi: Departmanındaki donanımları okuyabilir.
    - Standart Kullanıcı: Sadece üzerine zimmetli donanımları görebilir.
    """

    serializer_class = DonanimSerializer
    filterset_fields = ['durum', 'kategori', 'marka']
    search_fields = ['seri_no', 'marka', 'model_adi']
    ordering_fields = ['olusturma_tarihi', 'marka']

    def get_queryset(self):
        user = self.request.user
        base_qs = Donanim.objects.select_related('zimmetli_kullanici')

        if user.rol in (Rol.ADMIN, Rol.IT_UZMANI):
            return base_qs.all()

        if user.rol == Rol.DEPARTMAN_YONETICISI:
            return base_qs.filter(
                zimmetli_kullanici__departman=user.departman,
            )

        # Standart Kullanıcı — sadece kendi zimmetli donanımları
        return base_qs.filter(zimmetli_kullanici=user)

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsITStaff()]
        return [IsAuthenticated()]

    # ------------------------------------------------------------------
    # Zimmetleme (Assign)
    # ------------------------------------------------------------------

    @action(detail=True, methods=['post'], url_path='assign')
    def zimmetle(self, request, pk=None):
        """
        Donanımı bir kullanıcıya zimmetler.

        Race condition koruması için select_for_update kullanılır.
        """
        serializer = DonanimZimmetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        kullanici_id = serializer.validated_data['kullanici_id']
        aciklama = serializer.validated_data.get('aciklama', '')

        with transaction.atomic():
            donanim = (
                Donanim.objects
                .select_for_update()
                .get(pk=pk)
            )

            if donanim.durum != DonanimDurum.DEPODA:
                return Response(
                    {'detail': 'Sadece depodaki donanımlar zimmetlenebilir.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            hedef_kullanici = Kullanici.objects.get(pk=kullanici_id)
            eski_kullanici = donanim.zimmetli_kullanici

            donanim.zimmetli_kullanici = hedef_kullanici
            donanim.durum = DonanimDurum.KULLANIMDA
            donanim.save()

            ZimmetLog.objects.create(
                donanim=donanim,
                islem_turu=ZimmetIslemTuru.ATAMA,
                eski_kullanici=eski_kullanici,
                yeni_kullanici=hedef_kullanici,
                islem_yapan=request.user,
                aciklama=aciklama,
            )

        return Response(
            DonanimSerializer(donanim).data,
            status=status.HTTP_200_OK,
        )

    # ------------------------------------------------------------------
    # İade (Return)
    # ------------------------------------------------------------------

    @action(detail=True, methods=['post'], url_path='return')
    def iade(self, request, pk=None):
        """Zimmetli donanımı iade alır ve depoya geri çeker."""
        with transaction.atomic():
            donanim = (
                Donanim.objects
                .select_for_update()
                .get(pk=pk)
            )

            if donanim.durum != DonanimDurum.KULLANIMDA:
                return Response(
                    {'detail': 'Sadece kullanımda olan donanımlar iade alınabilir.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            eski_kullanici = donanim.zimmetli_kullanici
            donanim.zimmetli_kullanici = None
            donanim.durum = DonanimDurum.DEPODA
            donanim.save()

            ZimmetLog.objects.create(
                donanim=donanim,
                islem_turu=ZimmetIslemTuru.IADE,
                eski_kullanici=eski_kullanici,
                yeni_kullanici=None,
                islem_yapan=request.user,
                aciklama=request.data.get('aciklama', ''),
            )

        return Response(
            DonanimSerializer(donanim).data,
            status=status.HTTP_200_OK,
        )

    # ------------------------------------------------------------------
    # Durum Güncelleme
    # ------------------------------------------------------------------

    @action(detail=True, methods=['patch'], url_path='durum')
    def durum_guncelle(self, request, pk=None):
        """Donanım durumunu state machine kurallarına uygun olarak günceller."""
        donanim = self.get_object()
        serializer = DonanimDurumGuncelleSerializer(
            data=request.data,
            context={'donanim': donanim},
        )
        serializer.is_valid(raise_exception=True)

        yeni_durum = serializer.validated_data['yeni_durum']
        aciklama = serializer.validated_data.get('aciklama', '')

        with transaction.atomic():
            donanim = (
                Donanim.objects
                .select_for_update()
                .get(pk=pk)
            )
            eski_durum = donanim.durum
            donanim.durum = yeni_durum
            donanim.save()

            ZimmetLog.objects.create(
                donanim=donanim,
                islem_turu=ZimmetIslemTuru.DURUM_DEGISIKLIGI,
                eski_kullanici=donanim.zimmetli_kullanici,
                yeni_kullanici=donanim.zimmetli_kullanici,
                islem_yapan=request.user,
                aciklama=f'{eski_durum} → {yeni_durum}. {aciklama}'.strip(),
            )

        return Response(
            DonanimSerializer(donanim).data,
            status=status.HTTP_200_OK,
        )

    # ------------------------------------------------------------------
    # CSV Export
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'], url_path='export')
    def export_csv(self, request):
        """Envanter verilerini CSV olarak disari aktarir."""
        if request.user.rol not in (Rol.ADMIN, Rol.IT_UZMANI):
            return Response({'detail': 'Yetki yok.'}, status=status.HTTP_403_FORBIDDEN)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="envanter.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Seri No', 'Marka', 'Model', 'Kategori', 'Durum', 'Garanti Bitis', 'Zimmetli'])
        for d in self.get_queryset():
            writer.writerow([
                d.id, d.seri_no, d.marka, d.model_adi, d.kategori,
                d.get_durum_display(),
                d.garanti_bitis_tarihi.strftime('%d.%m.%Y') if d.garanti_bitis_tarihi else '',
                d.zimmetli_kullanici.tam_ad if d.zimmetli_kullanici else '',
            ])
        return response


# ==========================================================================
# DESTEK TALEBİ (TICKET)
# ==========================================================================


class DestekTalebiViewSet(viewsets.ModelViewSet):
    """
    Destek talebi (ticket) yönetimi.

    - Admin / IT Uzmanı: Tüm biletleri görebilir ve yönetebilir.
    - Departman Yöneticisi: Kendi departmanındaki biletleri görebilir.
    - Standart Kullanıcı: Sadece kendi oluşturduğu biletleri görebilir.
    """

    serializer_class = DestekTalebiSerializer
    filterset_fields = ['durum', 'kategori', 'aciliyet', 'atanan_it_uzmani']
    search_fields = ['baslik', 'aciklama']
    ordering_fields = ['olusturma_tarihi', 'aciliyet']

    def get_queryset(self):
        user = self.request.user
        base_qs = DestekTalebi.objects.select_related(
            'olusturan',
            'atanan_it_uzmani',
            'ilgili_donanim',
        )

        if user.rol in (Rol.ADMIN, Rol.IT_UZMANI):
            return base_qs.all()

        if user.rol == Rol.DEPARTMAN_YONETICISI:
            return base_qs.filter(olusturan__departman=user.departman)

        # Standart Kullanıcı — sadece kendi biletleri
        return base_qs.filter(olusturan=user)

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAdmin()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Bilet oluşturulurken olusturan alanını otomatik set eder."""
        serializer.save(olusturan=self.request.user)

    # ------------------------------------------------------------------
    # Durum Güncelleme
    # ------------------------------------------------------------------

    @action(detail=True, methods=['patch'], url_path='status')
    def durum_guncelle(self, request, pk=None):
        """
        Bilet durumunu state machine kurallarına uygun olarak günceller.

        Standart kullanıcı sadece KAPATILDI veya YENI'ye çekebilir.
        """
        ticket = self.get_object()
        user = request.user

        # Standart kullanıcı kısıtı
        if user.rol == Rol.STANDART_KULLANICI:
            allowed = {TicketDurum.KAPATILDI, TicketDurum.YENI}
            yeni_durum = request.data.get('yeni_durum')
            if yeni_durum not in allowed:
                return Response(
                    {'detail': 'Bu durum değişikliği için yetkiniz yok.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = TicketDurumGuncelleSerializer(
            data=request.data,
            context={'ticket': ticket},
        )
        serializer.is_valid(raise_exception=True)

        ticket.durum = serializer.validated_data['yeni_durum']
        ticket.save()

        return Response(
            DestekTalebiSerializer(ticket).data,
            status=status.HTTP_200_OK,
        )

    # ------------------------------------------------------------------
    # Bileti Üstlenme (Assign)
    # ------------------------------------------------------------------

    @action(detail=True, methods=['patch'], url_path='assign')
    def ustlen(self, request, pk=None):
        """IT Uzmanının bileti kendi üzerine almasını sağlar."""
        ticket = self.get_object()
        user = request.user

        if user.rol not in (Rol.ADMIN, Rol.IT_UZMANI):
            return Response(
                {'detail': 'Bilet atama yetkisine sahip değilsiniz.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        ticket.atanan_it_uzmani = user

        if ticket.durum == TicketDurum.YENI:
            ticket.durum = TicketDurum.ISLEMDE

        ticket.save()

        return Response(
            DestekTalebiSerializer(ticket).data,
            status=status.HTTP_200_OK,
        )

    # ------------------------------------------------------------------
    # Yorumlar
    # ------------------------------------------------------------------

    @action(detail=True, methods=['get', 'post'], url_path='comments')
    def comments(self, request, pk=None):
        """Bilete yorum listele (GET) veya yorum ekle (POST)."""
        ticket = self.get_object()

        if request.method == 'GET':
            yorumlar = ticket.yorumlar.select_related('yazan').all()
            serializer = TicketYorumSerializer(yorumlar, many=True)
            return Response(serializer.data)

        serializer = TicketYorumSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(ticket=ticket, yazan=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # ------------------------------------------------------------------
    # CSV Export
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'], url_path='export')
    def export_csv(self, request):
        """Tum biletleri CSV olarak disari aktarir (IT Staff only)."""
        if request.user.rol not in (Rol.ADMIN, Rol.IT_UZMANI):
            return Response({'detail': 'Yetki yok.'}, status=status.HTTP_403_FORBIDDEN)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="biletler.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Baslik', 'Kategori', 'Aciliyet', 'Durum', 'Olusturan', 'Atanan', 'Olusturma Tarihi'])
        for t in self.get_queryset():
            writer.writerow([
                t.id, t.baslik, t.get_kategori_display(), t.get_aciliyet_display(),
                t.get_durum_display(), t.olusturan.tam_ad,
                t.atanan_it_uzmani.tam_ad if t.atanan_it_uzmani else '',
                t.olusturma_tarihi.strftime('%d.%m.%Y %H:%M'),
            ])
        return response


# ==========================================================================
# ZİMMET LOG (Audit — Salt Okunur)
# ==========================================================================


class ZimmetLogViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Zimmet log kayıtları (salt okunur denetim tablosu).

    Sadece Admin ve IT Uzmanı tüm logları görebilir.
    Departman Yöneticisi kendi departmanına ait logları görebilir.
    """

    serializer_class = ZimmetLogSerializer
    filterset_fields = ['donanim', 'islem_turu', 'islem_yapan']
    ordering_fields = ['islem_tarihi']

    def get_queryset(self):
        user = self.request.user
        base_qs = ZimmetLog.objects.select_related(
            'donanim',
            'eski_kullanici',
            'yeni_kullanici',
            'islem_yapan',
        )

        if user.rol in (Rol.ADMIN, Rol.IT_UZMANI):
            return base_qs.all()

        if user.rol == Rol.DEPARTMAN_YONETICISI:
            return base_qs.filter(
                donanim__zimmetli_kullanici__departman=user.departman,
            )

        return base_qs.none()

    def get_permissions(self):
        return [IsAuthenticated()]


# ==========================================================================
# AKTİVİTE GEÇMİŞİ
# ==========================================================================


class ActivityTimelineView(viewsets.ViewSet):
    """Kullanıcının tüm aktivitelerini kronolojik timeline olarak döndürür."""

    permission_classes = [IsAuthenticated]

    def list(self, request):
        user = request.user
        events = []

        # Bilet oluşturma
        for t in DestekTalebi.objects.filter(olusturan=user).order_by('-olusturma_tarihi')[:20]:
            events.append({
                'type': 'ticket_created',
                'icon': 'ticket',
                'color': 'brand',
                'title': f'Bilet olusturuldu: {t.baslik}',
                'detail': f'#{t.id} - {t.get_durum_display()}',
                'date': t.olusturma_tarihi.isoformat(),
            })

        # Yorum ekleme
        for y in TicketYorum.objects.filter(yazan=user).select_related('ticket').order_by('-olusturma_tarihi')[:20]:
            events.append({
                'type': 'comment_added',
                'icon': 'message-circle',
                'color': 'emerald',
                'title': f'Yorum eklendi: #{y.ticket_id}',
                'detail': y.icerik[:80],
                'date': y.olusturma_tarihi.isoformat(),
            })

        # Zimmet hareketleri
        for z in ZimmetLog.objects.filter(islem_yapan=user).select_related('donanim').order_by('-islem_tarihi')[:20]:
            events.append({
                'type': 'asset_action',
                'icon': 'monitor',
                'color': 'amber',
                'title': f'{z.get_islem_turu_display()}: {z.donanim}',
                'detail': z.aciklama[:80] if z.aciklama else '',
                'date': z.islem_tarihi.isoformat(),
            })

        events.sort(key=lambda e: e['date'], reverse=True)
        return Response(events[:50])
