from django.contrib import admin


class AdminDashboardAdminSite(admin.AdminSite):
    """Custom admin site for dashboard"""
    site_header = 'LuxeEstate Admin Dashboard'
    site_title = 'Admin'
    index_title = 'Dashboard'
