import ipaddress
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import decorator_from_middleware

class AdminSecurityMiddleware:
    """
    Middleware to restrict admin access to specific IP addresses and require superuser privileges
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if trying to access admin panels (both default and custom)
        if request.path.startswith('/admin/') or request.path.startswith('/real-admin/'):
            # If admin is entirely disabled, block all access
            if not getattr(settings, 'ADMIN_ENABLED', True):
                return HttpResponseForbidden(
                    "<h1>🚫 Admin Access Disabled</h1>"
                    "<p>The administrative interface has been disabled for security reasons.</p>"
                    "<p><a href='/'>← Back to Homepage</a></p>"
                )

            # If admin is enabled but restricted, check IP address first
            if settings.ADMIN_RESTRICTED_ACCESS:
                client_ip = self.get_client_ip(request)
                if not self.is_ip_allowed(client_ip):
                    return HttpResponseForbidden(
                        "<h1>🚫 Access Denied</h1>"
                        "<p>Admin access is restricted to authorized IP addresses only.</p>"
                        "<p>Your IP: {}</p>".format(client_ip)
                    )

        # Process the request first to get user authentication
        response = self.get_response(request)

        # Check admin access after authentication middleware has run
        if (request.path.startswith('/admin/') or request.path.startswith('/real-admin/') or request.path.startswith('/secure-admin/')) and settings.ADMIN_RESTRICTED_ACCESS:
            # Check if user is authenticated and is superuser
            if hasattr(request, 'user') and request.user.is_authenticated:
                if not request.user.is_superuser:
                    return HttpResponseForbidden(
                        "<h1>🚫 Admin Access Required</h1>"
                        "<p>You need administrator privileges to access this area.</p>"
                        "<p><a href='{}'>← Back to Homepage</a></p>".format(reverse('home'))
                    )
            elif hasattr(request, 'user'):
                # Redirect to login with next parameter
                login_url = "{}?next={}".format(reverse('accounts:login'), request.path)
                return HttpResponseRedirect(login_url)

        return response

    def get_client_ip(self, request):
        """Get the client's real IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def is_ip_allowed(self, client_ip):
        """Check if the client IP is in the allowed list"""
        for allowed_ip in settings.ALLOWED_ADMIN_IPS:
            try:
                # Handle CIDR notation (e.g., '192.168.1.0/24')
                if '/' in allowed_ip:
                    network = ipaddress.ip_network(allowed_ip, strict=False)
                    if ipaddress.ip_address(client_ip) in network:
                        return True
                else:
                    # Handle single IP addresses
                    if client_ip == allowed_ip:
                        return True
            except ipaddress.AddressValueError:
                continue
        return False

def admin_required(view_func):
    """
    Decorator to require admin access for views
    """
    def check_admin(user):
        return user.is_superuser

    decorated_view = user_passes_test(check_admin)(view_func)
    return decorated_view
