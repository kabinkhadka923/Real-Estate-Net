from django.urls import path
from . import views

app_name = 'accounts'
urlpatterns = [
    path('register/', views.register, name='register'),
    path('agent-application/', views.agent_application, name='agent_application'),
    path('agents/', views.agent_list, name='agent_list'),
    path('companies/', views.company_list, name='company_list'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('delete-account/', views.delete_account, name='delete_account'),

    # Normal Admin Panel URLs (/net-admin/)
    path('', views.normal_admin_dashboard, name='normal_admin_dashboard'),
    path('properties/', views.normal_admin_properties, name='normal_admin_properties'),
    path('users/', views.normal_admin_users, name='normal_admin_users'),
    path('inquiries/', views.normal_admin_inquiries, name='normal_admin_inquiries'),
    path('reports/', views.normal_admin_reports, name='normal_admin_reports'),
    path('profile/', views.normal_admin_profile, name='normal_admin_profile'),
    path('request-permission/', views.normal_admin_request_permission, name='normal_admin_request_permission'),
    path('permission-requests/', views.super_admin_permission_requests, name='normal_admin_permission_requests'),

    # Django Admin Integration URLs (for super admins)
    path('django-admin/', views.normal_admin_django_admin, name='normal_admin_django_admin'),
    path('django-users/', views.normal_admin_django_users, name='normal_admin_django_users'),
    path('django-properties/', views.normal_admin_django_properties, name='normal_admin_django_properties'),
    path('django-premium/', views.normal_admin_django_premium, name='normal_admin_django_premium'),
    path('django-contact/', views.normal_admin_django_contact, name='normal_admin_django_contact'),
    path('django-blog/', views.normal_admin_django_blog, name='normal_admin_django_blog'),
    path('django-analytics/', views.normal_admin_django_analytics, name='normal_admin_django_analytics'),

    # Integrated Admin URLs (from old /admin/ system)
    path('full-dashboard/', views.normal_admin_full_dashboard, name='normal_admin_full_dashboard'),
    path('full-users/', views.normal_admin_full_users, name='normal_admin_full_users'),
    path('full-properties/', views.normal_admin_full_properties, name='normal_admin_full_properties'),
    path('pending/', views.normal_admin_pending, name='normal_admin_pending'),
    path('featured/', views.normal_admin_featured, name='normal_admin_featured'),
    path('agents/', views.normal_admin_agents, name='normal_admin_agents'),
    path('companies/', views.normal_admin_companies, name='normal_admin_companies'),
    path('payments/', views.normal_admin_payments, name='normal_admin_payments'),
    path('full-reports/', views.normal_admin_full_reports, name='normal_admin_full_reports'),
    path('blog/', views.normal_admin_blog, name='normal_admin_blog'),
    path('cms/', views.normal_admin_cms, name='normal_admin_cms'),
    path('system-settings/', views.normal_admin_settings, name='normal_admin_settings'),

    # Detail views
    path('property/<int:property_id>/', views.normal_admin_property_detail, name='normal_admin_property_detail'),
    path('user/<int:user_id>/', views.normal_admin_user_detail, name='normal_admin_user_detail'),
    path('agent/<int:agent_id>/', views.normal_admin_agent_detail, name='normal_admin_agent_detail'),
]
