"""
Core uygulama URL tanımları.

Tüm API uç noktaları DRF Router aracılığıyla otomatik oluşturulur.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from core.views import (
    ActivityTimelineView,
    DepartmanViewSet,
    DestekTalebiViewSet,
    DonanimViewSet,
    KullaniciViewSet,
    ZimmetLogViewSet,
)

router = DefaultRouter()
router.register(r'departmanlar', DepartmanViewSet, basename='departman')
router.register(r'kullanicilar', KullaniciViewSet, basename='kullanici')
router.register(r'inventory', DonanimViewSet, basename='donanim')
router.register(r'tickets', DestekTalebiViewSet, basename='destek-talebi')
router.register(r'logs', ZimmetLogViewSet, basename='zimmet-log')
router.register(r'activity', ActivityTimelineView, basename='activity')

urlpatterns = [
    path('', include(router.urls)),
]
