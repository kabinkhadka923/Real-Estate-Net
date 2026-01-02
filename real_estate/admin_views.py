from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from properties.models import Property
from accounts.models import User
from contact.models import ContactInquiry
from premium.models import PremiumListing
from blog.models import BlogPost
from analytics.models import PageView

# Permission check for admin access
def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@user_passes_test(is_admin)
def admin_dashboard(request):
    """Main admin dashboard view"""
    # Get date 30 days ago for recent stats
    thirty_days_ago = timezone.now() - timedelta(days=30)

    # Basic statistics
    stats = {
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
        'active_premium': PremiumListing.objects.filter(is_active=True).count(),
        'premium_properties': Property.objects.filter(is_premium=True).count(),
    }

    # Chart data for property views (last 7 days for demo)
    chart_labels = []
    chart_values = []
    for i in range(7):
        date = thirty_days_ago + timedelta(days=(23 + i))  # Last 7 days
        chart_labels.append(date.strftime('%m/%d'))
        # Sample data - replace with real analytics
        chart_values.append(PageView.objects.filter(
            timestamp__date=date.date(),
            path__icontains='properties'
        ).count() or max(5, i * 3))  # Fallback sample data

    # User distribution data
    user_data = {
        'buyers': stats['total_buyers'],
        'brokers': stats['total_brokers'],
        'agents': User.objects.filter(user_type='agent').count(),
        'premium': stats['active_premium']
    }

    # Recent activities (mock data for now)
    recent_activities = [
        {
            'type': 'property',
            'title': 'New Property Listed',
            'description': 'Luxury apartment in Kathmandu added',
            'timestamp': timezone.now() - timedelta(hours=2)
        },
        {
            'type': 'user',
            'title': 'New User Registered',
            'description': 'Real estate agent joined the platform',
            'timestamp': timezone.now() - timedelta(hours=4)
        },
        {
            'type': 'payment',
            'title': 'Premium Subscription',
            'description': 'User upgraded to premium plan',
            'timestamp': timezone.now() - timedelta(hours=6)
        }
    ]

    context = {
        **stats,
        'chart_labels': chart_labels,
        'chart_values': chart_values,
        'user_data': user_data,
        'recent_activities': recent_activities,
    }

    return render(request, 'realestate_admin_templates/dashboard.html', context)

@user_passes_test(is_admin)
def admin_users(request):
    """Users management page"""
    users = User.objects.all().order_by('-date_joined')[:100]  # Limit for performance
    context = {
        'users': users,
        'total_users': User.objects.count(),
    }
    return render(request, 'realestate_admin_templates/users_list.html', context)

@user_passes_test(is_admin)
def admin_properties(request):
    """Properties management page"""
    properties = Property.objects.select_related('agent').order_by('-created_at')[:100]
    context = {
        'properties': properties,
        'total_properties': Property.objects.count(),
    }
    return render(request, 'realestate_admin_templates/properties_list.html', context)

@user_passes_test(is_admin)
def admin_pending(request):
    """Pending property approvals"""
    pending_properties = Property.objects.filter(
        is_verified=False
    ).select_related('agent').order_by('-created_at')

    context = {
        'properties': pending_properties,
        'pending_count': pending_properties.count(),
    }
    return render(request, 'realestate_admin_templates/properties_list.html', context)

@user_passes_test(is_admin)
def admin_featured(request):
    """Featured properties"""
    featured_properties = Property.objects.filter(
        is_premium=True
    ).select_related('agent').order_by('-created_at')

    context = {
        'properties': featured_properties,
        'featured_count': featured_properties.count(),
    }
    return render(request, 'realestate_admin_templates/properties_list.html', context)

@user_passes_test(is_admin)
def admin_agents(request):
    """Agents management"""
    agents = User.objects.filter(
        user_type__in=['agent', 'broker']
    ).order_by('-date_joined')

    context = {
        'agents': agents,
        'total_agents': agents.count(),
    }
    return render(request, 'realestate_admin_templates/agents_list.html', context)

@user_passes_test(is_admin)
def admin_companies(request):
    """Companies management"""
    # This would need a Company model - placeholder for now
    companies = []  # Placeholder
    context = {
        'companies': companies,
        'total_companies': len(companies),
    }
    return render(request, 'realestate_admin_templates/companies_list.html', context)

@user_passes_test(is_admin)
def admin_payments(request):
    """Payments management"""
    # This would need a Payment model - placeholder for now
    payments = []  # Placeholder
    context = {
        'payments': payments,
        'total_payments': len(payments),
    }
    return render(request, 'realestate_admin_templates/payments.html', context)



# Property detail view
@user_passes_test(is_admin)
def admin_property_detail(request, property_id):
    """Detailed view of a property for admin"""
    try:
        property_obj = Property.objects.select_related('agent').get(pk=property_id)
        inquiries = ContactInquiry.objects.filter(property=property_obj).order_by('-created_at')[:10]

        context = {
            'property': property_obj,
            'inquiries': inquiries,
        }
        return render(request, 'realestate_admin_templates/property_detail.html', context)
    except Property.DoesNotExist:
        return redirect('admin_properties')

# User detail view
@user_passes_test(is_admin)
def admin_user_detail(request, user_id):
    """Detailed view of a user for admin"""
    try:
        user_obj = User.objects.get(pk=user_id)
        user_properties = Property.objects.filter(agent=user_obj)[:10]

        context = {
            'user': user_obj,
            'properties': user_properties,
        }
        return render(request, 'realestate_admin_templates/user_detail.html', context)
    except User.DoesNotExist:
        return redirect('admin_users')

# Agent detail view
@user_passes_test(is_admin)
def admin_agent_detail(request, agent_id):
    """Detailed view of an agent for admin"""
    try:
        agent = User.objects.get(pk=agent_id, user_type__in=['agent', 'broker'])
        agent_properties = Property.objects.filter(agent=agent)

        context = {
            'agent': agent,
            'properties': agent_properties,
            'properties_count': agent_properties.count(),
        }
        return render(request, 'realestate_admin_templates/agent_detail.html', context)
    except User.DoesNotExist:
        return redirect('admin_agents')

# Additional admin views for real-admin system
@user_passes_test(is_admin)
def admin_reports(request):
    """Reports and analytics dashboard"""
    from django.db.models import Count, Sum
    from django.utils import timezone
    from datetime import timedelta

    thirty_days_ago = timezone.now() - timedelta(days=30)

    # Generate comprehensive reports
    reports = {
        'user_growth': User.objects.filter(date_joined__gte=thirty_days_ago).count(),
        'property_growth': Property.objects.filter(created_at__gte=thirty_days_ago).count(),
        'premium_revenue': 0,  # Would integrate with payment system
        'active_listings': Property.objects.filter(status='approved').count(),
        'pending_reviews': Property.objects.filter(status='pending').count(),
        'total_inquiries': ContactInquiry.objects.count(),
        'conversion_rate': 0,  # Would calculate based on inquiries to sales
    }

    context = {
        'reports': reports,
        'chart_data': {
            'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'datasets': [{
                'label': 'User Registrations',
                'data': [10, 15, 8, 12, 20, 18],
                'borderColor': '#0033A0',
                'backgroundColor': 'rgba(0, 51, 160, 0.1)',
            }]
        }
    }
    return render(request, 'realestate_admin_templates/reports.html', context)

@user_passes_test(is_admin)
def admin_blog(request):
    """Blog management for admin"""
    from blog.models import BlogPost

    posts = BlogPost.objects.all().order_by('-created_at')
    context = {
        'posts': posts,
        'total_posts': posts.count(),
        'published_posts': posts.filter(is_published=True).count(),
        'draft_posts': posts.filter(is_published=False).count(),
    }
    return render(request, 'realestate_admin_templates/blog_list.html', context)

@user_passes_test(is_admin)
def admin_cms(request):
    """Content Management System"""
    context = {
        'pages': [],  # Would integrate with CMS pages
        'templates': [],  # Available templates
        'media_files': [],  # Media library
    }
    return render(request, 'realestate_admin_templates/cms.html', context)

@user_passes_test(is_admin)
def admin_settings(request):
    """System settings management"""
    if request.method == 'POST':
        # Handle settings updates
        pass

    context = {
        'settings': {
            'site_title': 'Real Estate Net',
            'site_description': 'Premier property marketplace',
            'contact_email': 'admin@gorkharealestate.com',
            'maintenance_mode': False,
            'email_notifications': True,
        }
    }
    return render(request, 'realestate_admin_templates/settings.html', context)

# Permission Requests Management for Super Admin
def is_super_admin(user):
    return user.is_authenticated and user.user_type == 'super_admin' and user.is_admin_active

@user_passes_test(is_super_admin)
def admin_permission_requests(request):
    """Super Admin Permission Requests Management"""
    from accounts.models import AdminPermissionRequest

    # Get all pending permission requests
    pending_requests = AdminPermissionRequest.objects.filter(
        status='pending'
    ).select_related('requesting_admin').order_by('-requested_at')

    # Get recent approved/rejected requests
    recent_requests = AdminPermissionRequest.objects.filter(
        status__in=['approved', 'rejected']
    ).select_related('requesting_admin', 'reviewed_by').order_by('-reviewed_at')[:20]

    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')
        review_notes = request.POST.get('review_notes', '')

        try:
            permission_request = AdminPermissionRequest.objects.get(pk=request_id, status='pending')

            if action == 'approve':
                permission_request.approve_request(request.user)
                messages.success(request, f'Permission request approved for {permission_request.requesting_admin.username}.')

            elif action == 'reject':
                permission_request.reject_request(request.user, review_notes)
                messages.success(request, f'Permission request rejected for {permission_request.requesting_admin.username}.')

        except AdminPermissionRequest.DoesNotExist:
            messages.error(request, "Permission request not found.")

        return redirect('admin_permission_requests')

    context = {
        'pending_requests': pending_requests,
        'recent_requests': recent_requests,
        'total_pending': pending_requests.count(),
    }

    return render(request, 'realestate_admin_templates/permission_requests.html', context)
