"""
URL configuration for real_estate project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from properties.views import home
from accounts import views
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponsePermanentRedirect
from django.views.generic import RedirectView
from . import admin_views

# Custom admin site with full access for superusers
class SecureAdminSite(admin.AdminSite):
    site_header = "🏠 Real Estate Net Administration"
    site_title = "Real Estate Net Admin Portal"
    index_title = "Welcome to Real Estate Admin"
    index_template = "admin/custom_index.html"

    # Custom CSS for admin branding
    class Media:
        css = {
            'all': ('css/admin_custom.css',)
        }

    def has_permission(self, request):
        # Allow superusers and normal admins full access
        return request.user.is_authenticated and (
            request.user.is_superuser or
            request.user.user_type in ['super_admin', 'admin']
        )

    def each_context(self, request):
        context = super().each_context(request)
        context['custom_stats'] = self.get_custom_stats()
        return context

    def get_custom_stats(self):
        from properties.models import Property
        from accounts.models import User
        from contact.models import ContactInquiry
        from blog.models import BlogPost
        from analytics.models import PageView
        from properties.utils import get_image_statistics
        from django.utils import timezone
        from datetime import timedelta

        # Get date 30 days ago for recent stats
        thirty_days_ago = timezone.now() - timedelta(days=30)

        # Get basic stats
        basic_stats = {
            'total_properties': Property.objects.count(),
            'verified_properties': Property.objects.filter(is_verified=True).count(),
            'total_users': User.objects.count(),
            'total_brokers': User.objects.filter(user_type='broker').count(),
            'total_buyers': User.objects.filter(user_type='buyer').count(),
            'pending_verifications': Property.objects.filter(is_verified=False).count(),
            'recent_properties': Property.objects.filter(created_at__gte=thirty_days_ago).count(),
            'total_inquiries': ContactInquiry.objects.count(),
            'unresolved_inquiries': ContactInquiry.objects.filter(is_resolved=False).count(),
            'total_blog_posts': BlogPost.objects.count(),
            'published_posts': BlogPost.objects.filter(is_published=True).count(),
            'total_page_views': PageView.objects.count(),
            'recent_page_views': PageView.objects.filter(timestamp__gte=thirty_days_ago).count(),
        }

        # Get image stats
        try:
            image_stats = get_image_statistics()
        except Exception:
            # Fallback if there are issues with image stats
            image_stats = {
                'total_images': 0,
                'flagged_images': 0,
                'approved_images': 0,
                'rejected_images': 0,
                'deleted_images': 0,
                'duplicate_images': 0,
            }

        # Combine stats
        basic_stats.update(image_stats)
        return basic_stats

# Create secure admin instance
secure_admin = SecureAdminSite(name='secure_admin')

# Import models for admin registration
from properties.models import Property, PropertyType, Amenity, Image, Company, Location
from accounts.models import User
from contact.models import ContactInquiry
from blog.models import BlogPost
from analytics.models import PageView
from premium.models import PremiumListing


# Import admin classes
from properties.admin import PropertyAdmin, PropertyTypeAdmin, AmenityAdmin, ImageAdmin, CompanyAdmin, LocationAdmin
from premium.admin import PremiumListingAdmin

# Create custom admin classes
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'user_type', 'phone_number', 'properties_count', 'is_staff', 'is_active', 'view_properties')
    list_filter = ('user_type', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'phone_number')
    fieldsets = (
        ('Basic Information', {
            'fields': ('username', 'email', 'password')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'phone_number', 'address', 'user_type')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    actions = ['delete_brokers', 'delete_investors', 'delete_tenants']

    def properties_count(self, obj):
        return obj.properties.count()
    properties_count.short_description = 'Properties Listed'

    def view_properties(self, obj):
        url = f'/real-admin/properties/property/?user={obj.id}'
        return f'<a href="{url}" target="_blank">View Properties</a>'
    view_properties.short_description = 'Properties'
    view_properties.allow_tags = True

    def delete_brokers(self, request, queryset):
        queryset.filter(user_type='broker').delete()
        self.message_user(request, "Selected broker accounts deleted.")
    delete_brokers.short_description = 'Delete selected brokers'

    def delete_investors(self, request, queryset):
        queryset.filter(user_type='investor').delete()
        self.message_user(request, "Selected investor accounts deleted.")
    delete_investors.short_description = 'Delete selected investors'

    def delete_tenants(self, request, queryset):
        queryset.filter(user_type='tenant').delete()
        self.message_user(request, "Selected tenant accounts deleted.")
    delete_tenants.short_description = 'Delete selected tenants'

# Register models with custom admin classes
secure_admin.register(Property, PropertyAdmin)
secure_admin.register(PropertyType, PropertyTypeAdmin)
secure_admin.register(Amenity, AmenityAdmin)
secure_admin.register(Image, ImageAdmin)
secure_admin.register(Company, CompanyAdmin)
secure_admin.register(Location, LocationAdmin)
secure_admin.register(User, UserAdmin)
secure_admin.register(PremiumListing, PremiumListingAdmin)
secure_admin.register(ContactInquiry)
secure_admin.register(BlogPost)
secure_admin.register(PageView)

urlpatterns = [
    path('favicon.ico', lambda r: HttpResponsePermanentRedirect('/static/logo.png')),  # Favicon redirect

    path('real-admin/', secure_admin.urls),  # Super Admin Panel (Full Access)
    path('net-admin/', include('accounts.urls', namespace='normal_admin')),  # Normal Admin Panel (Limited Access)

    # Unified Account URLs - Minimal allauth for social auth
    path('accounts/', include([
        path('signup/', RedirectView.as_view(url='/accounts/register/', permanent=True), name='account_signup'),
        path('', include('allauth.urls')),  # Required for social authentication
        path('', include('accounts.urls', namespace='accounts')),
        # Main registration endpoint
        path('register/', views.register, name='register'),
        # Custom login view
        path('login/', views.user_login, name='login'),
    ])),

    # Local app URLs
    path('properties/', include('properties.urls', namespace='properties')),
    path('premium/', include('premium.urls', namespace='premium')),
    path('analytics/', include('analytics.urls', namespace='analytics')),
    path('contact/', include('contact.urls', namespace='contact')),
    path('blog/', include('blog.urls', namespace='blog')),
    path('legal/', include('legal.urls', namespace='legal')),

    # Custom Admin URLs
    path('admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', admin_views.admin_users, name='admin_users'),
    path('admin/properties/', admin_views.admin_properties, name='admin_properties'),
    path('admin/pending/', admin_views.admin_pending, name='admin_pending'),
    path('admin/featured/', admin_views.admin_featured, name='admin_featured'),
    path('admin/agents/', admin_views.admin_agents, name='admin_agents'),
    path('admin/companies/', admin_views.admin_companies, name='admin_companies'),
    path('admin/payments/', admin_views.admin_payments, name='admin_payments'),
    path('admin/reports/', admin_views.admin_reports, name='admin_reports'),
    path('admin/blog/', admin_views.admin_blog, name='admin_blog'),
    path('admin/cms/', admin_views.admin_cms, name='admin_cms'),
    path('admin/settings/', admin_views.admin_settings, name='admin_settings'),
    path('admin/permission-requests/', admin_views.admin_permission_requests, name='admin_permission_requests'),

    # Detail views
    path('admin/property/<int:property_id>/', admin_views.admin_property_detail, name='admin_property_detail'),
    path('admin/user/<int:user_id>/', admin_views.admin_user_detail, name='admin_user_detail'),
    path('admin/agent/<int:agent_id>/', admin_views.admin_agent_detail, name='admin_agent_detail'),

    path('admin/api/', include('adminapi.urls', namespace='adminapi')),
    path('', home, name='home'),
]

# Django admin is now integrated into net-admin panel - no separate /admin/ URL

# Serve media and static files during development and tunneling
if settings.DEBUG or getattr(settings, 'SERVEO_TUNNEL_ACTIVE', False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
