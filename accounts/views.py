from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, get_user_model, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django import forms
from django.utils import timezone
from django.db.models import Count, Q
from django.http import Http404
from datetime import timedelta
from .forms import CustomUserCreationForm, CustomAuthenticationForm, RealEstateAgentApplicationForm
from .models import RealEstateAgentApplication, AdminActivityLog, AdminPermissionRequest
from django.contrib.auth.models import AnonymousUser
from properties.models import Property
from contact.models import ContactInquiry
from premium.models import PremiumListing
from blog.models import BlogPost
from analytics.models import PageView

User = get_user_model()

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            # Handle different user types
            if user.user_type == 'agent':
                # For agents, create account but mark as pending application
                user.is_active = False
                user.is_verified = False
                user.save()

                # Store user ID in session for the application form
                request.session['pending_agent_application'] = user.pk
                request.session['agent_registration'] = True

                messages.info(request,
                    "Account created successfully! Now please complete your Real Estate Agent application."
                )
                return redirect('accounts:agent_application')
            else:
                # For buyers and brokers, activate immediately
                user.is_active = True
                user.is_verified = True
                user.verification_date = timezone.now()
                user.save()
                login(request, user)
                messages.success(request, "Registration successful. Welcome!")
                return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


def agent_application(request):
    """Handle real estate agent application submission"""
    # Check if user just registered as agent
    user_id = request.session.get('pending_agent_application')
    if not user_id:
        messages.error(request, "Please register as a Real Estate Agent first.")
        return redirect('accounts:register')

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('accounts:register')

    if request.method == 'POST':
        form = RealEstateAgentApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.applicant = user
            application.save()

            # Clear the session
            del request.session['pending_agent_application']
            if 'agent_registration' in request.session:
                del request.session['agent_registration']

            messages.success(request,
                "Your Real Estate Agent application has been submitted successfully! "
                "Admin will review your application and contact you soon. "
                "You will receive notification once your account is approved."
            )
            return redirect('accounts:login')
    else:
        # Pre-populate with user's basic info if available
        initial_data = {
            'contact_phone': user.phone_number,
            'contact_email': user.email or '',
        }
        form = RealEstateAgentApplicationForm(initial=initial_data)

    context = {
        'form': form,
        'user': user,
        'is_agent_registration': request.session.get('agent_registration', False)
    }
    return render(request, 'accounts/agent_application.html', context)

def user_login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        username = request.POST.get('username')
        password = request.POST.get('password')

        if form.is_valid():
            user = authenticate(username=username, password=password)

            if user is not None:
                # Handle admin users first (super_admin and admin types)
                if user.user_type in ['super_admin', 'admin']:
                    if user.is_admin_active:
                        login(request, user)
                        messages.success(request, f"Welcome back, Admin {username}!")

                        # Redirect based on admin type and next parameter
                        next_url = request.GET.get('next')
                        if next_url:
                            return redirect(next_url)
                        elif user.user_type == 'super_admin':
                            return redirect('normal_admin:normal_admin_dashboard')
                        else:  # normal admin
                            return redirect('normal_admin:normal_admin_dashboard')
                    else:
                        messages.error(request, "Your admin account is deactivated. Contact Super Admin.")
                        return render(request, 'accounts/login.html', {'form': form})

                # Handle agent verification check BEFORE checking is_active
                elif user.user_type == 'agent':
                    # Check if agent has submitted an application
                    try:
                        application = user.agent_application
                        if application.status == 'approved' and user.is_active and user.is_verified:
                            # Agent is approved, allow login
                            login(request, user)
                            messages.success(request, f"Welcome back, {username}!")
                            return redirect('home')
                        elif application.status in ['pending', 'under_review']:
                            messages.warning(request,
                                "Your Real Estate Agent application is under review. "
                                "You will be notified once it's approved."
                            )
                            return render(request, 'accounts/login.html', {'form': form})
                        elif application.status == 'needs_info':
                            messages.warning(request,
                                "Your application needs additional information. "
                                "Please check your application status for details."
                            )
                            return render(request, 'accounts/login.html', {'form': form})
                        elif application.status == 'rejected':
                            messages.error(request,
                                "Your Real Estate Agent application has been rejected. "
                                "Please contact support for assistance."
                            )
                            return render(request, 'accounts/login.html', {'form': form})
                    except:
                        # No application found
                        messages.error(request,
                            "You must submit a Real Estate Agent application first. "
                            "Please register as an agent again."
                        )
                        return render(request, 'accounts/login.html', {'form': form})

                # For regular users (buyers and brokers), check normal activation
                else:
                    if not user.is_active:
                        messages.error(request, "Your account is deactivated. Contact support.")
                        return render(request, 'accounts/login.html', {'form': form})

                    # Normal login for buyers and brokers
                    login(request, user)
                    messages.success(request, f"Welcome back, {username}!")
                    return redirect('home')

            else:
                # Invalid credentials
                messages.error(request, "Invalid username or password.")
        else:
            # Form not valid
            messages.error(request, "Please enter valid credentials.")
    else:
        form = CustomAuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})

def user_logout(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('home') # Assuming a 'home' URL exists

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'address']

@login_required
def dashboard(request):
    user_form = UserProfileForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)

    if request.method == 'POST':
        if 'username' in request.POST:  # profile update
            user_form = UserProfileForm(request.POST, instance=request.user)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, "Profile updated successfully.")
                return redirect('accounts:dashboard')
        elif 'old_password' in request.POST:  # password change
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password changed successfully.")
                return redirect('accounts:dashboard')
            else:
                messages.error(request, "Error changing password.")
    else:
        user_form = UserProfileForm(instance=request.user)
        password_form = PasswordChangeForm(request.user)

    return render(request, 'accounts/dashboard.html', {'form': user_form, 'password_form': password_form})

@login_required
def delete_account(request):
    """View for users to delete their own account"""
    if request.method == 'POST':
        # Double confirmation check
        confirmation = request.POST.get('confirm_deletion', '')
        username = request.POST.get('confirm_username', '')

        if confirmation == 'DELETE' and username == request.user.username:
            # Delete user's properties first
            properties_count = request.user.properties.all().count()
            request.user.properties.all().delete()  # This will cascade delete related images

            # Delete the user account
            user_to_delete = request.user
            username = user_to_delete.username
            user_to_delete.delete()

            # Log out the user (they're already deleted so this is just cleanup)
            messages.success(request, f"Account '{username}' has been successfully deleted along with {properties_count} properties.")

            # Redirect to home page since user is now anonymous
            return redirect('home')

        else:
            messages.error(request, "Account deletion confirmation failed. Please type 'DELETE' and your username exactly.")

    return render(request, 'accounts/delete_account.html', {})


def agent_list(request):
    """Display list of all verified agents and brokers"""
    # Get agents and brokers who are verified
    agents = User.objects.filter(
        Q(user_type='agent') | Q(user_type='broker'),
        is_verified=True,
        is_active=True
    ).select_related().annotate(
        properties_count=Count('properties')
    ).order_by('-is_verified', '-is_premium_user', '-properties_count')

    context = {
        'agents': agents,
        'total_agents': agents.count(),
    }
    return render(request, 'accounts/agent_list.html', context)


def company_list(request):
    """Display list of real estate companies/agencies"""
    # Get companies by grouping users with company_name
    companies = User.objects.filter(
        Q(company_name__isnull=False) & ~Q(company_name=''),
        Q(user_type='agent') | Q(user_type='broker'),
        is_verified=True,
        is_active=True
    ).values('company_name').annotate(
        company_agents=Count('id'),
        total_properties=Count('properties'),
        premium_members=Count('id', filter=Q(is_premium_user=True))
    ).order_by('-premium_members', '-total_properties', '-company_agents')

    context = {
        'companies': companies,
        'total_companies': len(companies),
    }
    return render(request, 'accounts/company_list.html', context)


# ===== NORMAL ADMIN VIEWS =====
# Permission check for normal admin access
def is_admin_user(user):
    return user.is_authenticated and (user.is_normal_admin() or user.is_super_admin())

# Activity logging helper
def log_admin_activity(request, action_type, description, target_model=None, target_id=None, is_high_risk=False):
    """Log admin activity for monitoring"""
    AdminActivityLog.objects.create(
        admin=request.user,
        action_type=action_type,
        description=description,
        target_model=target_model,
        target_id=target_id,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        device_info={
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip': request.META.get('REMOTE_ADDR', ''),
            'browser': request.META.get('HTTP_USER_AGENT', '').split(' ')[0] if request.META.get('HTTP_USER_AGENT') else '',
        },
        is_high_risk=is_high_risk
    )

@user_passes_test(is_admin_user, login_url='accounts:login')
def normal_admin_dashboard(request):
    """Normal Admin Dashboard - Limited Access"""
    # Update last login tracking
    request.user.last_login_ip = request.META.get('REMOTE_ADDR')
    request.user.save(update_fields=['last_login_ip'])

    # Log admin login
    log_admin_activity(request, 'login', f'Normal admin {request.user.username} logged into dashboard')

    # Get date 30 days ago for recent stats
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)

    # Get basic stats (limited compared to super admin)
    stats = {
        'properties_managed': Property.objects.filter(
            Q(user=request.user)
        ).count(),
        'inquiries_handled': ContactInquiry.objects.filter(
            is_resolved=True
        ).count(),
        'pending_reviews': Property.objects.filter(
            is_verified=False,
            created_at__gte=thirty_days_ago
        ).count() if request.user.can_manage_properties() else 0,
        'recent_activity': AdminActivityLog.objects.filter(
            admin=request.user,
            timestamp__gte=thirty_days_ago
        ).count(),
    }

    # Get total system stats (read-only for normal admins)
    total_stats = {
        'total_properties': Property.objects.count(),
        'verified_properties': Property.objects.filter(is_verified=True).count(),
        'pending_verifications': Property.objects.filter(is_verified=False).count(),
        'total_users': User.objects.count(),
        'total_buyers': User.objects.filter(user_type='buyer').count(),
        'total_brokers': User.objects.filter(user_type='broker').count(),
        'total_agents': User.objects.filter(user_type='agent').count(),
        'active_premium': PremiumListing.objects.filter(is_active=True).count(),
        'unresolved_inquiries': ContactInquiry.objects.filter(is_resolved=False).count(),
    }

    # Get recent activities for timeline
    recent_activities = []
    recent_logs = AdminActivityLog.objects.filter(
        admin=request.user
    ).order_by('-timestamp')[:5]

    for log in recent_logs:
        recent_activities.append({
            'type': 'admin',
            'action': log.get_action_type_display(),
            'description': log.description[:100] + '...' if len(log.description) > 100 else log.description,
            'timestamp': log.timestamp
        })

    # Add some system-wide activities if admin has permissions
    if request.user.can_manage_properties():
        recent_properties = Property.objects.filter(
            created_at__gte=thirty_days_ago
        ).order_by('-created_at')[:3]

        for prop in recent_properties:
            recent_activities.append({
                'type': 'property',
                'action': 'New Property Listed',
                'description': f'"{prop.title}" by {prop.user.username}',
                'timestamp': prop.created_at
            })

    # Sort activities by timestamp
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = recent_activities[:8]  # Limit to 8 items

    # Get user's permissions for UI display
    permissions = request.user.get_admin_permissions()

    # Get unread admin notifications
    notifications = request.user.admin_notifications.filter(
        is_read=False
    ).order_by('-created_at')[:5]

    context = {
        'stats': stats,
        'total_stats': total_stats,
        'recent_activities': recent_activities,
        'permissions': permissions,
        'notifications': notifications,
        'user': request.user,
        'is_normal_admin': True,
    }

    return render(request, 'accounts/normal_admin/dashboard.html', context)

@user_passes_test(is_admin_user, login_url='accounts:login')
def normal_admin_properties(request):
    """Normal Admin Properties Management - Limited Access"""
    if not request.user.can_manage_properties():
        messages.error(request, "You don't have permission to manage properties.")
        return redirect('normal_admin:normal_admin_dashboard')

    # Show properties this admin can manage: their own properties + unverified properties for review
    properties = Property.objects.filter(
        Q(user=request.user) |
        Q(is_verified=False)  # Can review unverified properties
    ).select_related('user').order_by('-created_at')[:50]

    if request.method == 'POST':
        property_id = request.POST.get('property_id')
        action = request.POST.get('action')

        try:
            property_obj = Property.objects.get(pk=property_id)

            if action == 'approve' and request.user.can_manage_properties():
                property_obj.status = 'approved'
                property_obj.is_verified = True
                property_obj.verified_by = request.user
                property_obj.verified_at = timezone.now()
                property_obj.save()

                log_admin_activity(
                    request, 'approve', f'Approved property: {property_obj.title}',
                    'Property', property_obj.id, is_high_risk=True
                )
                messages.success(request, f'Property "{property_obj.title}" approved successfully.')

            elif action == 'reject' and request.user.can_manage_properties():
                property_obj.status = 'rejected'
                property_obj.save()

                log_admin_activity(
                    request, 'reject', f'Rejected property: {property_obj.title}',
                    'Property', property_obj.id, is_high_risk=True
                )
                messages.success(request, f'Property "{property_obj.title}" rejected.')

        except Property.DoesNotExist:
            messages.error(request, "Property not found.")

        return redirect('normal_admin:normal_admin_properties')

    context = {
        'properties': properties,
        'can_approve': request.user.can_manage_properties(),
        'permissions': request.user.get_admin_permissions(),
    }

    return render(request, 'accounts/normal_admin/properties.html', context)

@user_passes_test(is_admin_user, login_url='accounts:login')
def normal_admin_users(request):
    """Normal Admin Users Management - Limited Access"""
    if not request.user.can_manage_users():
        messages.error(request, "You don't have permission to manage users.")
        return redirect('normal_admin:normal_admin_dashboard')

    # Limited user management - only basic users, not other admins
    users = User.objects.filter(
        user_type__in=['buyer', 'agent', 'broker'],
        is_active=True
    ).exclude(
        user_type__in=['admin', 'super_admin']
    ).order_by('-date_joined')[:50]

    context = {
        'users': users,
        'permissions': request.user.get_admin_permissions(),
    }

    return render(request, 'accounts/normal_admin/users.html', context)

@user_passes_test(is_admin_user, login_url='accounts:login')
def normal_admin_inquiries(request):
    """Normal Admin Inquiries Management"""
    # Show all inquiries since there's no assignment system
    inquiries = ContactInquiry.objects.select_related('property').order_by('-submitted_at')[:50]

    if request.method == 'POST':
        inquiry_id = request.POST.get('inquiry_id')
        action = request.POST.get('action')
        notes = request.POST.get('admin_notes', '')

        try:
            inquiry = ContactInquiry.objects.get(pk=inquiry_id)

            if action == 'resolve':
                inquiry.is_resolved = True
                inquiry.admin_notes = notes
                inquiry.save()

                log_admin_activity(
                    request, 'update', f'Resolved inquiry #{inquiry.id}',
                    'ContactInquiry', inquiry.id
                )
                messages.success(request, 'Inquiry resolved successfully.')

        except ContactInquiry.DoesNotExist:
            messages.error(request, "Inquiry not found.")

        return redirect('normal_admin:normal_admin_inquiries')

    context = {
        'inquiries': inquiries,
        'permissions': request.user.get_admin_permissions(),
    }

    return render(request, 'accounts/normal_admin/inquiries.html', context)

@user_passes_test(is_admin_user, login_url='/accounts/login/')
def normal_admin_reports(request):
    """Normal Admin Reports - Limited Access"""
    # Generate basic reports for this admin
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)

    reports = {
        'properties_managed': Property.objects.filter(
            Q(user=request.user),
            created_at__gte=thirty_days_ago
        ).count(),
        'inquiries_resolved': ContactInquiry.objects.filter(
            is_resolved=True
        ).count(),
        'activity_count': AdminActivityLog.objects.filter(
            admin=request.user,
            timestamp__gte=thirty_days_ago
        ).count(),
    }

    # Recent activity for this admin
    recent_activity = AdminActivityLog.objects.filter(
        admin=request.user
    ).order_by('-timestamp')[:10]

    context = {
        'reports': reports,
        'recent_activity': recent_activity,
        'permissions': request.user.get_admin_permissions(),
    }

    return render(request, 'accounts/normal_admin/reports.html', context)

@user_passes_test(is_admin_user, login_url='/accounts/login/')
def normal_admin_profile(request):
    """Normal Admin Profile Management"""
    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'profile':
            # Handle profile update
            request.user.first_name = request.POST.get('first_name', '')
            request.user.last_name = request.POST.get('last_name', '')
            request.user.phone_number = request.POST.get('phone_number', '')
            request.user.address = request.POST.get('address', '')
            request.user.bio = request.POST.get('bio', '')
            request.user.save()

            log_admin_activity(request, 'update', 'Updated admin profile')
            messages.success(request, 'Profile updated successfully.')

        elif form_type == 'password':
            # Handle password change
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
            elif len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters.')
            else:
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)

                log_admin_activity(request, 'update', 'Changed admin password', is_high_risk=True)
                messages.success(request, 'Password changed successfully.')

        return redirect('normal_admin:normal_admin_profile')

    context = {
        'user': request.user,
        'permissions': request.user.get_admin_permissions(),
        'admin_permissions_display': request.user.get_admin_permissions(),
    }

    return render(request, 'accounts/normal_admin/profile.html', context)

@user_passes_test(is_admin_user, login_url='/accounts/login/')
def normal_admin_request_permission(request):
    """Normal Admin Permission Request Form"""
    if request.method == 'POST':
        permission_type = request.POST.get('permission_type')
        reason = request.POST.get('reason')
        justification = request.POST.get('justification')

        if not permission_type or not reason or not justification:
            messages.error(request, "All fields are required.")
            return redirect('normal_admin:normal_admin_request_permission')

        # Check if user already has this permission
        permissions = request.user.get_admin_permissions()
        if permissions.get(permission_type, False):
            messages.warning(request, f"You already have {dict(AdminPermissionRequest.PERMISSION_TYPES)[permission_type]} permission.")
            return redirect('normal_admin:normal_admin_profile')

        # Check if there's already a pending request for this permission
        existing_request = AdminPermissionRequest.objects.filter(
            requesting_admin=request.user,
            permission_type=permission_type,
            status='pending'
        ).first()

        if existing_request:
            messages.warning(request, f"You already have a pending request for {dict(AdminPermissionRequest.PERMISSION_TYPES)[permission_type]} permission.")
            return redirect('normal_admin:normal_admin_profile')

        # Create the permission request
        AdminPermissionRequest.objects.create(
            requesting_admin=request.user,
            permission_type=permission_type,
            reason=reason,
            justification=justification
        )

        # Log the request
        log_admin_activity(
            request, 'create', f'Submitted permission request for {dict(AdminPermissionRequest.PERMISSION_TYPES)[permission_type]}',
            'AdminPermissionRequest', None
        )

        messages.success(request, f'Your request for {dict(AdminPermissionRequest.PERMISSION_TYPES)[permission_type]} permission has been submitted to Super Admin for review.')

        return redirect('normal_admin:normal_admin_profile')

    # Get available permissions that user doesn't have
    current_permissions = request.user.get_admin_permissions()
    available_permissions = []

    for perm_key, perm_name in AdminPermissionRequest.PERMISSION_TYPES:
        if not current_permissions.get(perm_key, False):
            # Check if there's already a pending request
            has_pending = AdminPermissionRequest.objects.filter(
                requesting_admin=request.user,
                permission_type=perm_key,
                status='pending'
            ).exists()
            available_permissions.append({
                'key': perm_key,
                'name': perm_name,
                'has_pending': has_pending
            })

    context = {
        'available_permissions': available_permissions,
        'permissions': request.user.get_admin_permissions(),
    }

    return render(request, 'accounts/normal_admin/request_permission.html', context)

# ===== SUPER ADMIN VIEWS =====
def is_super_admin(user):
    return user.is_authenticated and user.is_super_admin()

@user_passes_test(is_super_admin, login_url='/accounts/login/')
def super_admin_permission_requests(request):
    """Super Admin Permission Requests Management"""
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

        return redirect('normal_admin:normal_admin_permission_requests')

    context = {
        'pending_requests': pending_requests,
        'recent_requests': recent_requests,
        'total_pending': pending_requests.count(),
    }

    return render(request, 'realestate_admin_templates/permission_requests.html', context)

# ===== DJANGO ADMIN INTEGRATION VIEWS =====
@user_passes_test(is_super_admin, login_url='/accounts/login/')
def normal_admin_django_admin(request):
    """Redirect to Django Admin Dashboard"""
    return redirect('/real-admin/')

@user_passes_test(is_super_admin, login_url='/accounts/login/')
def normal_admin_django_users(request):
    """Redirect to Django Admin Users"""
    return redirect('/real-admin/accounts/user/')

@user_passes_test(is_super_admin, login_url='/accounts/login/')
def normal_admin_django_properties(request):
    """Redirect to Django Admin Properties"""
    return redirect('/real-admin/properties/property/')

@user_passes_test(is_super_admin, login_url='/accounts/login/')
def normal_admin_django_premium(request):
    """Redirect to Django Admin Premium Listings"""
    return redirect('/real-admin/premium/premiumlisting/')

@user_passes_test(is_super_admin, login_url='/accounts/login/')
def normal_admin_django_contact(request):
    """Redirect to Django Admin Contact Inquiries"""
    return redirect('/real-admin/contact/contactinquiry/')

@user_passes_test(is_super_admin, login_url='/accounts/login/')
def normal_admin_django_blog(request):
    """Redirect to Django Admin Blog Posts"""
    return redirect('/real-admin/blog/blogpost/')

@user_passes_test(is_super_admin, login_url='/accounts/login/')
def normal_admin_django_analytics(request):
    """Redirect to Django Admin Analytics"""
    return redirect('/real-admin/analytics/pageview/')

# ===== INTEGRATED ADMIN VIEWS =====
# Permission check for admin access
def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser or user.user_type in ['super_admin', 'admin'])

@user_passes_test(is_admin, login_url='/accounts/login/')
def normal_admin_full_dashboard(request):
    """Full admin dashboard view (integrated from old admin system)"""
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

@user_passes_test(is_admin, login_url='/accounts/login/')
def normal_admin_full_users(request):
    """Full users management page"""
    users = User.objects.all().order_by('-date_joined')[:100]  # Limit for performance
    context = {
        'users': users,
        'total_users': User.objects.count(),
    }
    return render(request, 'realestate_admin_templates/users_list.html', context)

@user_passes_test(is_admin, login_url='/accounts/login/')
def normal_admin_full_properties(request):
    """Full properties management page"""
    properties = Property.objects.select_related('user').order_by('-created_at')[:100]
    context = {
        'properties': properties,
        'total_properties': Property.objects.count(),
    }
    return render(request, 'realestate_admin_templates/properties_list.html', context)

@user_passes_test(is_admin, login_url='/accounts/login/')
def normal_admin_pending(request):
    """Pending property approvals"""
    pending_properties = Property.objects.filter(
        is_verified=False
    ).select_related('user').order_by('-created_at')

    context = {
        'properties': pending_properties,
        'pending_count': pending_properties.count(),
    }
    return render(request, 'realestate_admin_templates/properties_list.html', context)

@user_passes_test(is_admin, login_url='/accounts/login/')
def normal_admin_featured(request):
    """Featured properties"""
    featured_properties = Property.objects.filter(
        is_premium=True
    ).select_related('user').order_by('-created_at')

    context = {
        'properties': featured_properties,
        'featured_count': featured_properties.count(),
    }
    return render(request, 'realestate_admin_templates/properties_list.html', context)

@user_passes_test(is_admin, login_url='/accounts/login/')
def normal_admin_agents(request):
    """Agents management"""
    agents = User.objects.filter(
        user_type__in=['agent', 'broker']
    ).order_by('-date_joined')

    if request.method == 'POST':
        agent_id = request.POST.get('agent_id')
        action = request.POST.get('action')

        try:
            agent = User.objects.get(pk=agent_id, user_type__in=['agent', 'broker'])

            if action == 'verify' and not agent.is_verified:
                agent.is_verified = True
                agent.verification_date = timezone.now()
                agent.save()

                log_admin_activity(
                    request, 'verify', f'Verified agent: {agent.username}',
                    'User', agent.id
                )
                messages.success(request, f'Agent "{agent.get_full_name}" verified successfully.')

            elif action == 'unverify' and agent.is_verified:
                agent.is_verified = False
                agent.verification_date = None
                agent.save()

                log_admin_activity(
                    request, 'update', f'Unverified agent: {agent.username}',
                    'User', agent.id
                )
                messages.success(request, f'Agent "{agent.get_full_name}" unverified.')

            elif action == 'activate' and not agent.is_active:
                agent.is_active = True
                agent.save()

                log_admin_activity(
                    request, 'update', f'Activated agent account: {agent.username}',
                    'User', agent.id
                )
                messages.success(request, f'Agent "{agent.get_full_name}" activated.')

            elif action == 'deactivate' and agent.is_active:
                agent.is_active = False
                agent.save()

                log_admin_activity(
                    request, 'update', f'Deactivated agent account: {agent.username}',
                    'User', agent.id
                )
                messages.success(request, f'Agent "{agent.get_full_name}" deactivated.')

        except User.DoesNotExist:
            messages.error(request, "Agent not found.")

        return redirect('normal_admin:normal_admin_agents')

    context = {
        'agents': agents,
        'total_agents': agents.count(),
        'verified_agents': agents.filter(is_verified=True).count(),
        'active_agents': agents.filter(is_active=True).count(),
    }
    return render(request, 'realestate_admin_templates/agents_list.html', context)

@user_passes_test(is_admin, login_url='/accounts/login/')
def normal_admin_companies(request):
    """Companies management"""
    # Get companies by grouping users with company_name
    companies = User.objects.filter(
        Q(company_name__isnull=False) & ~Q(company_name=''),
        Q(user_type='agent') | Q(user_type='broker'),
        is_active=True
    ).values('company_name').annotate(
        company_agents=Count('id'),
        total_properties=Count('properties'),
        verified_agents=Count('id', filter=Q(is_verified=True)),
        premium_members=Count('id', filter=Q(is_premium_user=True))
    ).order_by('-premium_members', '-total_properties', '-company_agents')

    # Convert to list for easier template handling
    companies_list = []
    for company in companies:
        companies_list.append({
            'name': company['company_name'],
            'agents_count': company['company_agents'],
            'properties_count': company['total_properties'],
            'verified_agents': company['verified_agents'],
            'premium_members': company['premium_members'],
        })

    context = {
        'companies': companies_list,
        'total_companies': len(companies_list),
    }
    return render(request, 'realestate_admin_templates/companies_list.html', context)

@user_passes_test(is_admin, login_url='/accounts/login/')
def normal_admin_payments(request):
    """Payments management"""
    # This would need a Payment model - placeholder for now
    payments = []  # Placeholder
    context = {
        'payments': payments,
        'total_payments': len(payments),
    }
    return render(request, 'realestate_admin_templates/payments.html', context)

@user_passes_test(is_admin, login_url='/accounts/login/')
def normal_admin_full_reports(request):
    """Full reports and analytics dashboard"""
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

@user_passes_test(is_admin, login_url='/accounts/login/')
def normal_admin_blog(request):
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

@user_passes_test(is_admin, login_url='/accounts/login/')
def normal_admin_cms(request):
    """Content Management System"""
    context = {
        'pages': [],  # Would integrate with CMS pages
        'templates': [],  # Available templates
        'media_files': [],  # Media library
    }
    return render(request, 'realestate_admin_templates/cms.html', context)

@user_passes_test(is_admin, login_url='/accounts/login/')
def normal_admin_settings(request):
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

# Detail views
@user_passes_test(is_admin, login_url='/accounts/login/')
def normal_admin_property_detail(request, property_id):
    """Detailed view of a property for admin"""
    try:
        property_obj = Property.objects.select_related('user').get(pk=property_id)
        inquiries = ContactInquiry.objects.filter(property=property_obj).order_by('-created_at')[:10]

        context = {
            'property': property_obj,
            'inquiries': inquiries,
        }
        return render(request, 'realestate_admin_templates/property_detail.html', context)
    except Property.DoesNotExist:
        return redirect('normal_admin:normal_admin_full_properties')

@user_passes_test(is_admin, login_url='/accounts/login/')
def normal_admin_user_detail(request, user_id):
    """Detailed view of a user for admin"""
    try:
        user_obj = User.objects.get(pk=user_id)
        user_properties = Property.objects.filter(user=user_obj)[:10]

        context = {
            'user': user_obj,
            'properties': user_properties,
        }
        return render(request, 'realestate_admin_templates/user_detail.html', context)
    except User.DoesNotExist:
        return redirect('normal_admin:normal_admin_full_users')

@user_passes_test(is_admin, login_url='/accounts/login/')
def normal_admin_agent_detail(request, agent_id):
    """Detailed view of an agent for admin"""
    try:
        agent = User.objects.get(pk=agent_id, user_type__in=['agent', 'broker'])
        agent_properties = Property.objects.filter(user=agent)

        context = {
            'agent': agent,
            'properties': agent_properties,
            'properties_count': agent_properties.count(),
        }
        return render(request, 'realestate_admin_templates/agent_detail.html', context)
    except User.DoesNotExist:
        return redirect('normal_admin:normal_admin_agents')
