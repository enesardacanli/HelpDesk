"""
Proje ana URL konfigürasyonu.

API uç noktaları /api/ altında, JWT auth uç noktaları /api/auth/ altında,
frontend sayfaları kök seviyede sunulur.
"""

from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from core.frontend_views import (
    DashboardView,
    InventoryView,
    LoginView,
    LogsView,
    TicketsView,
)
from core.views import LogoutView

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # JWT Authentication
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/logout/', LogoutView.as_view(), name='logout'),

    # Core API
    path('api/', include('core.urls')),

    # Frontend Pages
    path('', DashboardView.as_view(), name='dashboard'),
    path('login/', LoginView.as_view(), name='login'),
    path('inventory/', InventoryView.as_view(), name='inventory'),
    path('tickets/', TicketsView.as_view(), name='tickets'),
    path('logs/', LogsView.as_view(), name='logs'),
]
