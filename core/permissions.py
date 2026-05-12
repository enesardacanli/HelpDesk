"""
Rol Bazlı Erişim Kontrolü (RBAC) — Custom DRF Permission Sınıfları.

Her permission sınıfı, ilgili rolün erişim sınırlarını tanımlar.
"""

from rest_framework.permissions import BasePermission

from core.constants import Rol


class IsAdmin(BasePermission):
    """Yalnızca Admin rolündeki kullanıcılara erişim verir."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.rol == Rol.ADMIN
        )


class IsITUzmani(BasePermission):
    """Yalnızca IT Uzmanı rolündeki kullanıcılara erişim verir."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.rol == Rol.IT_UZMANI
        )


class IsITStaff(BasePermission):
    """Admin veya IT Uzmanı rollerinden birine sahip kullanıcılara erişim verir."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.rol in (Rol.ADMIN, Rol.IT_UZMANI)
        )


class IsDepartmanYoneticisi(BasePermission):
    """Yalnızca Departman Yöneticisi rolündeki kullanıcılara erişim verir."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.rol == Rol.DEPARTMAN_YONETICISI
        )


class IsOwnerOrITStaff(BasePermission):
    """
    Nesne sahibi, Admin veya IT Uzmanına erişim verir.

    Nesne üzerindeki 'olusturan' alanı kullanıcıyla eşleşiyorsa
    veya kullanıcı IT Staff ise izin verilir.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.rol in (Rol.ADMIN, Rol.IT_UZMANI):
            return True

        owner_field = getattr(obj, 'olusturan', None)
        return owner_field == request.user


class IsSameDepartman(BasePermission):
    """
    Departman Yöneticisi için departman bazlı izolasyon.

    Nesnenin oluşturanı ile kullanıcının departmanı eşleşmelidir.
    Admin ve IT Uzmanı bu kontrolden muaftır.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.rol in (Rol.ADMIN, Rol.IT_UZMANI):
            return True

        owner = getattr(obj, 'olusturan', None)
        if owner is None:
            return False

        return (
            request.user.departman_id is not None
            and request.user.departman_id == owner.departman_id
        )
