from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Count, Sum
from django.core.paginator import Paginator
from properties.models import Property, Image
from accounts.models import User
from contact.models import ContactInquiry
from premium.models import PremiumListing
from blog.models import BlogPost
from analytics.models import PageView
import json

# Permission check for admin access
def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

# API endpoints for admin operations

@user_passes_test(is_admin)
@require_POST
def property_approve(request):
    """Approve a property listing"""
    try:
        property_id = request.POST.get('id')
        property_obj = get_object_or_404(Property, pk=property_id)
        property_obj.status = 'approved'
        property_obj.save()

        # Log the action
        # You could add admin activity logging here

        return JsonResponse({
            'success': True,
            'message': f'Property "{property_obj.title}" has been approved.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@user_passes_test(is_admin)
@require_POST
def property_reject(request):
    """Reject a property listing"""
    try:
        property_id = request.POST.get('id')
        reason = request.POST.get('reason', 'No reason provided')
        property_obj = get_object_or_404(Property, pk=property_id)
        property_obj.status = 'rejected'
        property_obj.save()

        # Log the action with reason
        # You could add admin activity logging here

        return JsonResponse({
            'success': True,
            'message': f'Property "{property_obj.title}" has been rejected.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@user_passes_test(is_admin)
@require_POST
def property_toggle_premium(request):
    """Toggle premium status of a property"""
    try:
        property_id = request.POST.get('id')
        property_obj = get_object_or_404(Property, pk=property_id)
        property_obj.is_premium = not property_obj.is_premium
        property_obj.save()

        status = "added to" if property_obj.is_premium else "removed from"
        return JsonResponse({
            'success': True,
            'is_premium': property_obj.is_premium,
            'message': f'Property "{property_obj.title}" {status} premium listings.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@user_passes_test(is_admin)
@require_POST
def property_delete(request):
    """Delete a property listing"""
    try:
        property_id = request.POST.get('id')
        property_obj = get_object_or_404(Property, pk=property_id)

        # Store title for message before deletion
        title = property_obj.title

        # Delete the property (this will cascade delete images)
        property_obj.delete()

        return JsonResponse({
            'success': True,
            'message': f'Property "{title}" has been permanently deleted.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@user_passes_test(is_admin)
@require_POST
def user_ban(request):
    """Ban a user account"""
    try:
        user_id = request.POST.get('id')
        user_obj = get_object_or_404(User, pk=user_id)
        user_obj.is_active = False
        user_obj.save()

        return JsonResponse({
            'success': True,
            'message': f'User "{user_obj.username}" has been banned.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@user_passes_test(is_admin)
@require_POST
def user_verify(request):
    """Verify a user account"""
    try:
        user_id = request.POST.get('id')
        user_obj = get_object_or_404(User, pk=user_id)
        user_obj.is_verified = True
        user_obj.verification_date = timezone.now()
        user_obj.save()

        return JsonResponse({
            'success': True,
            'message': f'User "{user_obj.username}" has been verified.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@user_passes_test(is_admin)
@require_POST
def users_bulk_ban(request):
    """Bulk ban multiple users"""
    try:
        user_ids = json.loads(request.POST.get('ids', '[]'))
        users = User.objects.filter(pk__in=user_ids)
        count = users.update(is_active=False)

        return JsonResponse({
            'success': True,
            'message': f'{count} users have been banned.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@user_passes_test(is_admin)
@require_POST
def users_bulk_verify(request):
    """Bulk verify multiple users"""
    try:
        user_ids = json.loads(request.POST.get('ids', '[]'))
        users = User.objects.filter(pk__in=user_ids)
        count = users.update(is_verified=True)

        return JsonResponse({
            'success': True,
            'message': f'{count} users have been verified.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@user_passes_test(is_admin)
@require_POST
def user_unban(request):
    """Unban a user account"""
    try:
        user_id = request.POST.get('id')
        user_obj = get_object_or_404(User, pk=user_id)
        user_obj.is_active = True
        user_obj.save()

        return JsonResponse({
            'success': True,
            'message': f'User "{user_obj.username}" has been unbanned.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@user_passes_test(is_admin)
def payment_invoice(request):
    """Generate invoice HTML for a payment"""
    try:
        payment_id = request.GET.get('id')
        # For now, return a placeholder. You'll need to implement Payment model
        # payment = get_object_or_404(Payment, pk=payment_id)

        # Placeholder invoice HTML
        invoice_html = f"""
        <div class="invoice">
            <h4>Invoice #{payment_id}</h4>
            <p><strong>Payment ID:</strong> {payment_id}</p>
            <p><strong>Status:</strong> Completed</p>
            <p><strong>Amount:</strong> NPR 0.00</p>
            <p><strong>Date:</strong> {timezone.now().strftime('%Y-%m-%d')}</p>
            <hr>
            <p>This is a placeholder invoice. Implement Payment model for full functionality.</p>
        </div>
        """

        return HttpResponse(invoice_html)
    except Exception as e:
        return HttpResponse(f"<div class='alert alert-danger'>Error generating invoice: {str(e)}</div>", status=400)

@user_passes_test(is_admin)
def stats_api(request):
    """Get dashboard statistics via AJAX"""
    try:
        # Get date 30 days ago for recent stats
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)

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

        return JsonResponse({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@user_passes_test(is_admin)
def chart_data_api(request):
    """Get chart data for dashboard"""
    try:
        # Property views over last 30 days
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)

        # Generate sample chart data (replace with real analytics)
        labels = []
        values = []
        for i in range(30):
            date = thirty_days_ago + timezone.timedelta(days=i)
            labels.append(date.strftime('%m/%d'))
            # Sample data - replace with real property view counts
            values.append(PageView.objects.filter(
                timestamp__date=date.date(),
                path__icontains='properties'
            ).count())

        chart_data = {
            'labels': labels,
            'values': values
        }

        return JsonResponse({
            'success': True,
            'chart_data': chart_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

# Additional utility endpoints

@user_passes_test(is_admin)
def export_properties_csv(request):
    """Export properties to CSV"""
    try:
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="properties_export.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Title', 'Agent', 'Price', 'Location', 'Status', 'Created'])

        properties = Property.objects.select_related('agent').all()
        for prop in properties:
            writer.writerow([
                prop.id,
                prop.title,
                prop.agent.get_full_name() if prop.agent else 'N/A',
                prop.price,
                f"{prop.city}, {prop.state}",
                prop.status,
                prop.created_at.strftime('%Y-%m-%d')
            ])

        return response
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@user_passes_test(is_admin)
def bulk_property_actions(request):
    """Handle bulk property actions"""
    try:
        action = request.POST.get('action')
        property_ids = json.loads(request.POST.get('ids', '[]'))

        if not property_ids:
            return JsonResponse({
                'success': False,
                'message': 'No properties selected'
            })

        properties = Property.objects.filter(pk__in=property_ids)
        count = 0

        if action == 'approve':
            count = properties.update(status='approved')
            message = f'{count} properties approved'
        elif action == 'reject':
            count = properties.update(status='rejected')
            message = f'{count} properties rejected'
        elif action == 'verify':
            count = properties.update(is_verified=True)
            message = f'{count} properties verified'
        elif action == 'make_premium':
            count = properties.update(is_premium=True)
            message = f'{count} properties marked as premium'
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid action'
            })

        return JsonResponse({
            'success': True,
            'message': message,
            'count': count
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
