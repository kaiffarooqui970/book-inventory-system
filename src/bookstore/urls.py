"""URL configuration for the bookstore project.

No admin interface and no templates — every route is a JSON API endpoint,
so everything can be exercised directly via URLs (curl, tests, etc.).
"""
from django.urls import include, path

urlpatterns = [
    path('', include('inventory.urls')),
]

handler404 = 'inventory.views.not_found_404'
