"""
Frontend template view'ları.

Tüm sayfalar basit TemplateView olarak sunulur.
İş mantığı tamamen API + JavaScript tarafında çalışır.
"""

from django.views.generic import TemplateView


class LoginView(TemplateView):
    template_name = 'login.html'


class DashboardView(TemplateView):
    template_name = 'dashboard.html'


class InventoryView(TemplateView):
    template_name = 'inventory.html'


class TicketsView(TemplateView):
    template_name = 'tickets.html'


class LogsView(TemplateView):
    template_name = 'logs.html'
