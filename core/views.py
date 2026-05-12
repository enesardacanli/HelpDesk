"""
IT Destek ve Envanter Yönetim Sistemi — API ViewSet'leri.

Tüm Use Case'leri (UC-01 ~ UC-12) karşılayan endpoint iş mantığı burada yer alır.
"""

from django.db import transaction
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.constants import (
    DonanimDurum,
    Rol,
    TicketDurum,
    ZimmetIslemTuru,
)
from core.models import Departman, DestekTalebi, Donanim, Kullanici, ZimmetLog
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
