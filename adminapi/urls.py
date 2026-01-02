from django.urls import path
from . import views

app_name = 'adminapi'

urlpatterns = [
    # Property management endpoints
    path('property/approve/', views.property_approve, name='property_approve'),
    path('property/reject/', views.property_reject, name='property_reject'),
    path('property/toggle-premium/', views.property_toggle_premium, name='property_toggle_premium'),
    path('property/delete/', views.property_delete, name='property_delete'),

    # User management endpoints
    path('user/ban/', views.user_ban, name='user_ban'),
    path('user/unban/', views.user_unban, name='user_unban'),
    path('user/verify/', views.user_verify, name='user_verify'),
    path('users/bulk-ban/', views.users_bulk_ban, name='users_bulk_ban'),
    path('users/bulk-verify/', views.users_bulk_verify, name='users_bulk_verify'),

    # Payment and finance endpoints
    path('payment/invoice/', views.payment_invoice, name='payment_invoice'),

    # Dashboard and analytics endpoints
    path('stats/', views.stats_api, name='stats'),
    path('chart-data/', views.chart_data_api, name='chart_data'),

    # Utility endpoints
    path('export/properties/csv/', views.export_properties_csv, name='export_properties_csv'),
    path('bulk/property-actions/', views.bulk_property_actions, name='bulk_property_actions'),
]
